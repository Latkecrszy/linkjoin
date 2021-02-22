from flask import Flask, make_response, jsonify, request, abort, render_template, redirect, url_for
from flask_pymongo import PyMongo
import jinja2, json, os, dotenv, datetime, dateutil.tz, base64, re, argon2
from argon2 import PasswordHasher
from flask_cors import CORS
ph = PasswordHasher()
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
cors = CORS(app, resources={r'/db/*': {"origins": ["https://linkjoin.xyz", "http://127.0.0.1:5000"]}})

@app.route("/")
def main():
    return render_template("website.html")


@app.route("/login")
def Login():
    return render_template("login.html", error=None)


@app.route("/signup")
def Signup():
    return render_template("signup.html", error=None)


@app.route("/open")
def open():
    login_info = request.cookies.get('login_info')
    if login_info:
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        return render_template("redirect.html", username=login_info['username'])
    return redirect("/login")


@app.route("/login_error", methods=['POST'])
def login():
    response = make_response(redirect("/links"))
    mongo = PyMongo(app)
    login_db = mongo.db.login
    hasher = PasswordHasher()
    login_info = {'username': request.form.get("email").lower(), 'password': hasher.hash(request.form.get("password"))}
    if login_db.find_one({'username': request.form.get("email").lower()}) is None:
        return render_template("login.html", error="username_not_found")
    authorization = login_db.find_one({'username': request.form.get("email").lower()})
    try:
        ph.verify(authorization['password'], request.form.get("password"))
    except argon2.exceptions.VerifyMismatchError:
        return render_template("login.html", error="incorrect_password")
    cookie = {key: value for key, value in login_info.items() if key != "_id"}
    cookie = json.dumps(cookie)
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie)
    return response


@app.route("/signup_error", methods=["POST"])
def signup():
    hasher = PasswordHasher()
    response = make_response(redirect("/links"))
    mongo = PyMongo(app)
    login_db = mongo.db.login
    email = request.form.get("email").lower()
    if not re.search(".+@[a-z+._\-!#$%&'*=?^`{|}~]+[.][a-z]+", email):
        return render_template("signup.html", error="invalid_email")
    login_info = {'username': email, 'password': request.form.get("password")}
    if login_db.find_one({'username': request.form.get("email").lower()}) is not None:
        return render_template("signup.html", error="email_in_use")
    HASH = hasher.hash(request.form.get("password"))
    login_db.insert_one({'username': request.form.get("email").lower(), 'password': HASH})
    cookie = {key: value for key, value in login_info.items() if key != "_id"}
    cookie = json.dumps(cookie)
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie)
    return response


@app.route("/added", methods=["POST"])
def register_link():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    id_db = mongo.db.id
    if request.cookies.get('login_info'):
        if "https" not in request.form.get("link"):
            link = f"https://{request.form.get('link')}"
        else:
            link = request.form.get("link")
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        print([request.form.get(day) for day in dict(request.form)])
        print([day for day in dict(request.form) if day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(day) == "true"])
        links_db.insert_one({"username": login_info['username'], "id": int(dict(id_db.find_one({"_id": "id"}))['id']), 'days': [day for day in dict(request.form) if day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(day) == 'true'], 'time': request.form.get("time"), 'link': link, 'name': request.form.get('name'), "active": "true"})
        id_db.find_one_and_update({"_id": "id"}, {"$inc": {"id": 1}})
        return redirect("/links")
    else:
        print(request.cookies)
        return make_response({"it": "didn't work"})


@app.route("/links")
def links():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_list = links_db.find({"username": login_info['username']})
        links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "username" and i != "password"} for link in links_list]
        link_names = [link['name'] for link in links_list]
        sort = request.args.get("sort") if request.args.get("sort") else "no"
        return render_template("links.html", username=login_info['username'], link_names=link_names, sort=sort)
    else:
        return redirect("/login")



@app.route("/delete", methods=["POST", "GET"])
def delete():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_delete({"username": login_info['username'], 'id': int(request.args.get("id"))})
        return redirect("/links")
    return redirect("/login")


@app.route("/update", methods=["POST"])
def update():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        print([day for day in dict(request.form) if
                                      day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(
                                          day) == 'true'])
        print(dict(request.form))
        if "https" not in request.form.get("link"):
            link = f"https://{request.form.get('link')}"
        else:
            link = request.form.get("link")
        links_db.find_one_and_replace({"username": login_info['username'], 'id': int(request.args.get("id"))}, {"username": login_info['username'],
                             'days': [day for day in dict(request.form) if
                                      day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(
                                          day) == 'true'], 'time': request.form.get("time"),
                             'link': link, 'name': request.form.get('name'), "active": "true", 'id': int(request.args.get("id"))})
        return redirect("/links")
    return redirect("/login")


@app.route("/deactivate")
def deactivate():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        print(links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))}, {"$set": {"active": "false"}}))
        return redirect("/links")
    return redirect("/login")


@app.route("/activate")
def activate():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))}, {"$set": {"active": "true"}})
        return redirect("/links")
    return redirect("/login")


@app.route("/db", methods=["GET", "POST"])
def db():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    username = request.args.get("username")
    links_list = links_db.find({"username": username})
    links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "password"} for
                  link in links_list]
    return make_response(jsonify(links_list))


@app.route("/giveid")
def giveid():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    id_db = mongo.db.id
    for document in links_db.find():
        if 'id' not in dict(document).keys():
            print(dict(document))
            doc = dict(document)
            doc['id'] = int(dict(id_db.find_one({"_id": "id"}))['id'])
            links_db.find_one_and_replace(dict(document), doc)
            id_db.find_one_and_update({"_id": "id"}, {"$inc": {"id": 1}})
    return make_response({"done": "it"})


@app.route("/otherlinks")
def otherlinks():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_list = links_db.find({"username": login_info['username']})
        links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "username" and i != "password"}
                      for link in links_list]
        link_names = [link['name'] for link in links_list]
        return render_template("alternate_links.html", username=login_info['username'], link_names=link_names)
    else:
        return redirect("/login")


if __name__ == "__main__":
    app.run()
