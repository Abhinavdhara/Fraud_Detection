from flask import Flask, request, jsonify, send_from_directory,render_template_string, redirect
from flask_cors import CORS
import os
import json
import pandas as pd
import pickle
import random
from random import randint
from datetime import datetime, timedelta
from flask import request, jsonify
from datetime import datetime, timedelta, timezone
import pandas as pd
import requests # type: ignore


# V-02 EDIT start-------------------------------------
from pymongo import MongoClient

# Connect to MongoDB Atlas

def send_email(to_email, subject, body):
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {os.environ.get('RESEND_API_KEY')}",
            "Content-Type": "application/json",
        },
        json={
            "from": "onboarding@resend.dev",  # free test sender
            "to": [to_email],
            "subject": subject,
            "text": body,
        },
    )
    return response.status_code


MONGO_URI = os.environ.get('MONGO_URI')
client = MongoClient(MONGO_URI)

# Use a database (it will be created if it doesn't exist)
db = client["fraudshield"]  # You can name this however you want

# Define collections
users_col = db["users"]
alerts_col = db["alerts"]
transactions_col = db["transactions"]
otp_col = db["otp"]

# V-02 Edit END ----------------------------------------

app = Flask(__name__, static_folder='../frontend/assets', static_url_path='/assets')
CORS(app)

# File paths
USERS_FILE = 'users.json'
ALERTS_FILE = 'alerts.json'
TRANSACTIONS_FILE = 'transactions.json'
DATA_FILE = 'data/uploaded_data.csv'
MODEL_FILE = './model/fraud_detection_pipeline.pkl'
import joblib
pipeline = joblib.load("model/fraud_detection_pipeline.pkl")








otp_store = {}  # In-memory OTP store

# ---------- Utility Functions ----------

#----------------V-02 EDIT START------------------
# MongoDB connection setup (move this to top-level if not already done)
client = MongoClient(MONGO_URI)
db = client["fraudshield"]
users_col = db["users"]
alerts_col = db["alerts"]
transactions_col = db["transactions"]

# Instead of saving to JSON, insert directly to MongoDB
def save_transaction(record):
    transactions_col.insert_one(record)
# ----------------V-02 Edit END-----------------------------


# ---------- User Auth ----------
#-------------- V-02 Edit START---------------------------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Check if user already exists
    if users_col.find_one({"username": data['username']}):
        return jsonify(success=False, message='Username already exists.')

    new_user = {
        'username': data['username'],
        'password': data['password'],
        'role': data['role'],
        'pin': data['pin'],
        'email': data['email'],
        'preferences': {},
        'balance': 10000,
        'transactions': [],
        'alerts': []
    }

    users_col.insert_one(new_user)
    print(f"✅ Registered new user: {data['username']}")
    return jsonify(success=True, message="Registration successful.")


# ✅ MongoDB-based login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")
    device_id = data.get("device_id")  # 👈 Get device_id from request

    user = users_col.find_one({"username": username})
    if user and user["password"] == password and user["role"] == role:
        # 🚫 Check if the device is blocked for this user
        if device_id in user.get("blocked_devices", []) or device_id in user.get("temp_blocked_devices", []):
            return jsonify(success=False, message="This device is currently blocked.")

        # 🔐 Require OTP if previously flagged
        if user.get("require_otp"):
            return jsonify(success=False, require_otp=True, message="OTP verification required due to security event.")

        # ✅ Login successful
        return jsonify(success=True)

    return jsonify(success=False, message="Invalid credentials.")


from flask import request, jsonify
from datetime import datetime

@app.route('/healthz')
def healthz():
    return "ok", 200


