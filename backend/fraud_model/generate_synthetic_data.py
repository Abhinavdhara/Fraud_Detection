import pandas as pd
import numpy as np
import random
from faker import Faker # type: ignore
from datetime import datetime, timedelta

faker = Faker()

# Prepare to collect transaction rows
data = []
num_users = 5000
min_tx, max_tx = 100, 500

# Generate synthetic user profiles
user_ids = list(range(1, num_users+1))
user_profiles = {}
for user_id in user_ids:
    profile = {}
    # Preferred transaction amount (mean and std deviation)
    profile['preferred_amount'] = random.uniform(20, 200)
    profile['amount_std'] = profile['preferred_amount'] * 0.5
    # Active hours window (start to end hour)
    start_hour = random.randint(6, 12)
    end_hour = random.randint(start_hour+4, min(start_hour+12, 22))
    profile['active_start'], profile['active_end'] = start_hour, end_hour
    # A few common recipient IDs for this user
    profile['common_recipients'] = random.sample([uid for uid in user_ids if uid != user_id], 
                                                 k=random.randint(3, 6))
    # Known device IDs for this user
    profile['devices'] = [faker.uuid4() for _ in range(random.randint(1, 2))]
    # Home location (latitude, longitude) in the US for consistency
    lat, lon = faker.local_latlng(country_code='US', coords_only=True)
    profile['home_lat'], profile['home_lon'] = float(lat), float(lon)
    user_profiles[user_id] = profile

# Define possible fraud strategies
fraud_strategies = [
    'high_amount', 'small_burst', 'geo_jump',
    'new_device', 'switch_recipient', 'off_hours'
]

# Simulate transactions for each user
start_date = datetime(2025, 1, 1)
minutes_per_year = 365 * 24 * 60

for user_id in user_ids:
    profile = user_profiles[user_id]
    # Random number of transactions for this user
    num_tx = random.randint(min_tx, max_tx)
    num_fraud = max(1, int(num_tx * 0.10))
    num_legit = num_tx - num_fraud
    strategy = random.choice(fraud_strategies)
    
    # Generate sorted random timestamps for transactions
    if strategy == 'small_burst':
        # Create a cluster for fraud transactions (burst of small transactions)
        cluster_day = random.randint(0, 364)
        cluster_hour = random.randint(0, 23)
        cluster_start = start_date + timedelta(days=cluster_day, hours=cluster_hour)
        cluster_times = [cluster_start + timedelta(minutes=i) for i in range(num_fraud)]
        # Exclude those cluster minutes from the pool
        cluster_minutes = [(cluster_day*1440) + (cluster_hour*60) + i for i in range(num_fraud)]
        available = list(set(range(minutes_per_year)) - set(cluster_minutes))
        chosen = sorted(random.sample(available, num_legit))
        legit_times = [start_date + timedelta(minutes=m) for m in chosen]
        times = sorted(cluster_times + legit_times)
        fraud_set = set(cluster_times)
    else:
        # Pick distinct minutes for all transactions
        chosen = sorted(random.sample(range(minutes_per_year), num_tx))
        times = [start_date + timedelta(minutes=m) for m in chosen]
        # Randomly pick which indices are fraud
        fraud_indices = set(random.sample(range(num_tx), num_fraud))
        fraud_set = set(times[i] for i in fraud_indices)

    # Generate each transaction entry
    seen_recipients = set(profile['common_recipients'])
    for txn_time in times:
        is_fraud = txn_time in fraud_set
        # Pick recipient
        if is_fraud and strategy == 'switch_recipient':
            # Use a new (unknown) recipient
            choices = [uid for uid in user_ids if uid != user_id and uid not in profile['common_recipients']]
            recipient_id = random.choice(choices)
        else:
            if not is_fraud or random.random() < 0.8:
                # Mostly use a known (common) recipient
                recipient_id = random.choice(profile['common_recipients'])
            else:
                # Occasionally pick a random other user
                recipient_id = random.choice([uid for uid in user_ids if uid != user_id])
        # Determine transaction amount
        if is_fraud and strategy == 'high_amount':
            amount = round(profile['preferred_amount'] * random.uniform(3, 6), 2)
        elif is_fraud and strategy == 'small_burst':
            amount = round(random.uniform(1, profile['preferred_amount']*0.2), 2)
        else:
            amount = round(np.random.normal(profile['preferred_amount'], profile['amount_std']), 2)
            amount = max(amount, round(random.uniform(1, profile['preferred_amount']), 2))
        # Transaction type (categorical)
        txn_type = random.choice(['payment', 'transfer', 'purchase', 'withdrawal', 'refund'])
        # Choose device ID
        if is_fraud and strategy == 'new_device':
            device_id = faker.uuid4()
        else:
            device_id = random.choice(profile['devices'])
        # Simulate geographic distance
        if is_fraud and strategy == 'geo_jump':
            geo_distance = round(random.uniform(50, 500), 2)
        else:
            geo_distance = round(abs(np.random.normal(10, 5)), 2)
        # Collect the raw transaction
        data.append({
            'sender_id': user_id,
            'recipient_id': recipient_id,
            'amount': amount,
            'timestamp': txn_time,
            'transaction_type': txn_type,
            'device_id': device_id,
            'geo_distance_km': geo_distance,
            'is_fraud': int(is_fraud)
        })

