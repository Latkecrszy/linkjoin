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
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/open")
def open():
    mongo = PyMongo(app)
    login_info = json.loads(base64.b64decode(request.cookies.get('login_info')))
    print(login_info)
    login_db = mongo.db.login
    authorized = login_db.find_one({"username": login_info['username'], "password": login_info['password']})
    if authorized:
        links = mongo.db.links
        links = links.find()
        links = [{str(i): str(j) for i, j in link.items() if i != "_id"} for link in links]
        date = datetime.datetime.now(dateutil.tz.gettz("America/Los_Angeles"))
        day = date.strftime("%A").lower()
        hour = int(date.strftime("%I"))
        minute = int(date.strftime("%M"))
        amorpm = date.strftime("%p").lower()
        return render_template("redirect.html", num=len(links), user_links=links, username=login_info['username'], password=login_info['password'], day=day, hour=hour, minute=minute, amorpm=amorpm)
    else:
        return jsonify({"You are not logged in": ":("})


@app.route("/add", methods=['POST', 'GET'])
def login():
    username = request.form.get("email")
    password = request.form.get("password")
    response = make_response(render_template("register_link.html"))
    if username is not None:
        mongo = PyMongo(app)
        login_db = mongo.db.login
        login_info = {'username': username, 'password': password}
        if login_db.find_one({'username': username}) is None:
            login_db.insert_one(login_info)
            print('created account')
        else:
            authorization = login_db.find_one(login_info)
            if authorization is None:
                print('incorrect password')
            else:
                print('logged in')
        cookie = {key: value for key, value in login_info.items() if key != "_id"}
        print(cookie)
        cookie = json.dumps(cookie)
        print(cookie)
        cookie = str.encode(cookie)
        print(cookie)
        cookie = base64.b64encode(cookie)
        print(cookie)
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
        print(links_list)
    else:
        return redirect("/login")
    return render_template("links.html", links=links_list, num=len(links_list))


if __name__ == "__main__":
    app.run()
