from flask import Flask, request, redirect, url_for, render_template, flash, abort, Response, jsonify
from flask.ext.pymongo import PyMongo
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask.ext.bcrypt import Bcrypt
from bson import ObjectId
from flask_jsglue import JSGlue

#Config
DEBUG = True
SECRET_KEY = '5eb5159208129d335c34fbbf838c83d94286bfaf5b064844' #This should be changed if this is ever run in production, though it is unlikely it will ever need to be, seeing as this is a test project.

app = Flask(__name__)
app.config.from_object(__name__)
mongo = PyMongo(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
jsglue = JSGlue(app)

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
    recent_entries = list(mongo.db.fdict_words.find().sort('_id', -1).limit(10))
    for entry in recent_entries:
        entry['view_url'] = url_for('view_definition', definitionid=str(entry['_id']))
        entry['user_username'] = mongo.db.fdict_users.find_one({'_id': entry['user']})['username']
    return render_template('index.html', recent_entries=recent_entries)

@app.route('/search', methods=['GET'])
def search_word():
    query = request.args.get('q')
    if query:
        query = request.args.get('q')
        results = list(mongo.db.fdict_words.find({'$text': {'$search': query}}))
        for entry in results:
            entry['view_url'] = url_for('view_definition', definitionid=str(entry['_id']))
            entry['user_username'] = mongo.db.fdict_users.find_one({'_id': entry['user']})['username']
        return render_template('search.html', results=results)
    else:
        #This will happen if the user sends an empty search. Just take them back to home and let them know what they did wrong.
        flash('You need to submit a query to search', 'danger')
        return redirect(url_for('index'))
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
            flash('Missing entry or unmatched passwords', 'danger')
            return redirect(url_for('register_user', username=username))
    else:
        username = request.args.get('username')
        return render_template('register.html', username=username)

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
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login', username=username))
    else:
        username = request.args.get('username')
        return render_template('login.html', username=username)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        word = request.form['word']
        definition = request.form['definition']
        if word and definition:
            mongo.db.fdict_words.insert({'user': current_user.userID, 'word': word, 'definition': definition, 'votes': 0, 'voters': []})
            flash('Definition submitted', 'success')
            return redirect(url_for('index'))
        else:
            flash('You need to provide both a word and definition', 'danger')
            return redirect(url_for('create'))
        return redirect(url_for('index'))
    else:
        return render_template('create.html')

@app.route('/view/<definitionid>')
def view_definition(definitionid):
    definitionObjectId = ObjectId(definitionid)
    definitionObject = mongo.db.fdict_words.find_one({'_id': definitionObjectId})
    definitionUserObject = mongo.db.fdict_users.find_one({'_id': definitionObject['user']})
    if current_user.is_authenticated():
        if current_user.userID in definitionObject['voters']:
            hasVoted = True
        else:
            hasVoted = False
    else:
        hasVoted = False

    if definitionObject:
        return render_template('view_definition.html', word=definitionObject['word'], definition=definitionObject['definition'], votes=len(definitionObject['voters']), user=definitionUserObject, defid=definitionid, hasVoted=hasVoted)
    else:
        abort(404)

@app.route('/addvote', methods=['POST'])
def add_vote():
    #This function adds a vote for a definition. It is meant to be called using AJAX
    if current_user.is_authenticated():
        definitionObjectId = ObjectId(request.form['definition_id'])
        definitionObject = mongo.db.fdict_words.find_one({'_id': definitionObjectId})
        if current_user.userID in definitionObject['voters']:
            abort(501)
        definitionObject['voters'].append(current_user.userID)
        mongo.db.fdict_words.save(definitionObject)
        return jsonify(votes = len(definitionObject['voters']))
    else:
        return abort(501)
        
@app.route('/revokevote', methods=['POST'])
def revoke_vote():
    #This function removes a vote for a definition. It is meant to be called using AJAX
    if current_user.is_authenticated():
        definitionObjectId = ObjectId(request.form['definition_id'])
        definitionObject = mongo.db.fdict_words.find_one({'_id': definitionObjectId})
        if not current_user.userID in definitionObject['voters']:
            abort(501)
        definitionObject['voters'].remove(current_user.userID)
        mongo.db.fdict_words.save(definitionObject)
        return jsonify(votes = len(definitionObject['voters']))
    else:
        return abort(501)

@app.route('/deletedef', methods=['POST'])
def delete_def():
    #This function removes an entry if the calling user created it. It is meant to be called using AJAX
    if current_user.is_authenticated():
        definitionObjectId = ObjectId(request.form['definition_id'])
        definitionObject = mongo.db.fdict_words.find_one({'_id': definitionObjectId})
        definitionUserObject = mongo.db.fdict_users.find_one({'_id': definitionObject['user']})
        if not current_user.userID ==  definitionUserObject['_id']:
            abort(501)
        print('about to delete')
        resp = Response(None, status=200)
        mongo.db.fdict_words.remove(definitionObjectId);
        return resp
    else:
        return abort(501)
        

if __name__ == '__main__':
    app.run()
    mongo.db.fdict_words.ensure_index([
        ('word', 'text'),
    ],
    name='search_index',
    weights={
        'word':100
    })
