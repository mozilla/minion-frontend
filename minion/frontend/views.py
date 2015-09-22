# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import functools
import json
import ldap

from flask import jsonify, request, session, Response, g

from minion.frontend import app
from minion.frontend.persona import verify_assertion
from minion.frontend.utils import frontend_config

import requests

config = frontend_config()

#
# Simple wrappers around common backend functionality
#

def login_user(email):
    r = requests.put(config['backend-api']['url'] + "/login",
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'email': email}))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('user')

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
        user = create_user(email, 'user')
    return user

def login_or_create_user(email):
    user = login_user(email)
    if not user:
        user = create_user(email, "user")
    return user

def accept_invite(recipient, data):
    invite_id = data['invite_id']
    invite = _backend_get_invite(id=invite_id)
    if invite:
        invite = _backend_control_invite(invite_id, \
            {'action': 'accept', 'login': recipient})
        if not invite:
            return None
        else:
            return get_user(recipient)
    else:
        return None

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

def get_status_report(user=None, group_name=None):
    params = {}
    if user is not None:
        params['user'] = user
        if group_name is not None:
            params['group_name'] = group_name
    r = requests.get(config['backend-api']['url'] + "/reports/status", params=params)
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

def _backend_get_plugins():
    r = requests.get(config['backend-api']['url'] + "/plugins")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('plugins')

def _backend_get_sites(url=None):
    params = {}
    if url:
        params['url'] = url
    r = requests.get(config['backend-api']['url'] + "/sites", params=params)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('sites')


def _backend_get_credInfo():
    r = requests.get(config['backend-api']['url'] + "/credInfo")
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('credInfo')


def _backend_get_site(site_id):
    r = requests.get(config['backend-api']['url'] + "/sites/" + site_id)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('site')


def _backend_add_site(site):
    r = requests.post(config['backend-api']['url'] + "/sites",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(site))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None,j.get('reason')
    return j.get('site'),None

def _backend_update_site(site_id, site):
    r = requests.post(config['backend-api']['url'] + "/sites/" + site_id,
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(site))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('site')

def _backend_add_invite(invite, sender):
    invite['sender'] = sender
    r = requests.post(config['backend-api']['url'] + "/invites",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(invite))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('invite')

def _backend_get_invite(id=None, recipient=None, sender=None):
    if id is not None:
        r = requests.get(config['backend-api']['url'] + "/invites/%s" % id)
    else:
        params = {}
        if recipient is not None:
            params['recipient'] = recipient
        if sender is not None:
            params['sender'] = sender
        r = requests.get(config['backend-api']['url'] + "/invites", params=params)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('invite') or j.get('invites')

def _backend_control_invite(id, action_data):
    r = requests.post(config['backend-api']['url'] + "/invites/%s/control" % id,
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(action_data))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('invite')

def _backend_delete_invite(id):
    r = requests.delete(config['backend-api']['url'] + '/invites/%s' % id)
    r.raise_for_status()
    j = r.json()
    return j

def _backend_get_plans(name=None):
    params = {}
    if name:
        params['name'] = name
    r = requests.get(config['backend-api']['url'] + "/plans", params=params)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('plans')

def _backend_create_plan(plan):
    r = requests.post(config['backend-api']['url'] + "/plans",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(plan))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('plan')

def _backend_update_plan(plan_name, plan):
    r = requests.post(config['backend-api']['url'] + "/plans/" + plan_name,
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(plan))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('plan')

def _backend_delete_plan(plan_name):
    r = requests.delete(config['backend-api']['url'] + "/plans/" + plan_name)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True

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

def _backend_update_user(user_email, user):
    r = requests.post(config['backend-api']['url'] + "/users/" + user_email,
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps(user))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('user')

def _backend_delete_user(user_email):
    r = requests.delete(config['backend-api']['url'] + "/users/" + user_email)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True

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
    r = requests.patch(config['backend-api']['url'] + "/groups/" + group_name,
                       headers={'Content-Type': 'application/json'},
                       data=json.dumps(patch))
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return True

