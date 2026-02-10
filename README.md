# FraudShield – Intelligent Financial Transaction Fraud Detection System

FraudShield is a **real-time financial transaction fraud detection system** that combines **machine learning–based behavioral analysis** with **rule-based security controls** to identify and prevent fraudulent activity.

The system is designed to simulate how modern banking fraud engines work by integrating **ML risk scoring**, **user behavior profiling**, **device & location tracking**, and **OTP/PIN-based authentication**.

---

## Problem Statement

Traditional transaction systems approve payments blindly, making them vulnerable to fraud.

FraudShield addresses this by:
- Detecting suspicious transactions in real time
- Analyzing user behavior instead of just transaction amount
- Applying intelligent security actions such as OTP verification or transaction blocking

---

## Key Features

- Real-time fraud detection for financial transactions
- Behavioral feature engineering (time, frequency, volatility, device, location)
- Machine learning–based fraud probability scoring
- Hybrid AI + rule-based decision engine
- OTP and secret PIN verification for suspicious activity
- Device change detection with alerts
- Secure transaction and alert storage using MongoDB
- REST API for model inference
- Admin monitoring and audit logging

---

## Machine Learning Approach

### 🔹 Data Generation
- Synthetic transaction data simulating:
  - Normal users
  - Fraudulent behavior
  - Realistic fraud patterns such as burst transactions and geo jumps

### 🔹 Feature Engineering
Behavioral features are computed dynamically, including:

| Feature | Description |
|------|------------|
| avg_amount_last_10 | User spending pattern |
| txn_count_last_24h | Burst transaction detection |
| time_of_day | Off-hours activity |
| rolling_std_amount_10 | Spending volatility |
| device_change_flag | Device hijack detection |
| geo_distance_km | Location jump detection |
| time_since_last_txn | Automation attacks |
| recipient_diversity | Money mule behavior |

### 🔹 Model Pipeline
- Supervised ML classification using scikit-learn
- Class imbalance handling using SMOTE
- Model serialized using Joblib
- Outputs fraud probability score

**Performance:**
- ROC-AUC: **0.93**
- Accuracy: **97%**

---

## Real-Time Decision Engine

When a transaction is processed:

1. Validate user, balance, and recipient
2. Extract behavioral features
3. Compute fraud probability using ML model
4. Apply business rules:
   - High risk + wrong PIN → Block transaction
   - New device detected → Force OTP verification
   - Low-risk transaction → Allow
5. Log transaction and alerts in MongoDB

This hybrid approach closely mirrors real-world banking fraud systems.

---

## Tech Stack

- **Programming Language:** Python  
- **Machine Learning:** Scikit-learn  
- **Backend:** Flask (REST APIs)  
- **Database:** MongoDB  
- **Security:** OTP verification, PIN authentication, RBAC  
- **Model Serialization:** Joblib  
- **Frontend:** HTML, CSS, JavaScript  

---

## Project Structure
# FraudShield – Financial Transaction Fraud Detection System

FraudShield is a real-time financial transaction fraud detection system that combines machine-learning-based behavioral analytics with rule-based security mechanisms to identify and prevent fraudulent activity. The system simulates modern banking fraud engines by integrating risk scoring, device and location analysis, and OTP/PIN-based verification.

---

## Project Structure


```text
Fraud_Detection/
│
├── app.py                     # Flask backend
├── model/
│   └── fraud_model.pkl        # Trained ML pipeline
├── data/
│   └── synthetic_data.csv     # Generated transaction data
├── templates/                 # HTML frontend
├── static/                    # CSS and JavaScript
├── requirements.txt
└── README.md

```

## Installation and Setup

### 1. Clone the repository

git clone https://github.com/Abhinavdhara/Fraud_Detection.git
cd Fraud_Detection

### 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt
pip install flask scikit-learn pymongo
Run the Application
bash
Copy code
python app.py
Open your browser and navigate to:
http://127.0.0.1:5000

### How the System Works
User initiates a financial transaction
Backend extracts behavioral and contextual features

Machine learning model computes fraud probability

Decision engine applies security and business rules

Transaction is approved, blocked, or sent for OTP verification

Alerts and logs are stored for monitoring and audit

Machine Learning Overview
Supervised classification using scikit-learn

Behavioral feature engineering (transaction frequency, spending volatility, device changes, location jumps)

Class imbalance handled using SMOTE

Model serialized and loaded for real-time inference

Performance on synthetic transaction data:

ROC-AUC: 0.93

Accuracy: 97 percent

Example API Response

{
  "is_fraud": 1,
  "fraud_probability": 0.87
}

### Use Cases
Banking transaction fraud detection

Financial risk scoring systems

Behavioral analytics platforms

Security-focused machine learning applications

Real-time decision engines

Future Enhancements
Time-series modeling for transaction history

Email and SMS-based fraud alerts

Cloud deployment on AWS or Azure

Admin dashboard for fraud analytics

Extension to credit card and UPI fraud detection



### Author
Abhinav Dhara
GitHub: https://github.com/Abhinavdhara
