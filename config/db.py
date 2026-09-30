from pymongo import MongoClient

MONGO_URI = "mongodb+srv://Herry:Herry%405%405@cluster0.ugnohw5.mongodb.net/"

client = MongoClient(MONGO_URI)

db = client["Restaurant_db"]

admins = db["admins"]
categories = db["categories"]
menus = db["menus"]
tables = db["tables"]
orders = db["orders"]
customers = db["customers"]