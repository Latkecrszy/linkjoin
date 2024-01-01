import dotenv, jinja2, os
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from twilio.rest import Client

dotenv.load_dotenv()
hasher = PasswordHasher()
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
db = MongoClient(os.environ.get('MONGO_URI', None)).zoom_opener
motor = AsyncIOMotorClient(os.environ.get('MONGO_URI', None)).zoom_opener
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
TWILIO_SID = os.environ.get('TWILIO_SID', None)
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)
client = Client(TWILIO_SID, TWILIO_TOKEN)
environment = jinja2.Environment()
text_messages = [
    'LinkJoin Reminder: Your link, {name}, will open in {text} minutes. To stop receiving text reminders, log into your LinkJoin account and edit your meeting.',
]
env = os.environ.get('ENVIRONMENT', None)
scheduler = AsyncIOScheduler(timezone=utc)