@app.route('/request-login-otp', methods=['POST'])
def request_login_otp():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify(success=False, message="Username is required."), 400

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify(success=False, message="User not found."), 404

    email = user.get("email")
    if not email:
        return jsonify(success=False, message="No email associated with this account."), 400

    otp = f"{random.randint(100000, 999999)}"
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

    # Save to MongoDB-based otp_col
    otp_col.update_one(
        {"username": username},
        {"$set": {"otp": otp, "expires_at": expires_at}},
        upsert=True
    )

    try:
        msg = Message(
            subject="Login OTP Verification - Fraud Detection App",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email],
            body=f"Hi {username},\n\nHere is your OTP to verify your login after a suspicious attempt:\n\n🔐 OTP: {otp}\n\nThis OTP will expire in 5 minutes.\n\nIf this wasn't you, please take action immediately.\n\n— Fraud Detection System"
        )
        mail.send(msg)
        print(f"✅ Login OTP sent to {email}")
        return jsonify(success=True, message="OTP sent via email.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return jsonify(success=False, message="Failed to send email."), 500


@app.route('/verify-otp', methods=['POST'])
def verify_otp_login():
    data = request.get_json()
    username = data.get("username")
    submitted_otp = data.get("otp")

    if not username or not submitted_otp:
        return jsonify(success=False, message="Missing username or OTP.")

    # Find the OTP entry
    otp_record = otp_col.find_one({"username": username})

    if not otp_record:
        return jsonify(success=False, message="No OTP found. Please request a new one.")

    # Check if expired
    now = datetime.utcnow()
    try:
        expiry_time = datetime.fromisoformat(otp_record['expires_at'])
    except Exception:
        return jsonify(success=False, message="Invalid OTP format. Please request again.")

    if expiry_time < now:
        return jsonify(success=False, message="OTP expired. Please request a new one.")

    # Check OTP match
    if otp_record['otp'] != submitted_otp:
        return jsonify(success=False, message="Incorrect OTP.")

    # ✅ OTP verified — clear the flag and delete OTP record
    users_col.update_one({"username": username}, {"$unset": {"require_otp": ""}})
    otp_col.delete_one({"username": username})

    return jsonify(success=True, message="OTP verified. Login allowed.")




# ----------------V-02 Edit END-----------------------------

#-------------- V-02 Edit START---------------------------------
@app.route('/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')
    if not username:
        return jsonify(success=False, message="Username not provided"), 400

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify(success=False, message="User not found"), 404

    # Remove top-level _id
    user.pop('_id', None)

    # Remove _id from nested documents like transactions and alerts
    if 'transactions' in user:
        for tx in user['transactions']:
            tx.pop('_id', None)

    if 'alerts' in user:
        for alert in user['alerts']:
            alert.pop('_id', None)

    return jsonify(success=True, profile=user)



@app.route("/users", methods=["GET"])
def get_users():
    users = users_col.find({}, {"_id": 0, "username": 1})
    usernames = [u["username"] for u in users]
    return jsonify({"users": usernames})

# ---------- User Search ----------
@app.route('/search-users', methods=['GET'])
def search_users():
    q = request.args.get('q', '').lower()

    # Fetch usernames from MongoDB
    users_cursor = users_col.find({}, {"username": 1, "_id": 0})
    usernames = [user["username"] for user in users_cursor]

    # Filter usernames that contain the query
    matches = [u for u in usernames if q in u.lower()]

    return jsonify(users=matches)



@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    print("Incoming /predict data:", data)

    # Extract inputs
    sender_raw = data.get('sender_id')
    recipient_raw = data.get('recipient_id')
    amount = float(data.get('amount', 0))
    transaction_type = data.get('transaction_type', 'unknown')
    timestamp = data.get('timestamp')
    device_id = data.get('device_id')
    ip_address = data.get('ip_address')
    geo_lat = data.get('geo_lat', 0.0)
    geo_lon = data.get('geo_lon', 0.0)

    if not sender_raw or not recipient_raw:
        return jsonify(error="Sender and recipient must be provided"), 400

    sender_key = sender_raw.strip().lower()
    recipient_key = recipient_raw.strip().lower()

    sender_user = users_col.find_one({"username": {'$regex': f'^{sender_key}$', '$options': 'i'}})
    recipient_user = users_col.find_one({"username": {'$regex': f'^{recipient_key}$', '$options': 'i'}})

    if not sender_user:
        return jsonify(error="Sender does not exist"), 400
    if not recipient_user:
        return jsonify(error="Recipient does not exist"), 400

    if sender_user['balance'] < amount:
        return jsonify(error="Insufficient balance"), 400

    sender = sender_user["username"]
    recipient = recipient_user["username"]

    if timestamp.endswith("Z"):
        timestamp = timestamp.replace("Z", "+00:00")
    tx_time = datetime.fromisoformat(timestamp)
    now_utc = datetime.now(timezone.utc)

    # --- Derived Features ---
    time_of_day = tx_time.hour + tx_time.minute / 60.0
    day_of_week = tx_time.weekday()

    recent_txs = list(transactions_col.find({"sender": sender}).sort("timestamp", -1).limit(10))
    avg_amount_last_10 = sum(tx['amount'] for tx in recent_txs) / len(recent_txs) if recent_txs else 0.0

    twenty_four_hrs_ago = (now_utc - timedelta(hours=24)).isoformat()
    tx_24h = list(transactions_col.find({"sender": sender, "timestamp": {"$gte": twenty_four_hrs_ago}}))
    txn_count_last_24h = len(tx_24h)

    unique_recipients = set(tx['recipient'] for tx in transactions_col.find({"sender": sender}))
    recipient_diversity = len(unique_recipients)
    is_known_recipient = int(recipient in unique_recipients)

    def haversine(lat1, lon1, lat2, lon2):
        from math import radians, cos, sin, asin, sqrt
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        return R * 2 * asin(sqrt(a))

    past_geo_tx = transactions_col.find_one(
        {"sender": sender, "geo_lat": {"$exists": True}}, sort=[("timestamp", -1)]
    )
    geo_distance_km = 0.0
    if past_geo_tx:
        geo_distance_km = haversine(geo_lat, geo_lon,
                                    past_geo_tx.get("geo_lat", 0.0),
                                    past_geo_tx.get("geo_lon", 0.0))

    last_tx = transactions_col.find_one({"sender": sender}, sort=[("timestamp", -1)])
    ip_change_flag = 0
    if last_tx and isinstance(last_tx.get("ip_address"), str):
        ip_change_flag = int(last_tx["ip_address"] != ip_address)

    device_change_flag = 0
    if last_tx and isinstance(last_tx.get("device_id"), str):
        device_change_flag = int(last_tx["device_id"] != device_id)

    time_since_last_txn = 0.0
    if last_tx and last_tx.get("timestamp"):
        try:
            last_ts = last_tx["timestamp"].replace("Z", "+00:00")
            last_time_utc = datetime.fromisoformat(last_ts)
            time_since_last_txn = (now_utc - last_time_utc).total_seconds() / 3600
        except:
            pass

    rolling_std_amount_10 = pd.Series(
        [tx["amount"] for tx in recent_txs]
    ).std() if len(recent_txs) >= 2 else 0.0

    # --- Model Prediction ---
    features = {
        "amount": amount,
        "time_of_day": time_of_day,
        "day_of_week": day_of_week,
        "transaction_type": transaction_type,
        "avg_amount_last_10": avg_amount_last_10,
        "txn_count_last_24h": txn_count_last_24h,
        "recipient_diversity": recipient_diversity,
        "is_known_recipient": is_known_recipient,
        "geo_distance_km": geo_distance_km,
        "ip_change_flag": ip_change_flag,
        "time_since_last_txn": time_since_last_txn,
        "rolling_std_amount_10": rolling_std_amount_10
    }

    X = pd.DataFrame([features])
    proba = pipeline.predict_proba(X)[0][1]
    is_fraud = int(proba >= 0.3)
    status = "Fraudulent" if is_fraud else "Legitimate"
    tx_id = int(datetime.now().timestamp())
    pin_override = data.get("pin")
    allow_txn = False

    # 🚨 Case: Fraud and incorrect PIN — block and force OTP next login
    if is_fraud and pin_override and pin_override != sender_user.get("pin"):
        print("🚨 Fraud + Incorrect PIN → session terminated, OTP required on next login")
        users_col.update_one({"username": sender}, {"$set": {"require_otp": True}})
        alerts_col.insert_one({
            'id': tx_id,
            'username': sender,
            'amount': amount,
            'transaction_type': transaction_type,
            'status': "Blocked",
            'timestamp': timestamp,
            'details': f"Fraud detected with bad PIN. Probability: {round(proba, 4)}",
            'is_fraud': is_fraud,
            'probability': round(proba, 4)
        })
        return jsonify({
            "is_fraud": is_fraud,
            "probability": round(proba, 4),
            "allowed": False,
            "logout": True,
            "message": "Incorrect PIN. Session terminated. OTP will be required on next login."
        }), 200

    # ✅ Allow transaction if legit or valid override
    if not is_fraud:
        allow_txn = True
    elif amount < 1000 and pin_override == sender_user.get("pin"):
        allow_txn = True

    if not allow_txn:
        print(f"🚫 Blocked TXN: sender={sender}, amount={amount}, probability={proba}")
        
        # Log fraud alert
        alerts_col.insert_one({
            'id': tx_id,
            'username': sender,
            'amount': amount,
            'transaction_type': transaction_type,
            'status': status,
            'timestamp': timestamp,
            'details': f"Fraud risk: {round(proba, 4)}",
            'is_fraud': is_fraud,
            'probability': round(proba, 4)
        })

        # 🚨 Send email if this device isn't blocked yet
        if device_id and device_id not in sender_user.get("blocked_devices", []):
            # 🚫 TEMPORARILY BLOCK DEVICE until user responds
            users_col.update_one(
                {"username": sender},
                {"$addToSet": {"temp_blocked_devices": device_id}}
            )

            try:
                requests.post("http://localhost:5000/send-device-alert", json={
                    "username": sender,
                    "device_id": device_id,
                    "ip_address": ip_address,
                    "geo_lat": geo_lat,
                    "geo_lon": geo_lon
                })
                print(f"📧 Device alert sent for {device_id}")
            except Exception as e:
                print(f"❌ Failed to send device alert: {e}")

        # 🔁 Always return after blocking
        return jsonify({
            "is_fraud": is_fraud,
            "probability": round(proba, 4),
            "allowed": False,
            "message": "Transaction blocked due to fraud risk"
        }), 200


    # ✅ Legitimate transaction: update balances and store transaction
    users_col.update_one({"username": sender}, {"$inc": {"balance": -amount}})
    users_col.update_one({"username": recipient}, {"$inc": {"balance": amount}})

    transactions_col.insert_one({
        'id': tx_id,
        'sender': sender,
        'recipient': recipient,
        'amount': amount,
        'transaction_type': transaction_type,
        'status': status,
        'timestamp': timestamp,
        'geo_lat': geo_lat,
        'geo_lon': geo_lon,
        'device_id': device_id,
        'ip_address': ip_address,
        'is_fraud': is_fraud,
        'probability': round(proba, 4)
    })
    print(f"✅ Transaction inserted: {sender} → {recipient} | ₹{amount} | {status}")

    # Log alert for all transactions
    alerts_col.insert_one({
        'id': tx_id,
        'username': sender,
        'amount': amount,
        'transaction_type': transaction_type,
        'status': status,
        'timestamp': timestamp,
        'details': f"Fraud risk: {round(proba, 4)}",
        'is_fraud': is_fraud,
        'probability': round(proba, 4)
    })

    return jsonify({
        "is_fraud": is_fraud,
        "probability": round(proba, 4),
        "allowed": True
    })


@app.route('/transactions', methods=['GET'])
def get_transactions():
    username = request.args.get('user')
    if not username:
        return jsonify(transactions=[]), 400

    user_txs = list(transactions_col.find({
        "$or": [
            {"sender": username},
            {"recipient": username}
        ]
    }, {"_id": 0}))  # exclude _id

    return jsonify(transactions=user_txs)

@app.route('/alerts', methods=['GET'])
def get_alerts():
    username = request.args.get('username')
    if not username:
        return jsonify(alerts=[]), 400

    user_alerts = list(alerts_col.find({"username": username}, {"_id": 0}))
    return jsonify(alerts=user_alerts)


# ----------------V-02 Edit END-----------------------------

# ---------- OTP & PIN ----------

@app.route('/request-otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    username = data.get('username')
    new_pin = data.get('new_pin')

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify(success=False, message='User not found'), 404

    user_email = user.get('email')
    if not user_email:
        return jsonify(success=False, message='Email not found for user'), 400

    otp = f"{random.randint(100000, 999999)}"
    expires = datetime.now() + timedelta(minutes=5)
    otp_store[username] = {'otp': otp, 'new_pin': new_pin, 'expires_at': expires}

    try:
        msg = Message(
            subject="Your OTP for PIN Change",
            sender=app.config['MAIL_USERNAME'],
            recipients=[user_email],
            body=f"Hi {username},\n\nYour OTP for changing PIN is: {otp}\n\nThis OTP is valid for 5 minutes.\n\n- Fraud Detection App"
        )
        mail.send(msg)
        print(f"✅ OTP sent to {user_email}")
        return jsonify(success=True, message='OTP sent via email')
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return jsonify(success=False, message='Failed to send email'), 500


@app.route('/verify-pin', methods=['POST'])
def verify_otp():
    data = request.get_json()
    username = data.get('username')
    entered = str(data.get('otp'))

    print(f"🔍 Looking up OTP for username: {username}")
    record = otp_store.get(username)
    print(f"🗄️ OTP record found: {record}")

    if not record:
        return jsonify(success=False, error='No OTP requested'), 400

    if datetime.now() > record['expires_at']:
        otp_store.pop(username, None)
        return jsonify(success=False, error='OTP expired'), 400

    if entered != record['otp']:
        print(f"❌ OTP mismatch: entered={entered}, expected={record['otp']}")
        return jsonify(success=False, error='Invalid OTP'), 400

    # Update user PIN in MongoDB
    update_result = users_col.update_one(
        {"username": username},
        {"$set": {"pin": record['new_pin']}}
    )

    otp_store.pop(username, None)

    # Return updated balance
    user = users_col.find_one({"username": username})
    print(f"✅ OTP verified, PIN changed for {username}")
    return jsonify(success=True, message='PIN changed successfully', balance=user['balance'])

@app.route('/log_alert', methods=['POST'])
def log_alert():
    data = request.get_json()

    # Ensure essential fields exist
    required = ['user', 'id', 'amount', 'status', 'timestamp', 'details']
    if not all(k in data for k in required):
        return jsonify(success=False, message="Missing alert fields"), 400

    alert_record = {
        "username": data['user'],
        "id": data['id'],
        "amount": data['amount'],
        "status": data['status'],
        "timestamp": data['timestamp'],
        "details": data['details']
    }

    alerts_col.insert_one(alert_record)
    return jsonify(success=True, message="Alert logged.")


@app.route('/log_transaction', methods=['POST'])
def log_transaction():
    data = request.get_json()

    # Ensure essential fields exist
    required = ['user', 'id', 'sender', 'recipient', 'amount', 'timestamp', 'status']
    if not all(k in data for k in required):
        return jsonify(success=False, message="Missing transaction fields"), 400

    tx_record = {
        "user": data['user'],
        "id": data['id'],
        "sender": data['sender'],
        "recipient": data['recipient'],
        "amount": data['amount'],
        "timestamp": data['timestamp'],
        "status": data['status']
    }

    transactions_col.insert_one(tx_record)
    return jsonify(success=True, message="Transaction logged.")

# ---------- V4 ----------------------

# Setup Flask-Mail

@app.route('/send-device-alert', methods=['POST'])
def send_device_alert():
    data = request.get_json()
    username = data.get("username")
    device_id = data.get("device_id")
    ip_address = data.get("ip_address")
    geo_lat = data.get("geo_lat")
    geo_lon = data.get("geo_lon")

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify(success=False, message="User not found"), 404

    user_email = user.get("email")
    if not user_email:
        return jsonify(success=False, message="User email not set."), 400

    confirm_url = f"http://localhost:5000/confirm-device?username={username}&device_id={device_id}"
    block_url = f"http://localhost:5000/block-device?username={username}&device_id={device_id}&ip={ip_address}&lat={geo_lat}&lon={geo_lon}"

    msg = Message(
        subject="Fraud Alert: Unrecognized Device Attempt",
        sender=app.config['MAIL_USERNAME'],
        recipients=[user_email],
        body=f"""
Hi {username},

A suspicious login or transaction attempt was blocked.

Device ID: {device_id}
IP: {ip_address}
Location: ({geo_lat}, {geo_lon})

✅ If this was you, click here: {confirm_url}
❌ If this was NOT you, click here to block the device: {block_url}

- Fraud Detection System
        """
    )
    mail.send(msg)
    return jsonify(success=True, message="Alert email sent.")

@app.route('/confirm-device')
def confirm_device():
    username = request.args.get("username")
    device_id = request.args.get("device_id")

    if not username or not device_id:
        return "Invalid request. Missing username or device ID.", 400

    # ✅ Remove from both temp and permanent block lists (just in case)
    users_col.update_one(
        {"username": username},
        {
            "$pull": {
                "temp_blocked_devices": device_id,
                "blocked_devices": device_id
            }
        }
    )

    return "✅ Device confirmed and unblocked. You may now log in from this device."


@app.route('/block-device', methods=['GET', 'POST'])
def block_device():
    username = request.args.get("username")
    device_id = request.args.get("device_id")
    ip = request.args.get("ip")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if request.method == 'POST':
        users_col.update_one(
            {"username": username},
            {"$addToSet": {"blocked_devices": device_id}}
        )
        return "🚫 Device has been blocked for your account."

    # Confirmation page (inline HTML)
    html = f"""
        <h2>Block This Device?</h2>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>Device ID:</strong> {device_id}</p>
        <p><strong>IP Address:</strong> {ip}</p>
        <p><strong>Location:</strong> ({lat}, {lon})</p>
        <form method='POST'>
            <button type='submit'>Block This Device</button>
        </form>
    """
    return render_template_string(html)

# Usage in login (pseudo-code reminder):
# - On login, check if device_id in user['blocked_devices'] → if yes, reject login
# - On fraud trigger, call POST to /send-device-alert with username, device_id, ip, lat/lon



@app.route('/')
def index():

    return send_from_directory('../frontend', 'login.html')  # Redirect root to login

@app.route('/<path:filename>')
def serve_page(filename):
    return send_from_directory('../frontend', filename)

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)
