import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import aura_points_collection

def migrate_aura_points(json_file='aura_points.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for user_id, points in data.items():
        aura_points_collection.update_one(
            {'user_id': user_id},
            {'$set': {'points': points}},
            upsert=True
        )

if __name__ == "__main__":
    migrate_aura_points()