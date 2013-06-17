# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Flask

app = Flask(__name__);

from minion.frontend import views

def configure_app(app, debug=False):
    if debug:
        app.debug = True
        app.secret_key =  "ThisIsOnlyForDevelopmentMode"
    else:
        raise Exception("TODO Implement a real session store for production apps")
    return app
