from pymongo import MongoClient
import os, dotenv, requests, time, datetime, random, logging, json, arrow
from argon2 import PasswordHasher

ph = PasswordHasher()
dotenv.load_dotenv()
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
mongo = MongoClient(os.environ.get('MONGO_URI', None))
days_dict = {"Sun": 1, "Mon": 2, "Tue": 3, "Wed": 4, "Thu": 5, "Fri": 6, "Sat": 7}


def convert_time(document, user, text):
    if text == 'false':
        text = 0
    hour = int(document["time"].split(":")[0])
    minute = int(document["time"].split(":")[1])
    if hour <= 9:
        hour = f'0{hour}'
    if minute <= 9:
        minute = f'0{minute}'
    user_info = {'days': []}
    for day in document['days']:
        Time = arrow.get(f'2021-08-{days_dict[day]} {hour}:{minute}', 'YYYY-MM-D HH:mm').shift(
            minutes=(int(user["offset"].split(".")[1]) - int(text)), hours=int(user["offset"].split(".")[0]))
        user_info['hour'] = int(Time.strftime('%-H'))
        user_info['minute'] = int(Time.strftime('%-M'))
        user_info['days'].append(Time.strftime('%a'))
    return user_info


def message():
    changes = {}
    print('Started')
    while True:
        for document, change in changes.items():
            print(document)
            print(change)
            mongo.zoom_opener.links.find_one_and_update({'username': document[0], 'id': int(document[1])}, {'$set': change})
        changes = {}
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
                user_info = convert_time(document, user, document['text'])
                if dict(user).get('number') and document['text'] != "false" and not (info['day'] not in user_info['days']
                        or (info['hour'], info['minute']) != (user_info['hour'], user_info['minute']))\
                        and document['starts'] == 0:
                    print('sending')
                    data = {'id': document['id'], 'number': user['number'], 'active': document['active'],
                            'name': document['name'], 'text': document['text'], 'key': os.environ.get('TEXT_KEY')}
                    response = requests.post("https://linkjoin.xyz/send_message", json=data,
                                             headers={'Content-Type': 'application/json'})
                    print(response)
                    print(response.text)

                user_info = convert_time(document, user, 0)
                if info['day'] not in user_info['days'] or (info['hour'], info['minute']) != (
                    user_info['hour'], user_info['minute']) or document['active'] == 'false':
                    continue
                # Check if the link is active or if it has yet to start
                if document['repeat'] == 'never' and int(document['starts']) == 0:
                    if len(document['days']) == 1:
                        changes[(document['username'], document['id'])] = {'active': 'false', 'text': 'false'}
                    else:
                        document['days'].remove(arrow.utcnow().shift(hours=-int(float(user['offset']))).strftime('%a'))
                        changes[(document['username'], document['id'])] = {'days': document['days']}
                    continue
                elif int(document['starts']) != 0:
                    changes[(document['username'], document['id'])] = {'starts': int(document['starts'])-1}
                    continue
                if document['repeat'][0].isdigit():
                    accept = [int(document['repeat'][0]) * len(user_info['days']) + x - len(user_info['days']) + 1
                              for x in
                              range(len(user_info['days']))]
                    if int(document['occurrences']) == accept[-1]:
                        changes[(document['username'], document['id'])] = {'occurrences': 0}
                    else:
                        changes[(document['username'], document['id'])] = {'occurrences': int(document['occurrences']) + 1}
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