def _backend_get_scans(site_id, plan_name, limit=3):
    params = {'site_id': site_id, 'plan_name': plan_name, 'limit': limit}
    r = requests.get(config['backend-api']['url'] + "/scans", params=params)
    r.raise_for_status()
    j = r.json()
    if not j.get('success'):
        return None
    return j.get('scans')

#
# Basic API for session management
#
def requires_session(*decor_args):
    """
    Check if user is logged in or not by checking
    'email' is in session. This is done by default
    without giving any argument to the decorator.
    You can give the name of a role as an argument.
    For examples:

    @app.route("/api/....")
    @requires_session
    def view_func(...)

    @app.rpite("/api/...."_
    @reqiores_session("administrator")
    def view_func(...)

    """

    def decorator(view):
        @functools.wraps(view)
        def check_session(*args, **kwargs):
            if not session.get('email'):
                return jsonify(success=False, reason='not-logged-in')
            if isinstance(decor_args[0], str):
                role = decor_args[0]
                if role is not None and session.get('role') != role:
                    return jsonify(success=False, reason='permission')
            return view(*args, **kwargs)
        return check_session

    # the decorator can implicilty take the function being
    # decorated. We must ensure the arg is actually callable.
    # Otherwise, we call the decorator without any argument.
    if len(decor_args) == 1 and callable(decor_args[0]):
        return decorator(decor_args[0])
    else:
        return decorator

@app.route("/")
def index():
    return app.send_static_file('index.html')

@app.route("/robots.txt")
def robots():
    return app.send_static_file('robots.txt')

@app.route("/api/session")
@requires_session
def api_session():
    return jsonify(success=True, data={'email': session['email'], 'role': session['role']})

@app.route("/api/login", methods=["GET"])
def api_login():
    return jsonify(success=True, data={'login_type': config['login']['type']})

@app.route("/api/login", methods=["POST"])
def login():
    return globals()[config['login']['type'] + '_login'](request)

def persona_login(request):
    if not request.json or 'assertion' not in request.json:
        return jsonify(success=False)
    receipt = verify_assertion(request.json['assertion'], request.host)
    if not receipt:
        return jsonify(success=False)
    if request.json.get('invite_id'):
        user = accept_invite(receipt['email'], request.json)
        if not user:
            return jsonify(success=False)
        user = login_or_create_user(user['email'])
    else:
        user = login_or_create_user(receipt['email'])
    if not user:
        return jsonify(success=False)
    elif user.get('status') == "banned":
        return jsonify(success=False, reason="banned")
    session['email'] = user['email']
    session['role'] = user['role']
    return api_session()

def ldap_login(request):
    data = json.loads(request.data)
    username = data['user']
    password = data['password']

    # Initialize LDAP
    try:
        ld = ldap.initialize(config['login']['ldap']['uri'])
    except ldap.LDAPError, e:
        return jsonify(success=False, reason="error")

    # Active Directory (and others) don't require a full DN to bind (such as samAccountName=april)
    if 'baseDN' in config['login']['ldap']:
        auth_query = "{ldap[usernameAttribute]}={username},{ldap[baseDN]}".format(
            ldap=config['login']['ldap'], username=username)
    else:
        auth_query = "{ldap[usernameAttribute]}={username}".format(ldap=config['login']['ldap'], username=username)

    # Authentication
    try:
        ld.simple_bind_s(auth_query, password)
    except ldap.LDAPError, e:
        if e.message['desc'] == 'Invalid credentials':
            return jsonify(success=False, reason="invalid_cred")
        return jsonify(success=False, reason="error")

    # Retrieve mail
    results = ld.search_s(auth_query, ldap.SCOPE_SUBTREE, attrlist=[str(config['login']['ldap']['emailAttribute'])])
    try:
        mail = results[0][1][config['login']['ldap']['emailAttribute']][0]
        user_dn = results[0][0]
    except Exception as e:
        return jsonify(sucess=False, reason="error")

    # Check if user in an authorized group
    if config['login']['ldap']['checkAuthorizedGroups']:
        authorized = False
        for group in config['login']['ldap']['authorizedGroups']:
            group_query = "{ldap[groupMembershipAttribute]}={user_dn}".format(
                ldap=config['login']['ldap'], user_dn=user_dn)

            results = ld.search_s(group, ldap.SCOPE_BASE, group_query)

            if len(results) > 0:
                authorized = True
                break

        if not authorized:
            return jsonify(success=False, reason="not_authorized")

    # Unbind the connection with the ldap server
    ld.unbind_s()

    # Login
    user = login_or_create_user(mail)

    if not user:
        return jsonify(success=False)
    elif user.get('status') == "banned":
        return jsonify(success=False, reason="banned")
    session['email'] = user['email']
    session['role'] = user['role']

    return api_session()

