
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import servers_collection

def migrate_servers(json_file='servers.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    for server_id, details in data.items():
        servers_collection.update_one(
            {'server_id': server_id},
            {'$set': details},
            upsert=True
        )

if __name__ == "__main__":
    migrate_servers()