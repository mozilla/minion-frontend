from minion.frontend import db


ROLE_GUEST = 0
ROLE_DEVELOPER = 1
ROLE_ADMIN = 2
ROLE_SUPERUSER = 7


users_sites_table = db.Table('users_sites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True)
)


sites_plans_table = db.Table('sites_plans',
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True),
    db.Column('plan_id', db.Integer, db.ForeignKey('plans.id'), primary_key=True)
)


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_GUEST)

    # A user owns many sites. Sites can have many owners.
    sites = db.relationship('Site', secondary=users_sites_table, backref=db.backref('sites', lazy='dynamic'))

    @classmethod
    def get_or_create(clazz, email):
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, role=ROLE_GUEST)
            db.session.add(user)
            db.session.commit()
        return user

    def __repr__(self):
        return '<User %r>' % self.email


class Site(db.Model):

    __tablename__ = "sites"

    id = db.Column(db.Integer, primary_key = True)
    url = db.Column(db.String(128), index = True, unique = False)

    # A site can have many plans. Plans have many sites.
    plans = db.relationship('Plan', secondary=sites_plans_table, backref=db.backref('sites', lazy='dynamic'))

    def __repr__(self):
        return '<Site %r>' % self.url


class Plan(db.Model):

    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key = True)
    manual = db.Column(db.Boolean, default = True)

    # This simply references a minion plan name for now. Eventually the complete plan configuration will go in here.
    minion_plan_name = db.Column(db.String(64), index = True, unique = False)

    # A plan has many scans that are executed on that plan
    scans = db.relationship('Scan', backref='plan', lazy='dynamic')

    def __repr__(self):
        return '<Plan %r>' % self.name


class Scan(db.Model):

    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key = True)

    # These fields are copied from the scan result in minion. This can go away when we store full scan results in the database.
    minion_scan_uuid = db.Column(db.String(40), index = True, unique = True)
    minion_scan_status = db.Column(db.String(32))
    minion_scan_created = db.Column(db.DateTime)
    minion_scan_high_count = db.Column(db.Integer, default = 0)
    minion_scan_medium_count = db.Column(db.Integer, default = 0)
    minion_scan_low_count = db.Column(db.Integer, default = 0)
    minion_scan_info_count = db.Column(db.Integer, default = 0)

    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))

    def __repr__(self):
        return '<Scan %r/%r>' % (self.id, self.minion_scan_uuid)


# Get an overview of sites and plans
# select sites.url,plans.minion_plan_name from sites, plans, sites_plans where sites_plans.site_id = sites.id and sites_plans.plan_id = plans.id;

# Get an overview of users, sites and plans
# select users.email,sites.url,plans.minion_plan_name from users, users_sites, sites, plans, sites_plans where users.id = users_sites.user_id and users_sites.site_id = sites.id and sites_plans.site_id = sites.id and sites_plans.plan_id = plans.id;
