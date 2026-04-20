"""Script to seed the database with Admin and Staff users."""
import os
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def seed_users():
    """Create hashed users and inventory items."""
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DB_NAME")]
    
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

    for user_data in users_to_seed:
        if not db.users.find_one({"email": user_data["email"]}):
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(user_data["password"].encode('utf-8'), salt)
            
            db.users.insert_one({
                "email": user_data["email"],
                "password_hash": hashed_pw.decode('utf-8'),
                "role": user_data["role"],
                "name": user_data["name"]
            })
            print(f"✅ User {user_data['email']} created successfully!")
        else:
            print(f"ℹ️ User {user_data['email']} already exists.")

if __name__ == "__main__":
    seed_users()