def oauth_login(request):
    """
    If email and role have been set in the session (via an oauth login stream), return them in the API call. If 'reason'
    has been set (as a result of a failed OAuth login), set it in the response to appear as an error and clear it out.
    """

    if 'email' in session and 'role' in session:
        return api_session()
    elif 'reason' in session:
        return jsonify(success=False, reason=session.pop('reason'))
    else:
        return jsonify(success=False)

@app.route("/api/logout")
def api_logout():
    session.clear()
    return jsonify(success=True)

@app.route('/api/forcelogout')
def api_force_logout():
    """
    A convenience call to be used by developers: it clears out the session internally and removes the session cookie
    """

    session.clear()
    resp = Response('Deleting session cookie')
    resp.set_cookie('session', value='expired', path='/')
    return resp

# #
# # WARNING WARNING WARNING - Everything below is temporary and will likely not survive the next
# # iteration of Minion where the focus will be more on the backend side of things. Don't assume
# # too much about that code or the backend infrastructure.
# #

@app.route("/api/issues")
@requires_session
def api_issues():
    report = get_issues_report(user=session['email'])
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/invites/<invite_id>", methods=['GET', 'PUT'])
def api_invite(invite_id):
    invite = _backend_get_invite(invite_id)
    if invite and invite['status'] == 'pending':
        if request.method == 'GET':
            return jsonify(success=True, data=invite)
        else:
            action = request.json['action']
            invite = _backend_control_invite(invite_id, {'action': action})
            return jsonify(success=True)
    return jsonify(success=False)

@app.route("/api/history")
@requires_session
def api_history():
    report = get_history_report(user=session['email'])
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/profile")
@requires_session
def api_profile():
    user = get_user(session['email'])
    if not user:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=user)

@app.route("/api/sites")
@requires_session
def api_sites():
    group_name = request.args.get("group_name")
    report = get_status_report(user=session['email'], group_name=group_name)
    if report is None:
        return jsonify(success=False, data=None)
    return jsonify(success=True, data=report)

@app.route("/api/scan/<minion_scan_id>/issue/<minion_issue_id>")
@requires_session
def api_scan_issue(minion_scan_id, minion_issue_id):
    r = requests.get(config['backend-api']['url'] + "/scans/" + minion_scan_id,
            params={'email': session['email']})
    j = r.json()
    if j['success']:
        for s in j['scan']['sessions']:
            for issue in s['issues']:
                if issue['Id'] == minion_issue_id:
                    SESSION_FIELDS = ('plugin', 'artifacts', 'state', 'artifacts')
                    r = {field: s.get(field) for field in SESSION_FIELDS}
                    return jsonify(success=True,data={'session': r, 'issue': issue, 'scan': j['scan']})
    else:
        return jsonify(success=False, reason=r.json()['reason'])

@app.route("/api/scan/<minion_scan_id>")
@requires_session
def api_scan(minion_scan_id):
    r = requests.get(config['backend-api']['url'] + "/scans/" + minion_scan_id,
            params={'email': session['email']})
    if r.json()['success']:
        return jsonify(success=True, data=r.json()['scan'])
    else:
        return jsonify(success=r.json()['success'], reason=r.json().get('reason'))

@app.route("/api/plan/<minion_plan_name>")
@requires_session
def api_plan(minion_plan_name):
    r = requests.get(
        config['backend-api']['url'] + "/plans/" + minion_plan_name,
        params={"email": session['email']})
    plan = r.json()['plan']
    return jsonify(success=True,data=plan)

