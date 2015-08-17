# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import json
import os

# ldap settings as such:
# uri -> URI to ldap server
# baseDN -> baseDN for users (remove for Active Directory)
#
# emailAttribute -> typically mail in OpenLDAP or userPrincipalName in AD
# groupMembershipAttribute -> typically member or uniqueMember
# usernameAttribute -> typically uid in OpenLDAP or samAccountName in AD
#
# checkAuthorizedGroups -> if true (instead of false), require group membership in addition to valid user id
# authorizedGroups -> list of groups where users are authorized to use Minion (if checkAuthorizedGroups is true)

DEFAULT_CONFIG_PATH = "/etc/minion"

def _load_config(name, default_path=DEFAULT_CONFIG_PATH):
    """
    Load the named configuration file from either the system in
    /etc/minion or if that does not exist from ~/.minion. Returns None
    if neither exists. Throws an exception if the file could not be
    opened, read or parsed.
    """
    if os.path.exists(os.path.join(default_path, name)):
        with open(os.path.join(default_path, name)) as fp:
            return json.load(fp)
    if os.path.exists(os.path.expanduser("~/.minion/%s" % name)):
        with open(os.path.expanduser("~/.minion/%s" % name)) as fp:
            return json.load(fp)

    # Fallback to using the Minion defaults
    cwfd = os.path.dirname(os.path.realpath(__file__))  # the directory of utils.py
    jsonf = os.path.realpath(os.path.join(cwfd, '..', '..', 'etc', name))
    with open(jsonf) as fp:
        return json.load(fp)

def frontend_config():
    """
    Load the frontend config from the two known locations. If it does
    not exist then return a copy of the default config.
    """
    return _load_config("frontend.json")
