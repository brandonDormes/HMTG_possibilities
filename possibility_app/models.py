from . import db


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subID = db.Column(db.Integer, index=True, unique=False)
    prolific_id = db.Column(db.String(64), unique=True)
    trustee_id = db.Column(db.Integer)
    trial_order = db.Column(db.Integer)
    bonus = db.Column(db.Float)
    exp_feedback = db.Column(db.VARCHAR(300))
    trials = db.relationship('Trial', backref='subject', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return '<Subject %r>' % self.subID


class Trial(db.Model):
    __tablename__ = 'trials'
    id = db.Column(db.Integer, primary_key=True)
    trl = db.Column(db.String(64), unique=False)
    p1_pic = db.Column(db.String(64))
    inv = db.Column(db.Integer)
    mult = db.Column(db.Integer)
    pred = db.Column(db.Integer)
    ret = db.Column(db.Integer)
    reason = db.Column(db.VARCHAR(200))
    reason_start = db.Column(db.Integer) # time to start writing
    reason_rt = db.Column(db.Integer) # time to submit response
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'))

    def __repr__(self):
        return '<Trial %r>' % self.trl
