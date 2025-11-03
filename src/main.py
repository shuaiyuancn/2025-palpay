from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH"))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase initialized successfully!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")

@app.route('/')
def hello_world():
    return 'Hello, PalPay!'

if __name__ == '__main__':
    app.run(debug=True)