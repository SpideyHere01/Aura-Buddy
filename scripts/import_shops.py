import json
import asyncio
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import shops_collection  # Adjust the import path if necessary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def import_shops():
    try:
        with open('shop/shops.json', 'r') as f:
            shops_data = json.load(f)
        
        # Clear existing shops in the collection
        await shops_collection.delete_many({})
        
        # Prepare data for insertion
        shops = []
        for guild_id, items in shops_data.items():
            shops.append({
                "_id": guild_id,
                "items": items
            })
        
        if shops:
            await shops_collection.insert_many(shops)
            logging.info("Shops data imported successfully to MongoDB.")
        else:
            logging.warning("No shops data found to import.")
            
    except FileNotFoundError:
        logging.error("shops.json file not found.")
    except json.JSONDecodeError:
        logging.error("Error decoding shops.json.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

asyncio.run(import_shops())