from pymongo import MongoClient
import os, dotenv, requests, time as t, datetime, json
from argon2 import PasswordHasher

ph = PasswordHasher()
dotenv.load_dotenv()
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
mongo = MongoClient(os.environ.get('MONGO_URI', None))


def message():
    changes = {}
    print('Started')
    while True:
        for document, change in changes.items():
            mongo.zoom_opener.links.find_one_and_update({'username': document[0], 'id': int(document[1])},
                                                        {'$set': change})
        changes = {}
        print('Running')
        start = t.perf_counter()
        users = mongo.zoom_opener.login
        links = mongo.zoom_opener.links
        time = datetime.datetime.utcnow()
        if os.environ.get('IS_HEROKU') == 'false':
            links_search = {'username': 'setharaphael7@gmail.com', 'time': f'{int(time.strftime("%H"))}:{time.strftime("%M")}'}
            otps = mongo.zoom_opener.otp.find({'email': 'setharaphael7@gmail.com'})
            anonymous_token = []
        else:
            links_search = {'active': 'true', 'activated': 'true', 'time': f'{int(time.strftime("%H"))}:{time.strftime("%M")}'}
            otps = mongo.zoom_opener.otp.find()
            anonymous_token = list(mongo.zoom_opener.anonymous_token.find())


        for i in ["5", "10", "15", "20", "30", "45", "60"]:
            future_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=int(i))
            if os.environ.get('IS_HEROKU') == 'false':
                text_search = {'username': 'setharaphael7@gmail.com',
                               'time': f'{int(future_time.strftime("%H"))}:{future_time.strftime("%M")}',
                               'text': i}
            else:
                text_search = {
                    'active': 'true', 'activated': 'true',
                    'time': f'{int(future_time.strftime("%H"))}:{future_time.strftime("%M")}', 'text': i
                }
            for document in links.find(text_search):
                user = users.find_one({"username": document['username']}) if users.find_one(
                    {"username": document['username']}) is not None else {}
                if dict(user).get('number') and document['text'] != "false" and time.strftime('%a') in document['days'] and not document.get('starts'):
                    print('sending')
                    data = {'id': document['id'], 'number': user['number'], 'active': document['active'],
                            'name': document['name'], 'text': document['text'], 'key': os.environ.get('TEXT_KEY')}
                    response = requests.post("https://linkjoin.xyz/send_message", json=data,
                                             headers={'Content-Type': 'application/json'})
                    print(response)
                    print(response.text)


        for document in links.find(links_search):
            if document['repeat'][0].isdigit():
                accept = [int(document['repeat'][0]) * len(document['days']) + x - len(document['days']) + 1
                          for x in
                          range(len(document['days']))]
                if int(document['occurrences']) == accept[-1]:
                    changes[(document['username'], document['id'])] = {'occurrences': 0}
                else:
                    changes[(document['username'], document['id'])] = {
                        'occurrences': int(document['occurrences']) + 1}
                    continue
        edit = {}
        for document in otps:
            if document['time'] - 1 == 0:
                edit[document['pw']] = {'type': 'delete'}
            else:
                edit[document['pw']] = {'type': 'edit', 'content': {'$set': {'time': document['time'] - 1}}}

        for otp, change in edit.items():
            if change['type'] == 'edit':
                mongo.zoom_opener.otp.find_one_and_update({'pw': otp}, change['content'])
            elif change['type'] == 'delete':
                mongo.zoom_opener.otp.find_one_and_delete({'pw': otp})
        edit = {}
        changed = 0
        for document in anonymous_token:
            if document.get('time'):
                if document['time'] - 1 == 0:
                    edit[document['token']] = {'type': 'delete'}
                else:
                    edit[document['token']] = {'type': 'edit', 'content': {'$set': {'time': document['time'] - 1}}}
                changed += 1
            else:
                changed += 1
                edit[document['token']] = {'type': 'edit', 'content': {'$set': {'time': 59}}}
        print(changed)
        for token, change in edit.items():
            if change['type'] == 'edit':
                mongo.zoom_opener.anonymous_token.find_one_and_update({'token': token}, change['content'])
            elif change['type'] == 'delete':
                mongo.zoom_opener.anonymous_token.find_one_and_delete({'token': token})
        sent = json.load(open('last-message.json'))
        for id, time_left in {i: j for i, j in sent.items()}.items():
            if time_left > 0:
                sent[id] = time_left - 1
            else:
                sent.pop(id)
        if os.environ.get('IS_HEROKU') == 'true':
            print('Checking days')
            if int(mongo.zoom_opener.new_analytics.find_one({'id': 'day'})['value']) != int(time.strftime('%d')):
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'day'}, {'$set': {'value': int(time.strftime('%d'))}})
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'daily_users'}, {'$push': {'value': []}})
            if int(mongo.zoom_opener.new_analytics.find_one({'id': 'month'})['value']) != int(time.strftime('%m')):
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'month'}, {'$set': {'value': int(time.strftime('%m'))}})
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'monthly_users'}, {'$push': {'value': []}})
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'total_monthly_logins'}, {'$push': {'value': 0}})
                mongo.zoom_opener.new_analytics.find_one_and_update({'id': 'total_monthly_signups'}, {'$push': {'value': 0}})

        speed = abs(60 - (t.perf_counter() - start))
        if speed < 50:
            print(f'Long time: {speed}')
        print(speed)
        t.sleep(speed)
