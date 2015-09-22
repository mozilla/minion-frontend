# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import requests
import uuid

from urllib import urlencode

from flask.json import loads
from flask import jsonify, redirect, request, session
from minion.frontend import app
from minion.frontend.utils import frontend_config
from minion.frontend.views import api_session, login_or_create_user

import requests


@app.route("/api/login/oauth", methods=["GET"])
def get_api_login_oauth_providers():
    providers = frontend_config().get('login', {}).get('oauth', {}).get('providers', {})

    # The list of providers with a client_secret set
    result = {
        'success': True,
        'data': {
            'providers': [provider for provider in providers.keys() if providers.get(provider, {}).get('client_secret', '')]
        }
    }

    # Put the reason in the API response, if a previous oauth login had failed
    if 'reason' in session:
        result['reason'] = session.pop('reason')

    return jsonify(result)

@app.route("/ws/login/oauth/facebook", methods=["GET"])
def get_api_login_oauth_facebook():
    ACCESS_TOKEN_URL = 'https://graph.facebook.com/v2.3/oauth/access_token'
    AUTHORIZATION_URL = 'https://www.facebook.com/dialog/oauth'
    API_URL = 'https://graph.facebook.com/me/'

    config = frontend_config()['login']['oauth']['providers']['facebook']

    # Called when we need to send them to Facebook
    if not request.args:
        # Facebook requires a client_id, redirect_uri, and scope
        parameters = {
            'client_id': config['client_id'],
            'redirect_uri': request.base_url,
            'scope': 'email'
        }

        # It also requires a nonce (state) as an anti-CSRF token
        parameters['state'] = session['state'] = str(uuid.uuid4())

        # Redirect to Facebook for authorization
        url = AUTHORIZATION_URL + '?' + urlencode(parameters)
        return redirect(url)

    # Called when Facebook redirects back to us
    else:
        # Get the code and state from Facebook
        code = request.args.get('code')
        state = request.args.get('state')

        # Facebook auth fails
        if code == None or state == None:
            return __oauth_failed_login_redirect()

        # Validate the nonce
        if not session.get('state') or session.get('state') != state:
            return __oauth_failed_login_redirect('error')

        # Get the session information from Facebook
        try:
            r = requests.post(url=ACCESS_TOKEN_URL,
                              data={
                                  'client_id': config['client_id'],
                                  'client_secret': config['client_secret'],
                                  'code': code,
                                  'redirect_uri': request.base_url,
                                  'state': state
            })
            r = loads(r.text)

        except:
            return __oauth_failed_login_redirect()

        # Check for error's in Facebook's response
        if 'error' in r or 'access_token' not in r:
            return __oauth_failed_login_redirect()

        # Get the user's email address from Facebook
        parameters = {
            'access_token': r['access_token'],
            'fields': 'email'
        }
        r = requests.get(API_URL + '?' + urlencode(parameters))
        r = loads(r.text)

        if 'email' not in r:
            return __oauth_failed_login_redirect()

        return __oauth_create_api_session(r['email'])

@app.route("/ws/login/oauth/firefoxaccounts", methods=["GET"])
def get_api_login_oauth_firefoxaccounts():
    # Development OAuth
    # ACCESS_TOKEN_URL = 'https://oauth-latest.dev.lcip.org/v1/token'
    # AUTHORIZATION_URL = 'https://oauth-latest.dev.lcip.org/v1/authorization'
    # API_URL = 'https://latest.dev.lcip.org/profile/v1/email'
    # OAUTH_URL = 'https://oauth-latest.dev.lcip.org/v1'

    # Production OAuth
    ACCESS_TOKEN_URL = 'https://oauth.accounts.firefox.com/v1/token'
    AUTHORIZATION_URL = 'https://oauth.accounts.firefox.com/v1/authorization'
    API_URL = 'https://profile.accounts.firefox.com/v1/email'
    OAUTH_URL = 'https://oauth.accounts.firefox.com/v1'

    config = frontend_config()['login']['oauth']['providers']['firefoxaccounts']

    # Called when we need to send them to FxA
    if not request.args:
        # GitHub requires a client_id, oauth_uri, redirect_uri, and scope
        parameters = {
            'client_id': config['client_id'],
            'oauth_uri': OAUTH_URL,
            'redirect_uri': request.base_url,
            'scope': 'profile:email'
        }

        # It also requires a nonce (state) as an anti-CSRF token
        parameters['state'] = session['state'] = str(uuid.uuid4())

        # Redirect to FxA for authorization
        url = AUTHORIZATION_URL + '?' + urlencode(parameters)
        return redirect(url)

    # Called when FxA redirects back to us
    else:
        # Get the code and state from FxA
        code = request.args.get('code')
        state = request.args.get('state')

        # FxA auth fails
        if code == None or state == None:
            return __oauth_failed_login_redirect()

        # Validate the nonce
        if not session.get('state') or session.get('state') != state:
            return __oauth_failed_login_redirect('error')

        # Get the session information from FxA
        try:
            r = requests.post(url=ACCESS_TOKEN_URL,
                              data={
                                  'client_id': config['client_id'],
                                  'client_secret': config['client_secret'],
                                  'code': code,
                                  'state': state,
                                  'ttl': 3600  # one hour
            })
            r = loads(r.text)
        except:
            return __oauth_failed_login_redirect()

        # Check for error's in FxA's response
        if 'error' in r or 'access_token' not in r or 'profile:email' not in r.get('scope'):
            return __oauth_failed_login_redirect()

        # Get the user's email address from FxA
        r = requests.get(API_URL,
                         headers = {'Authorization': 'Bearer ' + r.get('access_token')})
        r = loads(r.text)

        if 'email' not in r:
            return __oauth_failed_login_redirect()

        return __oauth_create_api_session(r['email'])

