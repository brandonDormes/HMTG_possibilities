from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dfkjfsdlf'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///hmtg_possib_DB.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = "None"


db = SQLAlchemy(app)
cors = CORS(app)
bootstrap = Bootstrap(app)


from . import views
if __name__ == '__main__':
    app.run()