@app.route("/api/scan/start", methods=['PUT'])
@requires_session
def api_scan_start():
    # Find the plan and site
    plan = request.json['plan']
    target = request.json['target']
    # Create a scan
    r = requests.post(config['backend-api']['url'] + "/scans",
                      headers={'Content-Type': 'application/json'},
                      data=json.dumps({
                          'user': session['email'],
                          'plan': plan,
                          'configuration': { 'target': target }}))
    r.raise_for_status()
    scan = r.json()['scan']
    # Start the scan
    r = requests.put(config['backend-api']['url'] + "/scans/" + scan['id'] + "/control",
                     headers={'Content-Type': 'text/plain'},
                     data="START",
                     params={'email': session['email']})
    r.raise_for_status()

    return jsonify(success=r.json()['success'], reason=r.json().get('reason'))

@app.route("/api/scan/stop", methods=['PUT'])
@requires_session
def api_scan_stop():
    # Get the scan id
    scan_id = request.json['scanId']
    # Stop the scan
    r = requests.put(config['backend-api']['url'] + "/scans/" + scan_id + "/control",
                     headers={'Content-Type': 'text/plain'},
                     data="STOP",
                     params={'email': session['email']})
    r.raise_for_status()
    return jsonify(success=r.json()['success'], reason=r.json().get('reason'))


#
# API For the Administration Pages
#

@app.route("/api/admin/plugins", methods=["GET"])
@requires_session('administrator')
def get_api_admin_plugins():
    plugins = _backend_get_plugins()
    if not plugins:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=plugins)

@app.route("/api/admin/sites", methods=["GET"])
@requires_session('administrator')
def get_api_admin_sites():
    # Retrieve user list from backend
    sites = _backend_get_sites()
    credInfo = _backend_get_credInfo()
    if not sites:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=sites, credInfo=credInfo)

@app.route("/api/admin/sites", methods=["POST"])
@requires_session('administrator')
def post_api_admin_sites():
    # Create a new site
    site = _backend_add_site(request.json)
    if not site:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=site)

@app.route("/api/admin/sites/<site_id>", methods=["POST"])
@requires_session('administrator')
def post_api_admin_sites_site_id(site_id):
    # Update a site
    site = _backend_update_site(site_id, request.json)
    if not site:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=site)

@app.route("/api/admin/users", methods=['GET'])
@requires_session('administrator')
def get_api_admin_users():
    # Retrieve user list from backend
    users = _backend_list_users()
    if not users:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=users)

@app.route("/api/admin/users", methods=['POST'])
@requires_session('administrator')
def post_api_admin_users():
    # Retrieve user list from backend
    user = _backend_add_user(request.json)
    if not user:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=user)

@app.route("/api/admin/invites", methods=['POST'])
@requires_session('administrator')
def post_api_admin_invite():
    invitation = _backend_add_invite(request.json, session['email'])
    return jsonify(success=True, data=invitation)

@app.route("/api/admin/invites", methods=['GET'])
@requires_session('administrator')
def get_api_admin_invites():
    recipient = request.args.get('recipient', None)
    sender = request.args.get('sender', None)
    invitations = _backend_get_invite(recipient=recipient, sender=sender)
    return jsonify(success=True, data=invitations)

@app.route("/api/admin/invites/<id>", methods=['GET'])
@requires_session('administrator')
def get_api_admin_invite(id):
    invitation = _backend_get_invite(id=id)
    return jsonify(success=True, data=invitation)

@app.route("/api/admin/invites/<id>", methods=['DELETE'])
@requires_session('administrator')
def delete_api_admin_invite(id):
    j = _backend_delete_invite(id=id)
    if j['success']:
        return jsonify(success=True)
    else:
        return jsonify(success=False, reason=j['reason'])

@app.route("/api/admin/invites/<id>/control", methods=["POST"])
@requires_session('administrator')
def control_api_admin_invite(id):
    invitation = _backend_control_invite(id, request.json)
    return jsonify(success=True, data=invitation)

