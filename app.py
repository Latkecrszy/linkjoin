from flask import Flask, make_response, jsonify, request, render_template, redirect
from flask_pymongo import PyMongo
import json, os, dotenv, base64, re, argon2
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
    cookie = json.dumps({key: value for key, value in login_info.items() if key != "_id"})
    cookie = str.encode(cookie)
    cookie = base64.b64encode(cookie)
    response.set_cookie('login_info', cookie, max_age=172800)
    return response


@app.route("/signup_error", methods=["POST"])
def signup():
    hasher = PasswordHasher()
    response = make_response(redirect("/links"))
    mongo = PyMongo(app)
    login_db = mongo.db.login
    email = request.form.get("email").lower()
    if not re.search("^[^@ ]+@[^@ ]+\.[^@ .]{2,}$", email):
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
    response.set_cookie('login_info', cookie, max_age=172800)
    return response


@app.route("/register")
def register():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    id_db = mongo.db.id
    print(request.args)
    if request.cookies.get('login_info'):
        if "https" not in request.args.get("link"):
            link = f"https://{request.args.get('link')}"
        else:
            link = request.args.get("link")
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if request.args.get("repeats") == "true":
            links_db.insert_one(
                {"username": login_info['username'], "id": int(dict(id_db.find_one({"_id": "id"}))['id']),
                 'days': request.args.get("days").split(","),
                 'time': request.args.get("time"), 'link': link, 'name': request.args.get('name'), "active": "true",
                 "recurring": "true"})
        else:
            links_db.insert_one(
                {"username": login_info['username'], "id": int(dict(id_db.find_one({"_id": "id"}))['id']),
                 'dates': [{"day": i.split("-")[2], "month": i.split("-")[1], "year": i.split("-")[0]} for i in
                           request.args.get("dates").split(",")],
                 'time': request.args.get("time"), 'link': link, 'name': request.args.get('name'), "active": "true",
                 "recurring": "false"})
        id_db.find_one_and_update({"_id": "id"}, {"$inc": {"id": 1}})
        return redirect("/links")
    return redirect("/login")


@app.route("/links")
def links():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "username" and i != "password"}
                      for link in links_db.find({"username": login_info['username']})]
        link_names = [link['name'] for link in links_list]
        sort = json.loads(request.cookies.get("sort"))['sort'] if request.cookies.get("sort") and \
                                                                  json.loads(request.cookies.get("sort"))['sort'] in [
                                                                      'time', 'day', 'datetime'] else "no"
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


@app.route("/update")
def update():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        if "https" not in request.args.get("link"):
            link = f"https://{request.args.get('link')}"
        else:
            link = request.args.get("link")
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        if request.args.get("repeats") == "true":
            links_db.find_one_and_replace({"username": login_info['username'], "id": int(request.args.get("id"))},
                                          {"username": login_info['username'], "id": int(request.args.get("id")),
                                           'days': request.args.get("days").split(","),
                                           'time': request.args.get("time"), 'link': link,
                                           'name': request.args.get('name'), "active": "true",
                                           "recurring": "true"})
        else:
            links_db.find_one_and_replace({"username": login_info['username'], "id": int(request.args.get("id"))},
                                          {"username": login_info['username'], "id": int(request.args.get("id")),
                                           'dates': [{"day": i.split("-")[2], "month": i.split("-")[1],
                                                      "year": i.split("-")[0]} for i in
                                                     request.args.get("dates").split(",")],
                                           'time': request.args.get("time"), 'link': link,
                                           'name': request.args.get('name'), "active": "true",
                                           "recurring": "false"})
        return redirect("/links")
    return redirect("/login")


@app.route("/deactivate")
def deactivate():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        print(links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))},
                                           {"$set": {"active": "false"}}))
        return redirect("/links")
    return redirect("/login")


@app.route("/activate")
def activate():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        links_db.find_one_and_update({"username": login_info['username'], 'id': int(request.args.get("id"))},
                                     {"$set": {"active": "true"}})
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


@app.route("/sort")
def sort():
    response = make_response(redirect("/links"))
    response.set_cookie("sort", json.dumps({"sort": request.args.get("sort")}))
    print(request.args.get("sort"))
    return response


@app.route("/reassign")
def reassign():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    for document in links_db.find():
        document = dict(document)
        if document['recurring'] == "true":
            document['repeat'] = "week"
            print("recurring")
        else:
            document['repeat'] = "none"
            print("non-recurring")
        document.pop('recurring')
        print(document)
    return make_response({"stuff": "happened"})


@app.route("/change_occurrence")
def change_occurrence():
    mongo = PyMongo(app)
    links_db = mongo.db.links
    links_db.find_one_and_update({"username": request.args.get("username"), "id": int(request.args.get("id"))},
                                 {"$set": {"occurrences": request.args.get("occurrences")}})
    return redirect("/links")


@app.route("/tos")
def tos():
    return make_response("Coming soon!")


@app.route("/privacy")
def privacy():
    return make_response("Coming soon!")


if __name__ == "__main__":
    app.run()
