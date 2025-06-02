
import json
import asyncio
import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo import aura_points_collection  # Adjust the import path if necessary

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def import_aura_points():
    try:
        with open('aura_points.json', 'r') as f:
            aura_points_data = json.load(f)
        
        # Clear existing aura points in the collection
        await aura_points_collection.delete_many({})
        
        # Prepare data for insertion
        aura_points = []
        for user_id, points in aura_points_data.items():
            aura_points.append({
                "_id": str(user_id),
                "points": points
            })
        
        if aura_points:
            await aura_points_collection.insert_many(aura_points)
            logging.info("Aura points data imported successfully to MongoDB.")
        else:
            logging.warning("No aura points data found to import.")
            
    except FileNotFoundError:
        logging.error("aura_points.json file not found.")
    except json.JSONDecodeError:
        logging.error("Error decoding aura_points.json.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

asyncio.run(import_aura_points())