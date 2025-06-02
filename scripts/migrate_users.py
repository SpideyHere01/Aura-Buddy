
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import users_collection

def migrate_users(json_file='data/users.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for user_id, details in data['users'].items():
        users_collection.update_one(
            {'user_id': user_id},
            {'$set': details},
            upsert=True
        )

if __name__ == "__main__":
    migrate_users()