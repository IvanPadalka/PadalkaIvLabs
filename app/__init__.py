from flask import Flask
from flask_migrate import Migrate

from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin
from flask_ckeditor import CKEditor

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login = LoginManager(app)
migrate = Migrate(app, db)
login.login_view = 'login'
login.login_message_category = 'info'

ckeditor = CKEditor(app)

from app import modelviews
from app import models
from flask_admin.contrib.sqla import ModelView

admin = Admin(app, index_view=modelviews.MyAdminIndexView())
admin.add_view(modelviews.UserAdminView(models.User, db.session))
admin.add_view(modelviews.PostAdminView(models.Post, db.session))
from app import views