@app.route("/api/admin/users/<user_email>", methods=['POST'])
@requires_session('administrator')
def post_api_admin_users_by_email(user_email):
    if not _backend_update_user(user_email, request.json):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/users/<user_email>", methods=['DELETE'])
@requires_session('administrator')
def delete_api_admin_users_by_email(user_email):
    if not _backend_delete_user(user_email):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/plans", methods=["GET"])
@requires_session('administrator')
def get_api_admin_plans():
    # Retrieve user list from backend
    plans = _backend_get_plans()
    if not plans:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=plans)

@app.route("/api/admin/plans", methods=["POST"])
@requires_session('administrator')
def post_api_admin_plans():
    plan = _backend_create_plan(request.json)
    if not plan:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/plans/<plan_name>", methods=['POST'])
@requires_session('administrator')
def post_api_admin_plans_by_plan_name(plan_name):
    if not _backend_update_plan(plan_name, request.json):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/plans/<plan_name>", methods=['DELETE'])
@requires_session('administrator')
def delete_api_admin_plans_by_plan_name(plan_name):
    if not _backend_delete_plan(plan_name):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/groups", methods=['GET'])
@requires_session('administrator')
def get_api_admin_groups():
    # Retrieve user list from backend
    groups = _backend_list_groups()
    if not groups:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=groups)

@app.route("/api/admin/groups", methods=['POST'])
@requires_session('administrator')
def post_api_admin_groups():
    # Create a new group
    group = _backend_add_group(request.json)
    if not group:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/groups/<group_name>", methods=['GET'])
@requires_session('administrator')
def get_api_admin_group_by_name(group_name):
    # Retrieve group from the backend
    group = _backend_get_group(group_name)
    if not group:
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True, data=group)

@app.route("/api/admin/groups/<group_name>", methods=['DELETE'])
@requires_session('administrator')
def delete_api_admin_group_by_name(group_name):
    # Retrieve group from the backend
    if not _backend_delete_group(group_name):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

@app.route("/api/admin/groups/<group_name>", methods=['PATCH'])
@requires_session('administrator')
def post_api_admin_groups_group_name_sites(group_name):
    # Patch the group
    if not _backend_patch_group(group_name, request.json):
        return jsonify(success=False, reason='unknown')
    return jsonify(success=True)

# Basic API mainly for Overlord now

def requires_ws_auth(*decorator_args):
    """
    Check if the request has an X-Minion-Api-Key and X-Minion-Api-User header. If
    it does, then match it against the user and store the user in g.api_user so
    that handlers can use it.
    """
    def decorator(view):
        @functools.wraps(view)
        def check_api_key(*args, **kwargs):
            api_user = request.headers.get('x-minion-api-user')
            if not api_user:
                return jsonify(success=False, reason='missing-api-user')
            user = get_user(api_user)
            if not user:
                return jsonify(success=False, reason='invalid-api-auth')
            api_key = request.headers.get('x-minion-api-key')
            if not api_key:
                return jsonify(success=False, reason='missing-api-key')
            if len(user.get('api_key', '')) == 0 or user.get('api_key') != api_key:
                return jsonify(success=False, reason='invalid-api-auth')
            g.api_user = user
            return view(*args, **kwargs)
        return check_api_key
    if len(decorator_args) == 1 and callable(decorator_args[0]):
        return decorator(decorator_args[0])
    else:
        return decorator

@app.route("/ws/whoami", methods=['GET'])
@requires_ws_auth
def ws_whoami():
    return Response(json.dumps({'success': True, 'user': { 'email': g.api_user['email'] } }, indent=4) + "\n", mimetype="application/json")

#
# Retrieve all sites. Or search for a specific one.
#
#  GET /ws/sites          retrieve all sites visible to user
#  GET /ws/sites?url=$URL retrieve all sites that match url (only direct match now, returns 1 result)
#
# Returns a site structure.
#

