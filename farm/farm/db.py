"""Database connection module for MongoDB"""

import os
import bcrypt
import json
import datetime
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId # Moved import to the top for cleanliness
from pymongo.errors import PyMongoError

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
    def verify_user(cls, email: str, password: str) -> dict | str | None:
        """REQ-1.3: Verifies user with a 3-strike temporary lockout system."""
        import datetime
        try:
            db = cls.get_db()
            user = db.users.find_one({"email": email})
            
            if not user:
                return None
                
            # 1. Check if the account is currently locked out
            if user.get("lockout_until"):
                if datetime.datetime.now() < user["lockout_until"]:
                    return "LOCKED" # Signal the frontend that it's blocked
                else:
                    # Time has passed, reset the lock
                    db.users.update_one({"email": email}, {"$set": {"failed_attempts": 0, "lockout_until": None}})

            # 2. Verify Password
            stored_password = user.get("password", "")
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Success! Reset failed attempts
                db.users.update_one({"email": email}, {"$set": {"failed_attempts": 0, "lockout_until": None}})
                user["_id"] = str(user["_id"])
                return user
            else:
                # 3. Failed Attempt Logic
                attempts = user.get("failed_attempts", 0) + 1
                update_data = {"failed_attempts": attempts}
                
                if attempts >= 3:
                    # Lock the account for 15 minutes
                    update_data["lockout_until"] = datetime.datetime.now() + datetime.timedelta(minutes=15)
                    
                db.users.update_one({"email": email}, {"$set": update_data})
                return "WRONG_PASSWORD"
                
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
    def create_order(cls, cart_items: list, total_price: float) -> bool:
        """REQ-6.2: Inserts a new order into the database."""
        try:
            db = cls.get_db()
            order_doc = {
                "items": cart_items,
                "total": round(total_price, 2), # REQ-6.6: Stores exact cumulative price
                "status": "Created",
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
    """REQ-2.4: Fetch all parcels and auto-update status based on planting date."""
    import datetime
    db = Database.get_db()
    parcels = list(db.parcels.find())
    
    # Gets today's date in 'YYYY-MM-DD' format (reads from your PC clock!)
    today = datetime.date.today().isoformat() 

    print(f"🕒 [SYSTEM TIME] Python thinks today is: {today}")

    for parcel in parcels:
        parcel_id = parcel["_id"]
        current_status = str(parcel.get("status", ""))
        p_date = str(parcel.get("planting_date", "None"))

        # Time-based transitions logic
        if current_status not in ["Available", "Harvested"] and p_date != "None":
            # If today is past or equal to planting date -> In Production. Otherwise -> Planned.
            new_status = "In Production" if today >= p_date else "Planned"

            print(f"📦 Checking '{parcel.get('name')}': Planted {p_date} -> Status: {new_status}")
            
            # If the status just shifted, update the database permanently
            if current_status != new_status:
                db.parcels.update_one({"_id": parcel_id}, {"$set": {"status": new_status}})
                parcel["status"] = new_status

        parcel["id"] = str(parcel.pop("_id"))
        parcel["active"] = "true" if parcel.get("active", True) else "false"
        
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

def create_crop(name: str, yield_per_ha: str, growth_duration: str, planting_season: str, resources: str) -> bool:
    """Saves a new crop type to the database (Updated with REQ-3.3, 3.4, 3.8)."""
    try:
        db = Database.get_db()
        if db.crops.find_one({"name": name}):
            return False
        db.crops.insert_one({
            "name": name, 
            "yield_per_ha": yield_per_ha,          # REQ-3.5 (Already existed)
            "growth_duration": growth_duration,    # REQ-3.3
            "planting_season": planting_season,    # REQ-3.4
            "resources": resources                 # REQ-3.8
        })
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
            c["active"] = "true" if c.get("active", True) else "false"
            combined_crops.append(c)
            seen_names.add(name)

    # 2. Automatically fetch existing products from the Store Inventory
    for item in db.inventory.find():
        name = item.get("name", "Unknown")
        if name not in seen_names:
            combined_crops.append({
                "id": str(item.get("_id", "auto")), 
                "name": name, 
                "yield_per_ha": "Auto-imported from store",
                "active": "true" if item.get("active", True) else "false"
            })
            seen_names.add(name)

    return combined_crops

# Note the added latitude and longitude in the arguments here!
def create_parcel(name: str, area: str, crop: str, planting_date: str, lat: str, lng: str, x: int, y: int, w: int, h: int, soil_type: str, irrigation: bool) -> bool:
    """Saves a new land parcel to the database (Updated with REQ-2.2 & 2.3)."""
    try:
        db = Database.get_db()
        status = "Available" if crop == "None" or not crop else "Planned"
        
        db.parcels.insert_one({
            "name": name,
            "area": area,
            "crop": crop,
            "planting_date": planting_date,
            "status": status,
            "latitude": lat,
            "longitude": lng,
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "soil_type": soil_type,      # REQ-2.2
            "irrigation": irrigation     # REQ-2.3
        })
        return True
    except Exception as e:
        print(f"Error creating parcel: {e}")
        return False



def harvest_parcel(parcel_id: str, actual_yield: float, quality_notes: str, user_name: str) -> bool:
    """Feature 4: Production Cycle Tracking with Smart Inventory Matching"""
    try:
        db = Database.get_db()
        
        parcel = db.parcels.find_one({"_id": ObjectId(parcel_id)})
        if not parcel:
            return False
            
        crop_name = str(parcel.get("crop", "Unknown")).strip()
        
        # Prevenim crearea produsului "none"
        if not crop_name or crop_name.lower() == "none" or crop_name == "Unknown":
            print("Cannot harvest an empty or None parcel.")
            return False 
            
        # 1. Eliberăm parcela (REQ-4.6)
        db.parcels.update_one(
            {"_id": ObjectId(parcel_id)},
            {"$set": {"status": "Available", "crop": "None", "planting_date": "None"}}
        )
        
        # 2. Salvăm istoricul de producție
        harvest_date = datetime.datetime.now().strftime("%Y-%m-%d")
        db.production_records.insert_one({
            "parcel_name": parcel.get("name", "Unknown"),
            "crop": crop_name,
            "planting_date": parcel.get("planting_date", "Unknown"),
            "harvest_date": harvest_date,
            "actual_yield": float(actual_yield),
            "quality_notes": quality_notes,
            "modified_by": user_name 
        })
        
        # 3. SMART MATCHING pentru Magazin
        inventory_items = list(db.inventory.find())
        matched_item = None
        
        for item in inventory_items:
            inv_name = str(item.get("name", "")).lower()
            c_name = crop_name.lower()
            
            # Verificăm dacă "Tomatoes" e în "Fresh Tomatoes" sau invers
            if c_name in inv_name or inv_name in c_name:
                matched_item = item
                break
                
        if matched_item:
            # Produs găsit! Adăugăm cantitatea la stocul curent
            new_stock = float(matched_item.get("stock", 0)) + float(actual_yield)
            db.inventory.update_one(
                {"_id": matched_item["_id"]}, 
                {"$set": {"stock": new_stock}}
            )
        else:
            # Creăm un produs nou DOAR dacă nu există nimic similar
            db.inventory.insert_one({
                "name": crop_name, 
                "stock": float(actual_yield), 
                "price": 0, 
                "unit": "kg"
            })
            
        return True
    except Exception as e:
        print(f"Error harvesting parcel: {e}")
        return False
    
def get_all_production_records() -> list:
    """Feature 9: Fetches all production history records."""
    try:
        db = Database.get_db()
        records = list(db.production_records.find())
        for r in records:
            r["id"] = str(r.pop("_id"))
        return records
    except Exception as e:
        print(f"Error fetching production records: {e}")
        return []


def export_full_database() -> str:
    """REQ-10.1, 10.2: Exports complete configuration and records."""
    try:
        db = Database.get_db()
        # We exclude '_id' because MongoDB generates new ones automatically 
        # and we don't want conflicts when importing.
        backup_data = {
            "parcels": list(db.parcels.find({}, {"_id": 0})),
            "crops": list(db.crop_types.find({}, {"_id": 0})) if "crop_types" in db.list_collection_names() else [],
            "inventory": list(db.inventory.find({}, {"_id": 0})),
            "production_records": list(db.production_records.find({}, {"_id": 0})),
            "orders": list(db.orders.find({}, {"_id": 0}))
        }
        # Format as a pretty JSON string
        return json.dumps(backup_data, indent=4)
    except Exception as e:
        print(f"Export error: {e}")
        return ""

def restore_database(json_string: str) -> bool:
    """REQ-10.6, 10.7: Import and validate the backup file."""
    try:
        data = json.loads(json_string)
        
        # REQ-10.7: File Validation. Ensure the file has the correct structure.
        if not isinstance(data, dict) or "parcels" not in data or "production_records" not in data:
            print("Validation failed: Missing required core collections.")
            return False
            
        db = Database.get_db()
        
        # Danger Zone: Clear existing data before restoring
        # We DO NOT clear the 'users' table so admins don't lock themselves out!
        for collection_name in ["parcels", "crop_types", "inventory", "production_records", "orders"]:
            if collection_name in data and isinstance(data[collection_name], list):
                db[collection_name].delete_many({}) # Wipe current data
                if data[collection_name]:           # If backup has data, insert it
                    db[collection_name].insert_many(data[collection_name])
                    
        return True
    except json.JSONDecodeError:
        print("Validation failed: Not a valid JSON file.")
        return False
    except Exception as e:
        print(f"Restore error: {e}")
        return False
    
def is_overlapping(rect1: dict, rect2: dict) -> bool:
    """Mathematical check if two rectangles overlap on a grid."""
    # We assume each dict has x, y, width, and height
    return (
        rect1.get('x', 0) < rect2.get('x', 0) + rect2.get('width', 0) and
        rect1.get('x', 0) + rect1.get('width', 0) > rect2.get('x', 0) and
        rect1.get('y', 0) < rect2.get('y', 0) + rect2.get('height', 0) and
        rect1.get('y', 0) + rect1.get('height', 0) > rect2.get('y', 0)
    )

def expand_parcel(parcel_id: str, new_width: int, new_height: int) -> tuple[bool, str]:
    """Attempts to expand a parcel, returns (Success, Message)."""
    try:
        db = Database.get_db()
        
        # 1. Get the parcel we want to expand
        target = db.parcels.find_one({"_id": ObjectId(parcel_id)})
        if not target:
            return False, "Parcel not found."
            
        # Create a temporary dictionary of what the parcel WOULD look like
        proposed_shape = {
            "x": target.get("x", 0),
            "y": target.get("y", 0),
            "width": new_width,
            "height": new_height
        }
        
        # 2. Get all OTHER parcels
        other_parcels = list(db.parcels.find({"_id": {"$ne": ObjectId(parcel_id)}}))
        
        # 3. Check for collisions
        for other in other_parcels:
            if is_overlapping(proposed_shape, other):
                return False, f"You can't expand this parcel, it would overlap with {other.get('name', 'another parcel')}!"
                
        # 4. If no overlaps, save the new size!
        db.parcels.update_one(
            {"_id": ObjectId(parcel_id)},
            {"$set": {"width": new_width, "height": new_height}}
        )
        return True, "Parcel expanded successfully!"
        
    except Exception as e:
        print(f"Expansion error: {e}")
        return False, "Database error during expansion."
    
def update_parcel(parcel_id: str, name: str, area: str, lat: str, lng: str, x: int, y: int, w: int, h: int, soil_type: str, irrigation: bool) -> bool:
    """Updates an existing parcel's details and coordinates."""
    try:
        db = Database.get_db()
        db.parcels.update_one(
            {"_id": ObjectId(parcel_id)},
            {"$set": {
                "name": name,
                "area": area,
                "latitude": lat,
                "longitude": lng,
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "soil_type": soil_type,      # REQ-2.2
                "irrigation": irrigation     # REQ-2.3
            }}
        )
        return True
    except Exception as e:
        print(f"Error updating parcel: {e}")
        return False
    
def cancel_customer_order(order_id: str) -> bool:
    """REQ-7.7: Allows a customer to reject and cancel their order."""
    try:
        db = Database.get_db()
        # We ONLY allow cancellation if the status is "Created"
        # If staff has started processing it, they must call the farm.
        result = db.orders.update_one(
            {"_id": ObjectId(order_id), "status": "Created"}, 
            {"$set": {"status": "Cancelled"}}
        )
        # Returns True if an order was actually updated
        return result.modified_count > 0
    except Exception as e:
        print(f"Cancel error: {e}")
        return False
    
def toggle_crop_status(crop_id: str, new_status: bool) -> bool:
    """REQ-3.6: Activate or deactivate a crop type."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        
        # 1. Try updating in the explicit crops table
        result = db.crops.update_one({"_id": ObjectId(crop_id)}, {"$set": {"active": new_status}})
        
        # 2. If it wasn't found, it must be an auto-imported inventory item!
        if result.matched_count == 0:
            db.inventory.update_one({"_id": ObjectId(crop_id)}, {"$set": {"active": new_status}})
            
        return True
    except Exception as e:
        print(f"Error toggling crop: {e}")
        return False

def toggle_parcel_status(parcel_id: str, new_status: bool) -> bool:
    """REQ-2.1: Activate or deactivate a parcel."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.parcels.update_one({"_id": ObjectId(parcel_id)}, {"$set": {"active": new_status}})
        return True
    except Exception as e:
        print(f"Error toggling parcel: {e}")
        return False
    
def delete_parcel(parcel_id: str) -> bool:
    """REQ-2.8: Deletes a parcel entirely from the database."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.parcels.delete_one({"_id": ObjectId(parcel_id)})
        return True
    except Exception as e:
        print(f"Error deleting parcel: {e}")
        return False