from . import db


class Subject(db.Model):
    __tablename__ = 'subjects'
    prolific_id = db.Column(db.String(64), unique=True, primary_key=True, index=True)
    in_progress = db.Column(db.Boolean)
    complete = db.Column(db.Boolean)
    session_id = db.Column(db.VARCHAR(300))
    trustee_id = db.Column(db.Integer)
    trustee_strategy = db.Column(db.Integer)
    bonus = db.Column(db.Float)
    exp_feedback = db.Column(db.VARCHAR(300))
    trials = db.relationship('Trial', backref='subject', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return '<Subject %r>' % self.prolific_id


class Trial(db.Model):
    __tablename__ = 'trials'
    id = db.Column(db.Integer, primary_key=True)
    trl = db.Column(db.Integer, unique=False, index=True)
    p1_pic = db.Column(db.Integer)
    inv = db.Column(db.Integer)
    mult = db.Column(db.Integer)
    pred = db.Column(db.Integer)
    ret = db.Column(db.Integer)
    probe = db.Column(db.Boolean)
    reason = db.Column(db.VARCHAR(200))
    reason_start = db.Column(db.Integer) # time to start writing
    reason_rt = db.Column(db.Integer) # time to submit response
    prolific_id = db.Column(db.String, db.ForeignKey('subjects.prolific_id'))

    def __repr__(self):
        return '<Trial %r>' % self.trl