# Build DataFrame and sort chronologically for each user
df = pd.DataFrame(data)
df.sort_values(['sender_id', 'timestamp'], inplace=True)
df.reset_index(drop=True, inplace=True)

# Add noise: alter 5-10% of legitimate transactions (e.g., use a different device)
for user_id, group in df.groupby('sender_id'):
    legit_idx = group.index[group['is_fraud'] == 0].tolist()
    if not legit_idx:
        continue
    k = max(1, int(len(legit_idx) * random.uniform(0.05, 0.1)))
    noise_indices = random.sample(legit_idx, min(k, len(legit_idx)))
    devices = user_profiles[user_id]['devices']
    for idx in noise_indices:
        current_dev = df.at[idx, 'device_id']
        # Switch to an alternate device or a new device
        if len(devices) > 1:
            new_device = random.choice(devices)
            if new_device == current_dev:
                new_device = devices[0] if current_dev != devices[0] else devices[1]
        else:
            new_device = faker.uuid4()
        df.at[idx, 'device_id'] = new_device

# Compute time-based features
df['time_of_day'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute/60.0
df['day_of_week'] = df['timestamp'].dt.dayofweek

# Compute rolling features per user
df['avg_amount_last_10'] = (df.groupby('sender_id')['amount']
                             .rolling(window=10, min_periods=1)
                             .mean().reset_index(level=0, drop=True))
# Calculate 24-hour transaction count per user
txn_count = (
    df.set_index('timestamp')
      .groupby('sender_id')['amount']
      .rolling('24h')
      .count()
      .reset_index()
      .rename(columns={'amount': 'txn_count_last_24h'})
)

# Merge back with the original DataFrame
df = df.merge(txn_count, on=['sender_id', 'timestamp'], how='left')
df['txn_count_last_24h'] = df['txn_count_last_24h'].fillna(1)

# Fill NaN counts (e.g. first transaction) with 1
df['txn_count_last_24h'] = df['txn_count_last_24h'].fillna(1)

# Compute recipient diversity and known-recipient flag
recipient_diversity = []
is_known_recipient = []
ip_flag = []
for user_id, group in df.groupby('sender_id'):
    seen = set()
    prev_device = None
    for _, row in group.iterrows():
        rec = row['recipient_id']
        known = 1 if rec in seen else 0
        recipient_diversity.append(len(seen) + 1 if known == 0 else len(seen))
        is_known_recipient.append(known)
        # IP change if device differs from previous transaction
        dev = row['device_id']
        if prev_device is None:
            ip_flag.append(0)
        else:
            ip_flag.append(int(dev != prev_device))
        prev_device = dev
        seen.add(rec)

df['recipient_diversity'] = recipient_diversity
df['is_known_recipient'] = is_known_recipient
df['ip_change_flag'] = ip_flag

# Reorder columns as specified
df = df[['sender_id', 'recipient_id', 'amount', 'time_of_day', 'day_of_week',
         'transaction_type', 'avg_amount_last_10', 'txn_count_last_24h',
         'recipient_diversity', 'is_known_recipient',
         'device_id', 'geo_distance_km', 'ip_change_flag',
         'is_fraud', 'timestamp']]

# Save to CSV
df.to_csv('realistic_fraud_dataset.csv', index=False)
