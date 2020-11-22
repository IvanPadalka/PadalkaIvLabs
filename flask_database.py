from flask_script import Manager, prompt_bool, Command
from app import db

manager = Manager(usage="Perform database operations")

@manager.command
def drop():
    "Drops database tables"
    if prompt_bool("Are you sure to lose all your data?"):
        db.drop_all()

@manager.command
def createdb():
    "Create database"
    if prompt_bool("Do you want to create a database?"):
        db.create_all()

@manager.command
def recreate():
    "Rebuild the database"
    if prompt_bool("Do you want to rebuild a database?"):
        dropdb()
        createdb()

@manager.command
def init_data():
    print("initialization completed")