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
    def create_order(cls, cart_items: list, total_price: float, customer_email: str) -> bool:
        """REQ-6.2: Inserts a new order into the database."""
        import datetime
        try:
            db = cls.get_db()
            order_doc = {
                "customer_email": customer_email, # NEW: Links the order to the user!
                "items": cart_items,
                "total": round(total_price, 2), 
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

def get_season(month: int) -> str:
    """Helper to map a calendar month to a meteorological season."""
    if month in [3, 4, 5]: return "spring"
    if month in [6, 7, 8]: return "summer"
    if month in [9, 10, 11]: return "autumn"
    return "winter"

# Add this under your other functions in farm/db.py
def get_all_parcels():
    """REQ-2.4 & REQ-2.10: Fetch parcels, auto-update status with strict season validation, and repair coordinates."""
    import datetime
    db = Database.get_db()
    parcels = list(db.parcels.find())
    
    today_obj = datetime.date.today()
    today = today_obj.isoformat() 
    current_season = get_season(today_obj.month)

    print(f"🕒 [SYSTEM TIME] Today is: {today} | Season: {current_season.upper()}")

    # Build a quick lookup dictionary of { "Crop Name" : "Season String" }
    crop_seasons = {c["name"]: str(c.get("planting_season", "")).lower() for c in db.crops.find()}

    for parcel in parcels:
        parcel_id = parcel["_id"]
        current_status = str(parcel.get("status", ""))
        p_date = str(parcel.get("planting_date", "None"))
        crop_name = str(parcel.get("crop", "Unknown"))

        # --- REQ-2.10: Complex Season Validation ---
        if current_status == "Planned" and p_date != "None" and today >= p_date:
            c_season = crop_seasons.get(crop_name, "")
            
            is_match = True
            if c_season: # Only validate if the crop actually has a defined season
                match_words = [current_season]
                if current_season == "autumn": match_words.append("fall") # Catch synonyms
                
                # Check if the current season is mentioned anywhere in the crop's string
                is_match = any(word in c_season for word in match_words)
            
            if is_match:
                new_status = "In Production"
                db.parcels.update_one({"_id": parcel_id}, {"$set": {"status": new_status}})
                parcel["status"] = new_status
            else:
                # BLOCK ACTIVATED! The DB stays "Planned", but we warn the UI.
                print(f"⚠️ [REQ-2.10] Blocked '{parcel.get('name')}'. {current_season.upper()} does not match '{c_season}'.")
                parcel["status"] = "Season Locked"

        # --- Spatial Geometry Repair ---
        needs_repair = False
        updates = {}
        for coord in ["x", "y"]:
            if coord not in parcel:
                parcel[coord], updates[coord], needs_repair = 0, 0, True
        for dim in ["width", "height"]:
            if dim not in parcel:
                parcel[dim], updates[dim], needs_repair = 10, 10, True
                
        if needs_repair:
            db.parcels.update_one({"_id": parcel_id}, {"$set": updates})

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

def create_parcel(name: str, area: str, crop: str, planting_date: str, lat: str, lng: str, x: float, y: float, w: float, h: float, soil_type: str, irrigation: bool, coordinates: list = None) -> tuple[bool, str]:
    """Saves a new land parcel with advanced Polygon collision detection."""
    try:
        db = Database.get_db()
        
        # 1. Define the proposed shape (Handles both rectangles and custom polygons)
        proposed_parcel = {"x": float(x), "y": float(y), "width": float(w), "height": float(h), "coordinates": coordinates}
        proposed_poly = get_polygon(proposed_parcel)
        
        # 2. Check for collisions against all existing parcels
        existing_parcels = list(db.parcels.find())
        for other in existing_parcels:
            other_poly = get_polygon(other)
            if polygons_overlap(proposed_poly, other_poly):
                return False, f"Collision detected! Space occupied by '{other.get('name', 'another parcel')}'."

        # 3. If no overlap, proceed with creation
        status = "Available" if crop == "None" or not crop else "Planned"
        db.parcels.insert_one({
            "name": name, "area": area, "crop": crop, "planting_date": planting_date,
            "status": status, "latitude": lat, "longitude": lng,
            "x": float(x), "y": float(y), "width": float(w), "height": float(h),
            "coordinates": coordinates, # NEW: Save custom shape geometry
            "soil_type": soil_type, "irrigation": irrigation
        })
        return True, "Parcel created successfully!"
    except Exception as e:
        print(f"Error creating parcel: {e}")
        return False, "Database error while adding parcel."


def harvest_parcel(parcel_id: str, actual_yield: float, quality_notes: str, user_name: str) -> bool:
    """Feature 4: Production Tracking with Expected Yield & Fingerprinting."""
    import re
    try:
        db = Database.get_db()
        
        parcel = db.parcels.find_one({"_id": ObjectId(parcel_id)})
        if not parcel:
            return False
            
        # --- NEW SECURITY BLOCK ---
        if parcel.get("status") != "In Production":
            print(f"⚠️ Security Block: Attempted to harvest parcel while status is '{parcel.get('status')}'.")
            return False

        crop_name = str(parcel.get("crop", "Unknown")).strip()
        if not crop_name or crop_name.lower() == "none" or crop_name == "Unknown":
            return False 

        # --- REQ-4.7: Calculate Expected Yield ---
        # 1. Extract the raw number from area (e.g., "2.5 ha" -> 2.5)
        area_match = re.search(r"(\d+(\.\d+)?)", str(parcel.get("area", "0")))
        area_val = float(area_match.group(1)) if area_match else 0.0
        
        # 2. Get the crop's yield per hectare from the DB
        crop_doc = db.crops.find_one({"name": crop_name})
        expected_yield = 0.0
        if crop_doc:
            yield_match = re.search(r"(\d+(\.\d+)?)", str(crop_doc.get("yield_per_ha", "0")))
            if yield_match:
                expected_yield = float(yield_match.group(1)) * area_val

        # 1. Free up parcel (REQ-4.6)
        db.parcels.update_one(
            {"_id": ObjectId(parcel_id)},
            {"$set": {"status": "Available", "crop": "None", "planting_date": "None"}}
        )
        
        # 2. Save Production History (REQ-4.5, 4.7, 4.8)
        harvest_date = datetime.datetime.now().strftime("%Y-%m-%d")
        db.production_records.insert_one({
            "parcel_name": parcel.get("name", "Unknown"),
            "crop": crop_name,
            "planting_date": parcel.get("planting_date", "Unknown"),
            "harvest_date": harvest_date,             # REQ-4.5
            "expected_yield": expected_yield,         # REQ-4.7: The calculated math
            "actual_yield": float(actual_yield),
            "quality_notes": quality_notes,
            "modified_by": user_name                  # REQ-4.8: The User Fingerprint
        })
        
        # 3. SMART MATCHING pentru Magazin
        inventory_items = list(db.inventory.find())
        matched_item = None
        for item in inventory_items:
            inv_name = str(item.get("name", "")).lower()
            c_name = crop_name.lower()
            if c_name in inv_name or inv_name in c_name:
                matched_item = item
                break
                
        if matched_item:
            new_stock = float(matched_item.get("stock", 0)) + float(actual_yield)
            # REQ-4.9: Update stock, and force status back to Pending QA since it's a fresh batch
            db.inventory.update_one(
                {"_id": matched_item["_id"]}, 
                {"$set": {
                    "stock": new_stock, 
                    "status": "Pending QA",
                    "location": matched_item.get("location", "Receiving Bay")
                }}
            )
        else:
            # REQ-4.9: Create new inventory item with location and status tracking
            db.inventory.insert_one({
                "name": crop_name, 
                "stock": float(actual_yield), 
                "price": 0, 
                "unit": "kg",
                "location": "Receiving Bay",  # Default warehouse location
                "status": "Pending QA"        # Default inspection status
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
    
# --- ADVANCED GEOMETRY ENGINE (Supports Rectangles & Custom Polygons) ---

def get_polygon(parcel_data: dict) -> list:
    """Converts any parcel into a standard list of point coordinates."""
    if "coordinates" in parcel_data and parcel_data["coordinates"]:
        return parcel_data["coordinates"]
    
    # Safely convert old legacy parcels to avoid ValueError crashes
    try:
        x = float(parcel_data.get("x") or 0)
        y = float(parcel_data.get("y") or 0)
        w = float(parcel_data.get("width") or 10)
        h = float(parcel_data.get("height") or 10)
    except (ValueError, TypeError):
        x, y, w, h = 0.0, 0.0, 10.0, 10.0
        
    return [
        {"x": x, "y": y}, 
        {"x": x + w, "y": y}, 
        {"x": x + w, "y": y + h}, 
        {"x": x, "y": y + h}
    ]

def is_point_in_polygon(point: dict, polygon: list) -> bool:
    """Ray-casting algorithm to mathematically check if a point is inside a polygon."""
    if not polygon or len(polygon) < 3: return False
    
    x, y = point['x'], point['y']
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0]['x'], polygon[0]['y']
    
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]['x'], polygon[i % n]['y']
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y: # Avoid division by zero on horizontal lines
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        # FIX: This check must be indented inside the p1y != p2y block!
                        if p1x == p2x or x <= xinters:
                            inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def _ccw(A, B, C):
    """Helper for edge intersection."""
    return (C['y'] - A['y']) * (B['x'] - A['x']) > (B['y'] - A['y']) * (C['x'] - A['x'])

def _segments_intersect(A, B, C, D):
    """Checks if two lines cross each other."""
    return _ccw(A, C, D) != _ccw(B, C, D) and _ccw(A, B, C) != _ccw(A, B, D)

def polygons_overlap(poly1: list, poly2: list) -> bool:
    """Checks if two shapes overlap using point-in-polygon and edge intersection."""
    # 1. Check if any point of shape 1 is inside shape 2
    for p in poly1:
        if is_point_in_polygon(p, poly2): return True
    # 2. Check if any point of shape 2 is inside shape 1
    for p in poly2:
        if is_point_in_polygon(p, poly1): return True
    # 3. Check if any boundaries cross
    for i in range(len(poly1)):
        for j in range(len(poly2)):
            if _segments_intersect(poly1[i], poly1[(i+1)%len(poly1)], poly2[j], poly2[(j+1)%len(poly2)]):
                return True
    return False

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
    
def update_parcel(parcel_id: str, name: str, area: str, lat: str, lng: str, x: float, y: float, w: float, h: float, soil_type: str, irrigation: bool, crop: str, planting_date: str, coordinates: list = None) -> tuple[bool, str]:
    """Updates a parcel with advanced Polygon collision detection."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        
        existing_parcel = db.parcels.find_one({"_id": ObjectId(parcel_id)})
        if not existing_parcel:
            return False, "Parcel not found."
            
        current_status = existing_parcel.get("status", "Available")
        
        if current_status == "In Production":
            if crop != existing_parcel.get("crop") or planting_date != existing_parcel.get("planting_date"):
                return False, "Security Block: Cannot modify crop or date while In Production!"
            new_status = "In Production"
        else:
            new_status = "Available" if crop == "None" or not crop else "Planned"

        # Geometry Checks
        proposed_parcel = {"x": float(x), "y": float(y), "width": float(w), "height": float(h), "coordinates": coordinates}
        proposed_poly = get_polygon(proposed_parcel)
        other_parcels = list(db.parcels.find({"_id": {"$ne": ObjectId(parcel_id)}}))
        
        for other in other_parcels:
            other_poly = get_polygon(other)
            if polygons_overlap(proposed_poly, other_poly):
                return False, f"Collision detected! Overlaps with '{other.get('name', 'another parcel')}'."

        db.parcels.update_one(
            {"_id": ObjectId(parcel_id)},
            {"$set": {
                "name": name, "area": area, "latitude": lat, "longitude": lng,
                "x": float(x), "y": float(y), "width": float(w), "height": float(h),
                "coordinates": coordinates, # NEW: Save custom shape geometry
                "soil_type": soil_type, "irrigation": irrigation,
                "crop": crop, "planting_date": planting_date,
                "status": new_status                          
            }}
        )
        return True, f"Parcel '{name}' updated successfully!"
    except Exception as e:
        print(f"Error updating parcel: {e}")
        return False, "Database error during update."
    
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
    
    # --- TASK MANAGEMENT FUNCTIONS ---
def get_all_tasks() -> list:
    """Fetches all daily tasks."""
    db = Database.get_db()
    tasks = list(db.tasks.find())
    for t in tasks:
        t["id"] = str(t.pop("_id"))
    return tasks

def create_task(time: str, task: str, parcel: str, priority: str) -> bool:
    """Creates a new daily task."""
    try:
        db = Database.get_db()
        db.tasks.insert_one({
            "time": time,
            "task": task,
            "parcel": parcel,
            "priority": priority,
            "status": "Pending"
        })
        return True
    except Exception as e:
        print(f"Error creating task: {e}")
        return False

def update_task_details(task_id: str, time: str, task: str, parcel: str, priority: str) -> bool:
    """Updates an existing task's core details."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"time": time, "task": task, "parcel": parcel, "priority": priority}}
        )
        return True
    except Exception:
        return False

