# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json

from flask import render_template, redirect, url_for, session, jsonify, request, session

from minion.frontend import app, db
from minion.frontend.persona import verify_assertion
from minion.frontend.models import User, Site, Plan, Scan

import requests

@app.route("/")
def index():
    return app.send_static_file('index.html')

@app.route("/api/session")
def api_session():
    if session.get('email') is None:
        return jsonify(success=False)
    return jsonify(success=True, data={'email': session['email'], 'role': session['role']})

@app.route("/api/login", methods=["POST"])
def persona_login():
    if not request.json or 'assertion' not in request.json:
        return jsonify(success=False)
    receipt = verify_assertion(request.json['assertion'], request.host)
    if not receipt:
        return jsonify(success=False)
    user = User.get_or_create(receipt['email'])
    session['email'] = user.email
    session['role'] = user.role
    return api_session()

@app.route("/api/logout")
def api_logout():
    session.clear()
    return jsonify(success=True)

#
# WARNING WARNING WARNING - Everything below is temporary and will likely not survive the next
# iteration of Minion where the focus will be more on the backend side of things. Don't assume
# too much about that code or the backend infrastructure.
#

MINION_BACKEND = "http://127.0.0.1:8383"

def load_minion_scan(id):
    r = requests.get(MINION_BACKEND + "/scans/" + id)
    r.raise_for_status()
    return r.json()['scan']

def count_scan_issues(scan, severity):
    n = 0
    for session in scan.get('sessions', []):
        for issue in session.get('issues', []):
            if issue['Severity'] == severity:
                n += 1
    return n

@app.route("/api/issues")
def api_issues():
    if session.get('email') is None:
        return jsonify(success=False)

    sites = []
    if session.get('role') == 1:
        user = User.query.filter_by(email=session.get('email')).first()
        sites = user.sites
    elif session.get('role') in (2,7):
        sites = Site.query.all()

    results = []
    for site in sites:
        s = {'url': site.url, 'issues': []}
        for plan in site.plans:
            scan = Scan.query.filter_by(site_id=site.id,plan_id=plan.id).order_by('minion_scan_created desc').first()
            if scan:
                minion_scan = load_minion_scan(scan.minion_scan_uuid)
                if minion_scan:
                    for minion_session in minion_scan.get('sessions', []):
                        for i in minion_session.get('issues', []):
                            for field in i.keys():
                                if field not in ('Id', 'Summary', 'Severity'):
                                    del i[field]
                            i['scan'] = {'id': minion_scan['id']}
                            s['issues'].append(i)
        SORTED_SEVERITIES = ('Fatal', 'High', 'Medium', 'Low', 'Informational', 'Info', 'Error')
        s['issues'] = sorted(s['issues'], key=lambda issue: SORTED_SEVERITIES.index(issue['Severity']))
        results.append(s)

    return jsonify(success=True, data=results)

@app.route("/api/history")
def api_history():
    if session.get('email') is None:
        return jsonify(success=False)
    limit = min(25, int(request.args.get('limit', 25)))
    page = int(request.args.get('page', 0))
    if session.get('role') == 1:
        q = db.session.query(User,Site,Plan,Scan)
        q = q.join(User.sites)
        q = q.join(Site.plans)
        q = q.join(Plan.scans)
        q = q.filter(User.email==session['email'])
        q = q.order_by(Scan.minion_scan_created.desc()).offset(page*limit).limit(limit)
    elif session.get('role') in (2,7):
        q = db.session.query(User,Site,Plan,Scan)
        q = q.join(User.sites)
        q = q.join(Site.plans)
        q = q.join(Plan.scans)
        q = q.order_by(Scan.minion_scan_created.desc()).offset(page*limit).limit(limit)
    results = []
    for user,site,plan,scan in q.all():
        epoch = datetime.datetime(year=1970,month=1,day=1)
        results.append({'site': {'url': site.url, 'id': site.id},
                        'plan': {'name': plan.minion_plan_name, 'id': plan.id, 'manual': plan.manual},
                        'scan': {'id': scan.minion_scan_uuid, 'date': int((scan.minion_scan_created - epoch).total_seconds()),
                                 'high': scan.minion_scan_high_count, 'medium': scan.minion_scan_medium_count,
                                 'low': scan.minion_scan_low_count, 'info': scan.minion_scan_info_count}})
    return jsonify(success=True, data=results)

