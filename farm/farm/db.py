"""Database connection module for MongoDB"""

import os
import bcrypt
import datetime
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId # Moved import to the top for cleanliness

load_dotenv(find_dotenv())

class Database:
    """Singleton DB connection - follows all SRS rules"""
    _client = None
    _db = None

    @classmethod
    def get_db(cls):
        """Initialize and return the database connection."""
        if cls._client is None:
            try:
                # Bypassing .env completely to guarantee connection
                uri = "mongodb://127.0.0.1:27017/"
                db_name = "farm_db"
                cls._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                cls._client.admin.command('ping')
                cls._db = cls._client[db_name]
                print(f"✅ Connected to MongoDB: {db_name}")
            except ConnectionFailure as e:
                print(f"❌ MongoDB connection failed: {e}")
                raise e
        return cls._db
    
    @classmethod
    def verify_user(cls, email: str, password: str) -> dict | None:
        """Verifies user credentials against the database using bcrypt."""
        try:
            db = cls.get_db()
            user = db.users.find_one({"email": email})
            
            if not user:
                return None
                
            # Verify the hashed password
            # Note: Expects the database password to be stored as a bcrypt hash string
            stored_password = user.get("password", "")
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Convert ObjectId to string for Reflex state serialization
                user["_id"] = str(user["_id"])
                return user
                
            return None
        except Exception as e:
            print(f"Login verification error: {e}")
            return None
    
    @classmethod
    def create_user(cls, email: str, password: str, name: str, role: str = "Customer") -> bool:
        """Creates a new user with a hashed password. Returns True if successful, False if email exists."""
        try:
            db = cls.get_db()
            
            # Verificăm dacă emailul este deja folosit
            if db.users.find_one({"email": email}):
                return False
            
            # Generăm salt-ul și criptăm parola
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            # Inserăm noul utilizator în baza de date
            db.users.insert_one({
                "email": email,
                "password": hashed_pw.decode('utf-8'),
                "role": role,
                "name": name
            })
            return True
        except Exception as e:
            print(f"Eroare la crearea contului: {e}")
            return False

    @classmethod
    def close(cls):
        """Close the database client connection."""
        if cls._client:
            cls._client.close()

    @classmethod
    def create_order(cls, cart_items: list, total_price: str) -> bool:
        """REQ-6.2: Inserts a new order into the database."""
        try:
            db = cls.get_db()
            order_doc = {
                "items": cart_items,
                "total": total_price,
                "status": "Pending",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            db.orders.insert_one(order_doc)
            return True
        except Exception as e:
            print(f"❌ Error creating order: {e}")
            return False

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

def delete_order(order_id: str):
    """Deletes an order from the database entirely."""
    db = Database.get_db()
    db.orders.delete_one({"_id": ObjectId(order_id)})

def get_all_orders():
    """Fetch all customer orders from the database."""
    db = Database.get_db()
    orders = list(db.orders.find())
    for order in orders:
        # Convert _id to string so Reflex can serialize/display it
        order["id"] = str(order.pop("_id")) 
    return orders

def update_order_status(order_id: str, new_status: str):
    db = Database.get_db()
    db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": new_status}})

# Add this under your other functions in farm/db.py
def get_all_parcels():
    """Fetch all parcels for graphical reporting."""
    db = Database.get_db()
    parcels = list(db.parcels.find())
    for parcel in parcels:
        parcel["id"] = str(parcel.pop("_id"))
    return parcels

# --- STAFF MANAGEMENT FUNCTIONS ---

def get_all_staff():
    """Fetches all users with the Staff role."""
    db = Database.get_db()
    staff = list(db.users.find({"role": "Staff"}))
    for s in staff:
        s["id"] = str(s.pop("_id"))
    return staff

def delete_user(user_id: str):
    """Deletes a user from the database by their ID."""
    db = Database.get_db()
    # Ensure ObjectId is imported at the top: from bson.objectid import ObjectId
    db.users.delete_one({"_id": ObjectId(user_id)})

# --- PARCELS & CROPS FUNCTIONS ---

def create_crop(name: str, yield_per_ha: str) -> bool:
    """Saves a new crop type to the database."""
    try:
        db = Database.get_db()
        # Prevent duplicate crop names
        if db.crops.find_one({"name": name}):
            return False
        db.crops.insert_one({"name": name, "yield_per_ha": yield_per_ha})
        return True
    except Exception as e:
        print(f"Error creating crop: {e}")
        return False

def get_all_crops() -> list:
    """Fetches all crop types by combining the 'crops' table and the existing 'inventory' table."""
    db = Database.get_db()
    
    combined_crops = []
    seen_names = set()

    # 1. Fetch crops explicitly added via the "+ New Crop Type" button
    for c in db.crops.find():
        name = c.get("name", "Unknown")
        if name not in seen_names:
            c["id"] = str(c.pop("_id"))
            combined_crops.append(c)
            seen_names.add(name)

    # 2. Automatically fetch existing products from the Store Inventory
    for item in db.inventory.find():
        name = item.get("name", "Unknown")
        if name not in seen_names:
            combined_crops.append({
                "id": str(item.get("_id", "auto")), 
                "name": name, 
                "yield_per_ha": "Auto-imported from store"
            })
            seen_names.add(name)

    return combined_crops

def create_parcel(name: str, area: str, crop: str, planting_date: str) -> bool:
    """Saves a new land parcel to the database."""
    try:
        db = Database.get_db()
        db.parcels.insert_one({
            "name": name,
            "area": area,
            "crop": crop,
            "planting_date": planting_date,
            "status": "Planned" # Default status for new parcels
        })
        return True
    except Exception as e:
        print(f"Error creating parcel: {e}")
        return False

def get_all_parcels() -> list:
    """Fetches all land parcels."""
    db = Database.get_db()
    parcels = list(db.parcels.find())
    for p in parcels:
        p["id"] = str(p.pop("_id"))
    return parcels