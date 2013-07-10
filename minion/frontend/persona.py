# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import requests

def verify_assertion(assertion, audience):
    data = {'assertion': assertion, 'audience': audience}
    response = requests.post('https://verifier.login.persona.org/verify', data=data, timeout=5)
    if response.status_code != 200:
        return None
    receipt = json.loads(response.content)
    if receipt.get('status') != 'okay':
        return None
    return receipt

