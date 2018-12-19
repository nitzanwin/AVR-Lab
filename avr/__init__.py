import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_mail import Mail

app = Flask(__name__)

# initialize the log handler
logHandler = RotatingFileHandler('siteLog.log', maxBytes=10240, backupCount=5)
logHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
# set the log handler level
logHandler.setLevel(logging.INFO)
# set the app logger level
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logHandler) 

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
ma = Marshmallow(app)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LfW_XoUAAAAAEVZdK6w22Zu5CxxEfY93RcV0x5M'
app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('RECAPTCHA_PRIVATE_KEY')
app.config['RECAPTCHA_DATA_ATTRS'] = {'theme': 'light'}

# this import should be at the bottom to avoid circular import
from avr import routes