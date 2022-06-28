import dotenv
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from pymongo import MongoClient
import os


dotenv.load_dotenv()
hasher = PasswordHasher()
encoder = Fernet(os.environ.get('ENCRYPT_KEY', None).encode())
db = MongoClient(os.environ.get('MONGO_URI', None)).zoom_opener
VONAGE_API_KEY = os.environ.get("VONAGE_API_KEY", None)
VONAGE_API_SECRET = os.environ.get("VONAGE_API_SECRET", None)
TWILIO_SID = os.environ.get('TWILIO_SID', None)
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', None)