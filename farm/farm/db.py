"""Database connection module for MongoDB"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId # Moved import to the top for cleanliness

load_dotenv()

class Database:
    """Singleton DB connection - follows all SRS rules"""
    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        """Initialize and return the database connection."""
        if cls._client is None:
            try:
                uri = os.getenv("MONGO_URI")
                db_name = os.getenv("DB_NAME")
                cls._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                cls._client.admin.command('ping')
                cls._db = cls._client[db_name]
                print(f"✅ Connected to MongoDB: {db_name}")
            except ConnectionFailure as e:
                print(f"❌ MongoDB connection failed: {e}")
                raise
        return cls._db

    @classmethod
    def close(cls):
        """Close the database client connection."""
        if cls._client:
            cls._client.close()

# --- USER FUNCTIONS ---

def get_user_by_email(email):
    """REQ-1.2: Fetch a user document from the DB by email."""
    db = Database.get_db()
    return db.users.find_one({"email": email})

def create_user(user_data):
    """Used for customer registration (REQ-6.1)."""
    db = Database.get_db()
    return db.users.insert_one(user_data)

# --- INVENTORY FUNCTIONS ---

def get_all_inventory():
    """Fetch all products from the inventory collection."""
    db = Database.get_db()
    return list(db.inventory.find({}, {"_id": 0}))

def update_inventory_item(name, update_data):
    """Update a specific product in the inventory."""
    db = Database.get_db()
    return db.inventory.update_one({"name": name}, {"$set": update_data})

# --- ORDER FUNCTIONS ---

def create_order(order_data):
    """Saves a new customer order to the orders collection."""
    db = Database.get_db()
    return db.orders.insert_one(order_data)

def get_all_orders():
    """Fetch all customer orders from the database."""
    db = Database.get_db()
    orders = list(db.orders.find())
    for order in orders:
        # Convert _id to string so Reflex can serialize/display it
        order["id"] = str(order.pop("_id")) 
    return orders

def update_order_status(order_id, new_status):
    """Update the status of a specific order using its ID."""
    db = Database.get_db()
    return db.orders.update_one(
        {"_id": ObjectId(order_id)}, 
        {"$set": {"status": new_status}}
    )