def update_task_status(task_id: str, new_status: str) -> bool:
    """Updates just the status of a task."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": new_status}}
        )
        return True
    except Exception:
        return False
        
def update_task_priority(task_id: str, new_priority: str) -> bool:
    """Updates just the priority of a task."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"priority": new_priority}}
        )
        return True
    except Exception:
        return False

def delete_task(task_id: str) -> bool:
    """Removes a task completely."""
    try:
        from bson.objectid import ObjectId
        db = Database.get_db()
        db.tasks.delete_one({"_id": ObjectId(task_id)})
        return True
    except Exception:
        return False
    


    # --- REPORTING & ANALYTICS FUNCTIONS ---
def get_production_vs_orders_report() -> list:
    """Aggregates total produced quantities vs total ordered quantities per crop."""
    try:
        db = Database.get_db()

        # 1. Total Production per Crop
        production_records = list(db.production_records.find())
        production_totals = {}
        for rec in production_records:
            crop = str(rec.get("crop", "Unknown")).strip()
            yield_val = float(rec.get("actual_yield", 0.0))
            production_totals[crop] = production_totals.get(crop, 0.0) + yield_val

        # 2. Total Orders per Crop
        orders = list(db.orders.find({"status": {"$ne": "Cancelled"}}))
        order_totals = {}
        for order in orders:
            for item in order.get("items", []):
                crop = str(item.get("name", "Unknown")).strip()
                qty = float(item.get("quantity", 0.0))
                order_totals[crop] = order_totals.get(crop, 0.0) + qty

        # 3. Combine Data
        all_crops = set(list(production_totals.keys()) + list(order_totals.keys()))
        report_data = []
        for crop in all_crops:
            if crop.lower() in ["none", "unknown"]: 
                continue
            prod = production_totals.get(crop, 0.0)
            ordered = order_totals.get(crop, 0.0)
            report_data.append({
                "crop": crop,
                "produced": round(prod, 2),
                "ordered": round(ordered, 2),
                "surplus": round(prod - ordered, 2)
            })

        return sorted(report_data, key=lambda x: x["crop"])
    except Exception as e:
        print(f"Error generating report: {e}")
        return []
    

def get_orders_by_user(email: str):
    """Fetches order history for a specific customer."""
    db = Database.get_db()
    # Find orders where the customer_email matches
    orders = list(db.orders.find({"customer_email": email}))
    for order in orders:
        order["id"] = str(order.pop("_id"))
    return orders