@app.route("/api/sites")
def api_sites():
    if session.get('email') is None:
        return jsonify(success=False)

    sites = []
    if session.get('role') == 1:
        user = User.query.filter_by(email=session.get('email')).first()
        sites = user.sites
    elif session.get('role') in (2,7):
        sites = Site.query.all()

    results = []
    for site in sites:
        s = {'id': site.id, 'url': site.url, 'plans': []}
        for plan in site.plans:
            p = {'id': plan.id,
                 'name': plan.minion_plan_name,
                 'manual': plan.manual,
                 'date': None,
                 'state': None,
                 'low_count': None,
                 'medium_count': None,
                 'high_count': None,
                 'info_count': None}

            # Find the most recent scan, then load it from the task engine and update the status and numbers
            scan = Scan.query.filter_by(site_id=site.id,plan_id=plan.id).order_by('minion_scan_created desc').first()
            if scan:
                if scan.minion_scan_status not in ('FINISHED', 'FAILED', 'CANCELLED'):
                    minion_scan = load_minion_scan(scan.minion_scan_uuid)
                    scan.minion_scan_status = minion_scan['state']
                    scan.minion_scan_low_count = count_scan_issues(minion_scan, 'Low')
                    scan.minion_scan_medium_count = count_scan_issues(minion_scan, 'Medium')
                    scan.minion_scan_high_count = count_scan_issues(minion_scan, 'High')
                    scan.minion_scan_info_count = count_scan_issues(minion_scan, 'Info')
                    db.session.add(scan)
                    db.session.commit()

                epoch = datetime.datetime(year=1970,month=1,day=1)
                p['date'] = (scan.minion_scan_created - epoch).total_seconds()
                p['state'] = scan.minion_scan_status
                p['scan_id'] = scan.minion_scan_uuid
                p['low_count'] = scan.minion_scan_low_count
                p['medium_count'] = scan.minion_scan_medium_count
                p['high_count'] = scan.minion_scan_high_count
                p['info_count'] = scan.minion_scan_info_count
            s['plans'].append(p)
        results.append(s)
    return jsonify(success=True, data=results)

@app.route("/api/scan/<minion_scan_id>/issue/<minion_issue_id>")
def api_scan_issue(minion_scan_id, minion_issue_id):
    if session.get('email') is None:
        return jsonify(success=False)
    r = requests.get(MINION_BACKEND + "/scans/" + minion_scan_id)
    j = r.json()
    for s in j['scan']['sessions']:
        for issue in s['issues']:
            if issue['Id'] == minion_issue_id:
                SESSION_FIELDS = ('plugin', 'artifacts', 'state', 'artifacts')
                r = {field: s.get(field) for field in SESSION_FIELDS}
                return jsonify(success=True,data={'session': r, 'issue': issue, 'scan': j['scan']})
    return jsonify(success=False)

@app.route("/api/scan/<minion_scan_id>")
def api_scan(minion_scan_id):
    if session.get('email') is None:
        return jsonify(success=False)
    r = requests.get(MINION_BACKEND + "/scans/" + minion_scan_id)
    scan = r.json()['scan']
    return jsonify(success=True,data=scan)

@app.route("/api/plan/<minion_plan_name>")
def api_plan(minion_plan_name):
    if session.get('email') is None:
        return jsonify(success=False)
    r = requests.get(MINION_BACKEND + "/plans/" + minion_plan_name)
    plan = r.json()['plan']
    return jsonify(success=True,data=plan)

@app.route("/api/scan/start", methods=['PUT'])
def api_scan_start():
    if session.get('email') is None:
        return jsonify(success=False)
    # Find the plan and site
    plan = Plan.query.get(request.json['planId'])
    site = Site.query.get(request.json['siteId'])
    # Create a scan
    r = requests.post(MINION_BACKEND + "/scans",
                     headers={'Content-Type': 'application/json'},
                     data=json.dumps({'plan': plan.minion_plan_name,
                                      'configuration': { 'target': site.url }}))
    r.raise_for_status()
    minion_scan = r.json()['scan']
    # Start the scan
    r = requests.put(MINION_BACKEND + "/scans/" + minion_scan['id'] + "/control",
                      headers={'Content-Type': 'text/plain'},
                      data="START")
    r.raise_for_status()

    # Create a scan record
    scan = Scan(site_id = site.id, plan_id = plan.id)
    scan.minion_scan_uuid = minion_scan['id']
    scan.minion_scan_status = "QUEUED"
    scan.minion_scan_created = datetime.datetime.now()
    db.session.add(scan)
    db.session.commit()

    return jsonify(success=True)

@app.route("/api/scan/stop", methods=['PUT'])
def api_scan_stop():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False)
    # Get the scan id
    scan_id = request.json['scanId']
    # Stop the scan
    r = requests.put(MINION_BACKEND + "/scans/" + scan_id + "/control",
                     headers={'Content-Type': 'text/plain'},
                      data="STOP")
    r.raise_for_status()
    return jsonify(success=True)
    
