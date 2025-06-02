
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import aura_data_collection

def migrate_aura_data(json_file='aura_data.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for user_id, details in data.items():
        aura_data_collection.update_one(
            {'user_id': user_id},
            {'$set': details},
            upsert=True
        )

if __name__ == "__main__":
    migrate_aura_data()