
import json
import pymongo

def main():
    # Load data from aura_points.json
    with open('aura_points.json', 'r') as f:
        aura_points = json.load(f)

    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['your_database_name']
    collection = db['aura_points']

    # Insert data into MongoDB
    for user_id, points in aura_points.items():
        collection.update_one(
            {'user_id': user_id},
            {'$set': {'points': points}},
            upsert=True
        )
    print("Data imported to MongoDB successfully.")

if __name__ == "__main__":
    main()