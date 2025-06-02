
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import custom_commands_collection

def migrate_custom_commands(json_file='custom_commands.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    custom_commands_collection.update_one(
        {'_id': 'custom_commands'},
        {'$set': data},
        upsert=True
    )

if __name__ == "__main__":
    migrate_custom_commands()