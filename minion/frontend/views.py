# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import functools
import json

from flask import render_template, redirect, url_for, session, jsonify, request, session

from minion.frontend import app
from minion.frontend.persona import verify_assertion
from minion.frontend.utils import frontend_config

import requests

# This should move somewhere else. The -d option is part of flask.script
# (althiugh it does not seem to work) and the session secret can move to
# the config file

app.debug = True
app.secret_key = "dkejkdejkldjel"

config = frontend_config()

#
# Simple wrappers around common backend functionality
#

def get_user(email):
    r = requests.get(config['backend-api']['url'] + "/users/" + email)
    r.raise_for_status()
    j = r.json()
    if not j['success']:
        return None
    return j.get('user')

def create_user(email, role):
    user = { 'email': email, 'role': role }
    r = requests.post(config['backend-api']['url'] + "/users",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(user))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('user')

def get_or_create_user(email):
    user = get_user(email)
    if not user:
        user = create_user(email, 'guest')
    return user

def get_history_report(user=None):
    params = {}
    if user is not None:
        params['user'] = user
    r = requests.get(config['backend-api']['url'] + "/reports/history", params={'user': session['email']})
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('report')

def get_status_report(user=None):
    params = {}
    if user is not None:
        params['user'] = user
    r = requests.get(config['backend-api']['url'] + "/reports/status", params={'user': session['email']})
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('report')

def get_issues_report(user=None):
    params = {}
    if user is not None:
        params['user'] = user
    r = requests.get(config['backend-api']['url'] + "/reports/issues", params={'user': session['email']})
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('report')

def _backend_get_sites():
    r = requests.get(config['backend-api']['url'] + "/sites")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('sites')

def _backend_add_site(site):
    r = requests.post(config['backend-api']['url'] + "/sites",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(site))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('site')

def _backend_get_plans():
    r = requests.get(config['backend-api']['url'] + "/plans")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('plans')

def _backend_list_users():
    r = requests.get(config['backend-api']['url'] + "/users")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('users')

def _backend_add_user(user):
    r = requests.post(config['backend-api']['url'] + "/users",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(user))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('user')

def _backend_list_groups():
    r = requests.get(config['backend-api']['url'] + "/groups")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('groups')

def _backend_delete_group(group_id):
    r = requests.delete(config['backend-api']['url'] + "/groups/" + group_id)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True

def _backend_get_group(group_name):
    r = requests.get(config['backend-api']['url'] + "/groups/" + group_name)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('group')

def _backend_add_group(group):
    r = requests.post(config['backend-api']['url'] + "/groups",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(group))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('group')

def _backend_delete_group(group_name):
    r = requests.delete(config['backend-api']['url'] + "/groups/" + group_name)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True

def _backend_patch_group(group_name, patch):
    print "PATCH", patch
    r = requests.patch(config['backend-api']['url'] + "/groups/" + group_name,
                       headers={'Content-Type': 'application/json'},
                       data=json.dumps(patch))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True


#
# Basic API for session management
#
NO_MATCHING = object()

def requires_session(required):
    """
    Check if the required key-value exist in the session.
    If a specific key does not require matching, e.g.
    session.get('email'), then the value will simply be
    NO_MATCHING object (see the global name above).

    @app.route("/api/....")
    @requires_session({'email': NO_MATCHING, 
        'role': 'administrator'})
    def view_func(...)

    """
    def decorator(view):
        @functools.wraps(view)
        def check_session(*args, **kwargs):
            for req_key, req_value in required.iteritems():
                value_in_session = session.get(req_key, None)
                if value_in_session is not None:
                    if req_value is not NO_MATCHING  and value_in_session != req_value:
                        return jsonify(success=False)
                else:
                    return jsonify(success=False)
        return check_session
    return decorator                

                
        
@app.route("/")
def index():
    return app.send_static_file('index.html')

@app.route("/api/session")
@requires_session({'email': NO_MATCHING})
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
    user = get_or_create_user(receipt['email'])
    if not user:
        return jsonify(success=False)
    session['email'] = user['email']
    session['role'] = user['role']
    return api_session()

@app.route("/api/logout")
def api_logout():
    session.clear()
    return jsonify(success=True)


# #
# # WARNING WARNING WARNING - Everything below is temporary and will likely not survive the next
# # iteration of Minion where the focus will be more on the backend side of things. Don't assume
# # too much about that code or the backend infrastructure.
# #

