
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import role_thresholds_collection

def migrate_role_thresholds(json_file='role_thresholds.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for guild_id, roles in data.items():
        role_thresholds_collection.update_one(
            {'guild_id': guild_id},
            {'$set': {'roles': roles}},
            upsert=True
        )

if __name__ == "__main__":
    migrate_role_thresholds()