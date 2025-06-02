
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import admins_collection

def migrate_admins(json_file='data/admins.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    admins_collection.update_one(
        {'_id': 'admins'},
        {'$set': data},
        upsert=True
    )

if __name__ == "__main__":
    migrate_admins()