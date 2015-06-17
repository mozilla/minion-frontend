# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import copy
import json
import os


DEFAULT_FRONTEND_CONFIG = {
    'backend-api': {
        'url': 'http://127.0.0.1:8383'
    },
    'login': {
		'type': 'persona', # persona OR ldap

		'ldap' : {
			'uri': 'ldaps://ldap.server/', # URI of the LDAP server
			'base': 'ou=test,dc=test_dc', # base dn for bind & search

			'uid_filter' : 'uid', # Filter for the username (uid, samAccountName...)
			'mail_filter' : 'mail', # Filter for the mail (mail, email...)

			'check_authorized_groups' : True, # True if we want to check if the user is in a list of groups

			'group_objectClass' : 'groupOfNames', # objectClass to check the group
			'group_base' : 'ou=group,dc=test_dc', # base dn for search to check the group

			'authorized_groups' : ['groupTest1', 'groupTest2'] # List of the authorized groups
		}
	}
}


def _load_config(name):
    """
    Load the named configuration file from either the system in
    /etc/minion or if that does not exist from ~/.minion. Returns None
    if neither exists. Throws an exception if the file could not be
    opened, read or parsed.
    """
    if os.path.exists("/etc/minion/%s" % name):
        with open("/etc/minion/%s" % name) as fp:
            return json.load(fp)
    if os.path.exists(os.path.expanduser("~/.minion/%s" % name)):
        with open(os.path.expanduser("~/.minion/%s" % name)) as fp:
            return json.load(fp)

def frontend_config():
    """
    Load the frontend config from the two known locations. If it does
    not exist then return a copy of the default config.
    """
    return _load_config("frontend.json") or copy.deepcopy(DEFAULT_FRONTEND_CONFIG)
