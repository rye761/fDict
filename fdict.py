from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from flask.ext.pymongo import PyMongo
from flask.ext.login import LoginManager
from flask.ext.bcrypt import Bcrypt

#Config
DEBUG = True
SECRET_KEY = '5eb5159208129d335c34fbbf838c83d94286bfaf5b064844' #This should be changed if this is ever run in production, though it is unlikely it will ever need to be, seeing as this is a test project.

app = Flask(__name__)
app.config.from_object(__name__)
mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        #check that everthing was filled out, and that passwords match
        if username and password and password_confirm and password == password_confirm:
            password_hash = bcrypt.generate_password_hash(password)
            mongo.db.fdict_users.insert({'username': username, 'password_hash': password_hash})
            return "User added"
        else:
            flash('Missing entry or unmatched passwords')
            return redirect(url_for('register_user'))
    else:
        return render_template('register.html')

@app.route('/login')
def login():
    pass
if __name__ == '__main__':
    app.run()