@app.route("/ws/sites", methods=['GET'])
@requires_ws_auth
def ws_get_sites():
    sites = _backend_get_sites(url=request.args.get('url'))
    return Response(json.dumps({'success': True, 'sites': sites}, indent=4) + "\n", mimetype="application/json")

@app.route("/ws/sites/<site_id>", methods=['GET'])
@requires_ws_auth
def ws_get_site(site_id):
    sites = _backend_get_site(site_id)
    return Response(json.dumps({'success': True, 'site': sites}, indent=4) + "\n", mimetype="application/json")

#
# Create a site.
#
#  POST /ws/sites
#
# Returns a site record.
#

@app.route("/ws/sites", methods=['POST'])
@requires_ws_auth
def ws_post_sites():
    site,reason = _backend_add_site(request.json)
    if not site:
        return jsonify(success=False, reason=reason)
    return jsonify(success=True, site=site)

#
# Retrieve plans
#

@app.route("/ws/plans", methods=["GET"])
@requires_ws_auth
def ws_get_plans():
    planz = _backend_get_plans(name=request.args.get('name'))
    return Response(json.dumps({'success': True, 'plans': planz}, indent=4) + "\n", mimetype="application/json")

#
# Retrieve scans
#

@app.route("/ws/scans", methods=['GET'])
@requires_ws_auth
def ws_get_scans():
    limit = request.args.get('limit')
    if limit: limit = int(limit)
    scanz = _backend_get_scans(request.args.get('site_id'), request.args.get('plan_name'), limit)
    return Response(json.dumps({'success': True, 'scans': scanz}, indent=4) + "\n", mimetype="application/json")

#
# Retrieve a specific scan
#

@app.route("/ws/scans/<scan_id>", methods=['GET'])
@requires_ws_auth
def ws_get_scan(scan_id):
    r = requests.get(config['backend-api']['url'] + "/scans/" + scan_id) # TODO , params={'email': session['email']})
    if r.json()['success']:
        print "SCAN", r.json()['scan']
        return jsonify(success=True, scan=r.json()['scan'])
    else:
        return jsonify(success=r.json()['success'], reason=r.json().get('reason'))

#
# Create and start a scan
#

@app.route("/ws/scans/create", methods=["PUT"])
@requires_ws_auth
def put_ws_scans():
    # Find the plan and site
    plan = request.json["planName"]
    siteId = request.json["siteId"]

    site = _backend_get_site(siteId)

    configuration = { "target": site["url"], "callback": { "url": request.json["callbackURL"], "events": ['scan-state'] } }

    # Create a scan
    r = requests.post(config["backend-api"]["url"] + "/scans",
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({"user": g.api_user["email"],
                                       "plan": plan,
                                       "configuration": configuration}))
    r.raise_for_status()
    scan = r.json()["scan"]

    # Start the scan
    r = requests.put(config["backend-api"]["url"] + "/scans/" + scan["id"] + "/control",
                     headers={"Content-Type": "text/plain"},
                     data="START")
    r.raise_for_status()

    return ws_get_scan(scan["id"])

#
# GET /ws/issues
#

@app.route("/ws/issues", methods=["GET"])
@requires_ws_auth
def get_ws_issues():
    params = { "group_name": request.args.get("group_name"),
               "plan_name": request.args.get("plan_name"),
               "issue_code": request.args.getlist("issue_code") }
    r = requests.get(config["backend-api"]["url"] + "/issues", params=params)
    r.raise_for_status()
    j = r.json()
    if j["success"]:
        return jsonify(success=j["success"], issues=j["issues"])
    else:
        return jsonify(success=r.json()["success"], reason=r.json().get("reason"))


@app.route("/api/scanschedule", methods=["PUT"])
def scanschedule():
  r = requests.post(config["backend-api"]["url"] + "/scanschedule",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(request.json))
  r.raise_for_status()
  return  str(r.text)



@app.route("/api/setCredentials", methods=["PUT"])
def setCredentials():
  r = requests.post(config["backend-api"]["url"] + "/setCredentials",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(request.json))
  r.raise_for_status()
  j = r.json()
  return  jsonify(success=j['success'], message=j['message'])
