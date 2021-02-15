from flask import Flask, make_response, jsonify, request, abort, render_template, redirect, url_for
from flask_pymongo import PyMongo
import jinja2, json, os, dotenv, datetime, dateutil.tz, base64
app = Flask(__name__)
dotenv.load_dotenv()
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)


@app.route("/")
def main():
    return render_template("website.html")


@app.route("/login")
def Login():
    return render_template("login.html", error=None)


@app.route("/signup")
def signup():
    return render_template("signup.html", error=None)


@app.route("/open")
def open():
    mongo = PyMongo(app)
    login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
    login_db = mongo.db.login
    authorized = login_db.find_one({"username": login_info['username'], "password": login_info['password']})
    if authorized:
        links_db = mongo.db.links
        links_list = links_db.find({"username": login_info['username'], 'password': login_info['password']})
        links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "username" and i != "password"}
                      for link in links_list]
        date = datetime.datetime.now(dateutil.tz.gettz("America/Los_Angeles"))
        day = date.strftime("%a").capitalize()
        hour = int(date.strftime("%H"))
        minute = int(date.strftime("%M"))
        return render_template("redirect.html", num=len(links_list), user_links=links_list, username=login_info['username'], password=login_info['password'], day=day, hour=hour, minute=minute)
    else:
        return redirect("/login")


@app.route("/login_error", methods=['POST'])
def login():
    response = make_response(redirect("/links"))
    mongo = PyMongo(app)
    login_db = mongo.db.login
    login_info = {'username': request.form.get("email"), 'password': request.form.get("password")}
    if login_db.find_one({'username': request.form.get("email")}) is None:
        return render_template("login.html", error="username_not_found")
    print(f"This: {login_db.find_one({'username': request.form.get('email')})}")
    authorization = login_db.find_one(login_info)
    if authorization is None:
        return render_template("login.html", error="incorrect_password")
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
    if request.cookies.get('login_info'):
        login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
        print([request.form.get(day) for day in dict(request.form)])
        print([day for day in dict(request.form) if day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(day) == "true"])
        links_db.insert_one({"username": login_info['username'], 'password': login_info['password'], 'days': [day for day in dict(request.form) if day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] and request.form.get(day) == 'true'], 'time': request.form.get("time"), 'link': request.form.get("link"), 'name': request.form.get('name'), "active": "true"})
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
        links_list = links_db.find({"username": login_info['username'], 'password': login_info['password']})
        links_list = [{str(i): str(j) for i, j in link.items() if i != "_id" and i != "username" and i != "password"} for link in links_list]
    else:
        return redirect("/login")
    return render_template("links.html", links=links_list, num=len(links_list))


if __name__ == "__main__":
    app.run()
