# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import Flask

app = Flask(__name__)

from minion.frontend import oauth, views
from minion.frontend.utils import frontend_config

def configure_app(app, production=True, debug=True):
    app.debug = debug
    app.use_evalex = False
    if production:
        config = frontend_config()
        if config.get('session-secret') is None:
            raise Exception("Configure a sesssion-secret in the configuration for production usage")
        app.secret_key = config.get('session-secret')
    else:
        app.secret_key =  "ThisIsOnlyForDevelopmentMode"
    return app
