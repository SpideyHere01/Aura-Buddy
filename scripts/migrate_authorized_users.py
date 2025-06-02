
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import authorized_users_collection

def migrate_authorized_users(json_file='authorized_users.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    authorized_users_collection.update_one(
        {'_id': 'authorized_users'},
        {'$set': data},
        upsert=True
    )

if __name__ == "__main__":
    migrate_authorized_users()