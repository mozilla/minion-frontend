# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import requests

BASE = "http://127.0.0.1:5000"

class TestFrontEndAPI(unittest.TestCase):
    def test_index_return_200(self):
        res = requests.get(BASE + "/")
        self.assertEqual(res.status_code, 200)

    def test_api_session_return_unsuccess(self):
        res = requests.get(BASE + '/api/session')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['success'], False)
