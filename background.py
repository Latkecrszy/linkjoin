from pymongo import MongoClient
import os, dotenv, requests, time, datetime, random, logging, json
from argon2 import PasswordHasher

ph = PasswordHasher()
dotenv.load_dotenv()
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
mongo = MongoClient(os.environ.get('MONGO_URI', None))


def get_time(hour: int, minute: int, days: list, before) -> tuple:
    days_dict = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}
    before = 0 if before == "false" or before is None else int(before) + 1
    minute -= before
    if minute < 0:
        minute += 60
        hour -= 1
        if hour <= 0:
            hour += 24
            for index, day in enumerate(days):
                day = days_dict[day]
                day -= 1
                if day < 0:
                    day = 6
                days[index] = day
    elif hour >= 24:
        hour -= 24
        for index, day in enumerate(days):
            day = days_dict[day]
            day += 1
            if day > 6:
                day = 0
            days[index] = {j: i for i, j in days_dict.items()}[day]
    return hour, minute, days


def message():
    print('Started')
    while True:
        print('Running')
        start = time.perf_counter()
        # Define the users db, links db, and current time
        users = mongo.zoom_opener.login
        links = mongo.zoom_opener.links
        current_time = datetime.datetime.utcnow()
        # Create a dictionary with all the needed info about the time
        info = {"day": current_time.strftime("%a"), "hour": current_time.hour, "minute": current_time.minute}
        # Loop through the links
        if os.environ.get('IS_HEROKU') == 'false':
            documents = list(links.find({'username': 'setharaphael7@gmail.com'}))
            otps = mongo.zoom_opener.otp.find({'email': 'setharaphael7@gmail.com'})
            anonymous_token = []
        else:
            documents = list(links.find())
            otps = mongo.zoom_opener.otp.find()
            anonymous_token = mongo.zoom_opener.anonymous_token.find()
        for document in documents:
            user = users.find_one({"username": document['username']}) if users.find_one(
                {"username": document['username']}) is not None else {}
            # Create a dictionary with all the needed info about the link time
            if 'offset' in user:
                user_info = {}
                user_info['hour'], user_info['minute'], user_info['days'] = get_time(
                    int(document['time'].split(":")[0]) + int(user['offset'].split(".")[0]),
                    int(document['time'].split(":")[1]) + int(user['offset'].split(".")[1]), document['days'],
                    dict(document).get('text'))
                if dict(user).get('number') and document['text'] != "false" and not (info['day'] not in user_info['days']
                        or (info['hour'], info['minute']) != (user_info['hour'], user_info['minute'])):
                    data = {'id': document['id'], 'number': user['number'], 'active': document['active'],
                            'name': document['name'], 'text': document['text'], 'key': os.environ.get('TEXT_KEY')}
                    response = requests.post("https://linkjoin.xyz/send_message", json=data,
                                             headers={'Content-Type': 'application/json'})
                    print(response)
                    print(response.text)

                user_info['hour'], user_info['minute'], user_info['days'] = get_time(
                    int(document['time'].split(":")[0]) + int(user['offset'].split(".")[0]),
                    int(document['time'].split(":")[1]) + int(user['offset'].split(".")[1]), document['days'],
                    -1)

                if info['day'] not in user_info['days'] or (info['hour'], info['minute']) != (
                user_info['hour'], user_info['minute']):
                    continue
                # Check if the link is active or if it has yet to start
                if document['active'] != "false":
                    try:
                        print(document['starts'])
                        if int(document['starts']) > 0:
                            for i in range(5):
                                print('CHANGING')
                            print(mongo.zoom_opener.links.find_one_and_update(
                                {'username': document['username'], 'name': document['name']},
                                {"$set": {"starts": int(document['starts']) - 1}}))
                            continue
                    except KeyError:
                        links.find_one_and_update(dict(document), {"$set": {"starts": 0}})
                    if document['repeat'][0].isdigit():
                        accept = [int(document['repeat'][0]) * len(user_info['days']) + x - len(user_info['days']) + 1
                                  for x in
                                  range(len(user_info['days']))]
                        if int(document['occurrences']) == accept[-1]:
                            links.find_one_and_update(dict(document), {"$set": {"occurrences": 0}})
                        else:
                            links.find_one_and_update(dict(document),
                                                      {"$set": {"occurrences": int(document['occurrences']) + 1}})
                            continue
        for document in otps:
            if document['time'] - 1 == 0:
                mongo.zoom_opener.otp.find_one_and_delete({'pw': document['pw']})
            else:
                mongo.zoom_opener.otp.find_one_and_update({'pw': document['pw']},
                                                          {'$set': {'time': document['time'] - 1}})
        for document in anonymous_token:
            if document.get('time'):
                if document['time'] - 1 == 0:
                    print('Changing tokens')
                    mongo.zoom_opener.anonymous_token.find_one_and_delete({'token': document['token']})
                else:
                    print('Changing tokens')
                    mongo.zoom_opener.anonymous_token.find_one_and_update({'token': document['token']},
                                                                          {'$set': {'time': document['time'] - 1}})
            else:
                print('Changing tokens')
                mongo.zoom_opener.anonymous_token.find_one_and_update({'token': document['token']},
                                                                      {'$set': {'time': 59}})
        sent = json.load(open('last-message.json'))
        for id, time_left in {i: j for i, j in sent.items()}.items():
            if time_left > 0:
                sent[id] = time_left - 1
            else:
                sent.pop(id)
        json.dump(sent, open('last-message.json', 'w'), indent=4)
        if os.environ.get('IS_HEROKU') == 'true':
            print('Checking days')
            analytics_data = mongo.zoom_opener.analytics.find_one({'id': 'analytics'})
            if analytics_data['day'] != int(current_time.strftime('%d')):
                analytics_data['daily_users'].append([])
                analytics_data['day'] = int(current_time.strftime('%d'))
                mongo.zoom_opener.analytics.find_one_and_replace({'id': 'analytics'}, analytics_data)
            if analytics_data['month'] != int(current_time.strftime('%m')):
                analytics_data['month'] = int(current_time.strftime('%m'))
                analytics_data['monthly_users'].append([])
                analytics_data['total_monthly_logins'].append(0)
                analytics_data['total_monthly_signups'].append(0)
                mongo.zoom_opener.analytics.find_one_and_replace({'id': 'analytics'}, analytics_data)
        # Wait 60 seconds
        speed = abs(60 - (time.perf_counter() - start))
        if speed < 50:
            print(f'Long time: {speed}')
        time.sleep(abs(60 - (time.perf_counter() - start)))