@app.route("/ws/login/oauth/github", methods=["GET"])
def get_api_login_oauth_github():
    ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
    AUTHORIZATION_URL = 'https://github.com/login/oauth/authorize'
    API_URL = 'https://api.github.com/user/emails'

    config = frontend_config()['login']['oauth']['providers']['github']

    # Called when we need to send them to GitHub
    if not request.args:
        # GitHub requires a client_id, redirect_url, and scope
        parameters = {
            'client_id': config['client_id'],
            'redirect_url': request.base_url,
            'scope': 'user:email'
        }

        # It also requires a nonce (state) as an anti-CSRF token
        parameters['state'] = session['state'] = str(uuid.uuid4())

        # Redirect to GitHub for authorization
        url = AUTHORIZATION_URL + '?' + urlencode(parameters)
        return redirect(url)

    # Called when GitHub redirects back to us
    else:
        # Get the code and state from GitHub
        code = request.args.get('code')
        state = request.args.get('state')

        # GitHub auth fails
        if code == None or state == None:
            return __oauth_failed_login_redirect()

        # Validate the nonce
        if not session.get('state') or session.get('state') != state:
            return __oauth_failed_login_redirect('error')

        # Get the session information from GitHub
        try:
            r = requests.post(url=ACCESS_TOKEN_URL,
                              headers={
                                  'Accept': 'application/json'
            },
                              data={
                                  'client_id': config['client_id'],
                                  'client_secret': config['client_secret'],
                                  'code': code,
                                  'state': state
            })
            r = loads(r.text)
        except:
            return __oauth_failed_login_redirect()

        # Check for error's in GitHub's response
        if 'error' in r or 'access_token' not in r or 'user:email' not in r.get('scope'):
            return __oauth_failed_login_redirect()

        # Get the user's email address from GitHub
        r = requests.get(API_URL, headers={'Authorization': 'token ' + r.get('access_token')})
        r = loads(r.text)

        email = None
        for address in r:
            if 'email' not in address:
                return __oauth_failed_login_redirect()

            if address.get('primary', False) and address.get('verified', False):
                email = address.get('email')

        return __oauth_create_api_session(email)

@app.route("/ws/login/oauth/google", methods=["GET"])
def get_api_login_oauth_google():
    ACCESS_TOKEN_URL = 'https://www.googleapis.com/oauth2/v3/token'
    AUTHORIZATION_URL = 'https://accounts.google.com/o/oauth2/auth'
    API_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

    config = frontend_config()['login']['oauth']['providers']['google']

    # Called when we need to send them to Google
    if not request.args:
        # Google requires a client_id, redirect_url, response_type, and scope
        parameters = {
            'client_id': config['client_id'],
            'response_type': 'code',
            'redirect_uri': request.base_url,
            'scope': 'email'
        }

        # It also requires a nonce (state) as an anti-CSRF token
        parameters['state'] = session['state'] = str(uuid.uuid4())

        # Redirect to Google for authorization
        url = AUTHORIZATION_URL + '?' + urlencode(parameters)
        return redirect(url)

    # Called when Google redirects back to us
    else:
        # Get the code and state from Google
        code = request.args.get('code')
        state = request.args.get('state')

        # Google auth fails
        if code == None or state == None:
            return __oauth_failed_login_redirect()

        # Validate the nonce
        if not session.get('state') or session.get('state') != state:
            return __oauth_failed_login_redirect('error')

        # Get the session information from Google
        try:
            r = requests.post(url=ACCESS_TOKEN_URL,
                              data={
                                  'client_id': config['client_id'],
                                  'client_secret': config['client_secret'],
                                  'code': code,
                                  'grant_type': 'authorization_code',
                                  'redirect_uri': request.base_url,
                                  'state': state
            })
            r = loads(r.text)
        except:
            return __oauth_failed_login_redirect()

        # Check for error's in Google's response
        if 'error' in r or 'access_token' not in r:
            return __oauth_failed_login_redirect()

        # Get the user's email address from Google
        r = requests.get(API_URL, headers={'Authorization': 'Bearer ' + r.get('access_token')})
        r = loads(r.text)

        # Make sure it's a verified email address
        if 'email' not in r or not r.get('verified_email', False):
            return __oauth_failed_login_redirect()

        return __oauth_create_api_session(r['email'])

def __oauth_create_api_session(email):
    if not email:
        return jsonify(success=False)

    # Attempt to log the user in on the backend
    user = login_or_create_user(email)

    if not user:
        __oauth_failed_login_redirect()
    elif user.get('status') == 'banned':
        __oauth_failed_login_redirect(reason='banned')

    session['email'] = user['email']
    session['role'] = user['role']

    # Redirect them to the OauthController, to fix the api_session,
    return redirect('/#!/login/oauth')

def __oauth_failed_login_redirect(reason='invalid_cred'):
    session['reason'] = reason

    return redirect('/#!/login/oauth')
