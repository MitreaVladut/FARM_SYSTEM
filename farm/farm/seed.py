"""Script to seed the database with Admin, Staff, Inventory, Crops, and Parcels."""
import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def seed_database():
    """Create hashed users, inventory items, agricultural crops, and geometric parcels."""
    print("🌱 Starting Master Farm Database Seeder...")
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/"))
    db = client[os.getenv("DB_NAME", "farm_db")]
    
    # 1. Define and seed inventory
    inventory_to_seed = [
        {"name": "Organic Carrots", "price": "11 RON / kg", "stock": "120", "status": "In Stock", "image": "/carrots.jpg"},
        {"name": "Crisp Lettuce", "price": "9 RON / piece", "stock": "8", "status": "In Stock", "image": "/lettuce.jpg"},
        {"name": "New Potatoes", "price": "7 RON / kg", "stock": "210", "status": "In Stock", "image": "/potatoes.jpg"},
        {"name": "Fresh Tomatoes", "price": "17 RON / kg", "stock": "48", "status": "In Stock", "image": "/tomatoes.jpg"},
        {"name": "Zucchini", "price": "13 RON / kg", "stock": "0", "status": "Out of Stock", "image": "/zucchini.jpg"},
    ]

    if db.inventory.count_documents({}) == 0:
        db.inventory.insert_many(inventory_to_seed)
        print("✅ Inventory seeded successfully!")

    # 2. Define and seed users
    users_to_seed = [
        {"email": "admin@farm.com", "password": "admin123", "role": "Admin", "name": "Administrator"},
        {"email": "ion.popescu@farm.ro", "password": "staff123", "role": "Staff", "name": "Popescu Ion"},
        {"email": "maria.ionescu@farm.ro", "password": "staff123", "role": "Staff", "name": "Ionescu Maria"},
        {"email": "andrei.georgescu@farm.ro", "password": "staff123", "role": "Staff", "name": "Georgescu Andrei"}
    ]
    db.users.delete_many({})
    print("🗑️ Conturile vechi (nesecurizate) au fost șterse.")

    for user_data in users_to_seed:
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(user_data["password"].encode('utf-8'), salt)
        
        db.users.insert_one({
            "email": user_data["email"],
            "password": hashed_pw.decode('utf-8'), 
            "role": user_data["role"],
            "name": user_data["name"]
        })
        print(f"✅ User {user_data['email']} ({user_data['role']}) a fost creat cu parolă securizată!")

    # 3. Wipe old crops and parcels to prevent schema mismatch
    print("🧹 Wiping old crops and parcels to align with new environmental requirements...")
    db.crops.delete_many({})
    db.parcels.delete_many({})

    # 4. Define and seed Crops (REQ-3.3, REQ-3.4, REQ-3.8)
    initial_crops = [
        {
            "name": "Tomatoes", "yield_per_ha": "50",
            "growth_duration": "90 days", "planting_season": "Spring",
            "resources": "High Water, NPK Fertilizer (10-10-10)"
        },
        {
            "name": "Carrots", "yield_per_ha": "30",
            "growth_duration": "75 days", "planting_season": "Spring / Early Autumn",
            "resources": "Moderate Water, Loose/Sandy soil prep"
        },
        {
            "name": "Potatoes", "yield_per_ha": "40",
            "growth_duration": "110 days", "planting_season": "Early Spring",
            "resources": "Moderate Water, High Phosphorus Fertilizer"
        }
    ]
    
    # 5. Define and seed Parcels (REQ-2.2, REQ-2.3 & Geometric Maps)
    initial_parcels = [
        {
            "name": "North Field", "area": "2 ha", "crop": "Tomatoes",
            "planting_date": "2026-04-15", "status": "Planned",
            "latitude": "44.3202", "longitude": "23.7949",
            "x": 0, "y": 0, "width": 10, "height": 10,
            "soil_type": "Loam", "irrigation": True
        },
        {
            "name": "South Field", "area": "3.5 ha", "crop": "Carrots",
            "planting_date": "2026-03-20", "status": "In Production",
            "latitude": "44.3150", "longitude": "23.7910",
            "x": 15, "y": 0, "width": 15, "height": 10,
            "soil_type": "Sandy", "irrigation": False
        },
        {
            "name": "East Expansion", "area": "5 ha", "crop": "None",
            "planting_date": "None", "status": "Available",
            "latitude": "44.3180", "longitude": "23.8000",
            "x": 0, "y": 15, "width": 20, "height": 15,
            "soil_type": "Clay", "irrigation": True
        }
    ]
    
    db.crops.insert_many(initial_crops)
    print(f"✅ {len(initial_crops)} Crop types planted!")
    
    db.parcels.insert_many(initial_parcels)
    print(f"✅ {len(initial_parcels)} Geometric parcels registered!")
    
    print("🚀 Master Database Seed Complete!")

if __name__ == "__main__":
    seed_database()