@app.route("/api/issues")
def api_issues():
    if session.get('email') is None:
        return jsonify(success=False)
    report = get_issues_report(user=session['email'])
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/history")
def api_history():
    if session.get('email') is None:
        return jsonify(success=False)
    report = get_history_report(user=session['email'])
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/sites")
def api_sites():
    if session.get('email') is None:
        return jsonify(success=False)
    report = get_status_report(user=session['email'])
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/scan/<minion_scan_id>/issue/<minion_issue_id>")
def api_scan_issue(minion_scan_id, minion_issue_id):
    if session.get('email') is None:
        return jsonify(success=False)
    r = requests.get(config['backend-api']['url'] + "/scans/" + minion_scan_id)
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
    # TODO This must check if the user actually has access to the scan
    r = requests.get(config['backend-api']['url'] + "/scans/" + minion_scan_id)
    scan = r.json()['scan']
    return jsonify(success=True,data=scan)

@app.route("/api/plan/<minion_plan_name>")
def api_plan(minion_plan_name):
    if session.get('email') is None:
        return jsonify(success=False)
    r = requests.get(config['backend-api']['url'] + "/plans/" + minion_plan_name)
    plan = r.json()['plan']
    return jsonify(success=True,data=plan)

@app.route("/api/scan/start", methods=['PUT'])
def api_scan_start():
    if session.get('email') is None:
        return jsonify(success=False)
    # Find the plan and site
    plan = request.json['plan']
    target = request.json['target']
    # Create a scan
    r = requests.post(config['backend-api']['url'] + "/scans",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({'plan': plan, 'configuration': { 'target': target }}))
    r.raise_for_status()
    scan = r.json()['scan']
    # Start the scan
    r = requests.put(config['backend-api']['url'] + "/scans/" + scan['id'] + "/control",
                     headers={'Content-Type': 'text/plain'},
                     data="START")
    r.raise_for_status()

    return jsonify(success=True)

@app.route("/api/scan/stop", methods=['PUT'])
def api_scan_stop():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False)
    # Get the scan id
    scan_id = request.json['scanId']
    # Stop the scan
    r = requests.put(config['backend-api']['url'] + "/scans/" + scan_id + "/control",
                     headers={'Content-Type': 'text/plain'},
                      data="STOP")
    r.raise_for_status()
    return jsonify(success=True)

#
# API For the Administration Pages
#

@app.route("/api/admin/sites", methods=["GET"])
def get_api_admin_sites():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve user list from backend
    sites = _backend_get_sites()
    if not sites:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=sites)

@app.route("/api/admin/sites", methods=["POST"])
def post_api_admin_sites():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Create a new site
    site = _backend_add_site(request.json)
    if not site:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=site)


@app.route("/api/admin/users", methods=['GET'])
def get_api_admin_users():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve user list from backend
    users = _backend_list_users()
    if not users:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=users)

@app.route("/api/admin/users", methods=['POST'])
def post_api_admin_users():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve user list from backend
    user = _backend_add_user(request.json)
    if not user:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=user)

@app.route("/api/admin/plans", methods=["GET"])
def get_api_admin_plans():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve user list from backend
    plans = _backend_get_plans()
    if not plans:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=plans)

@app.route("/api/admin/groups", methods=['GET'])
def get_api_admin_groups():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve user list from backend
    groups = _backend_list_groups()
    if not groups:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=groups)

@app.route("/api/admin/groups", methods=['POST'])
def post_api_admin_groups():
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Create a new group
    group = _backend_add_group(request.json)
    if not group:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/groups/<group_name>", methods=['GET'])
def get_api_admin_group_by_name(group_name):
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve group from the backend
    group = _backend_get_group(group_name)
    if not group:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=group)

@app.route("/api/admin/groups/<group_name>", methods=['DELETE'])
def delete_api_admin_group_by_name(group_name):
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Retrieve group from the backend
    if not _backend_delete_group(group_name):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/groups/<group_name>", methods=['PATCH'])
def post_api_admin_groups_group_name_sites(group_name):
    print "REQUEST DATA", request
    print "REQUEST DATA", request.headers
    # Check if the session is valid
    if session.get('email') is None:
        return jsonify(success=False, reason='not-logged-in')
    # Check if the user is an administrator
    if session.get('role') != 'administrator':
        return jsonify(success=False, reason='permission')
    # Patch the group
    if not _backend_patch_group(group_name, request.json):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)
