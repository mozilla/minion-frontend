# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__);
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.expanduser("~/minion-frontend.db")
db = SQLAlchemy(app)

from minion.frontend import views, models
