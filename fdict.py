from flask import Flask, request, redirect, url_for, render_template, flash
from flask.ext.pymongo import PyMongo
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user
from flask.ext.bcrypt import Bcrypt
from bson import ObjectId

#Config
DEBUG = True
SECRET_KEY = '5eb5159208129d335c34fbbf838c83d94286bfaf5b064844' #This should be changed if this is ever run in production, though it is unlikely it will ever need to be, seeing as this is a test project.

app = Flask(__name__)
app.config.from_object(__name__)
mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

class User(UserMixin):
    def __init__(self, username, userID):
        self.username = username
        self.userID = userID
    def get_id(self):
        return str(self.userID)

@login_manager.user_loader
def load_user(userID):
    objectID = ObjectId(userID)
    userObject = mongo.db.fdict_users.find_one({'_id': objectID})
    if userObject:
        user = User(userObject['username'], userObject['_id'])
        return user
    else:
        return None
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
            userObjectID =mongo.db.fdict_users.insert({'username': username, 'password_hash': password_hash})
            user = User(username, userObjectID)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Missing entry or unmatched passwords')
            return redirect(url_for('register_user'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        userObject = mongo.db.fdict_users.find_one({'username': username})
        if userObject and bcrypt.check_password_hash(userObject['password_hash'], password):
            user = User(userObject['username'], userObject['_id'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run()
