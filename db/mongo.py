import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017/")
db = client['aura']
shops_collection = db['shops']  # Added shops collection
aura_points_collection = db['aura_points']
servers_collection = db['servers']
role_thresholds_collection = db['role_thresholds']
last_used_collection = db['last_used']
users_collection = db['users']
admins_collection = db['admins']  # Ensure this matches the collection used for admin authorization
custom_commands_collection = db['custom_commands']
authorized_users_collection = db['authorized_users']
aura_data_collection = db['aura_data']
characters_collection = db['characters']  # Ensure characters collection is available