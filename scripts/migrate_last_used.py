
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import last_used_collection

def migrate_last_used(json_file='last_used.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for user_id, timestamp in data.items():
        last_used_collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_used': timestamp}},
            upsert=True
        )

if __name__ == "__main__":
    migrate_last_used()