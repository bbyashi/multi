import os

# ===== TELEGRAM API =====
API_ID = int(os.environ.get("API_ID", 21189715))          # Your Telegram API ID
API_HASH = os.environ.get("API_HASH", "988a9111105fd2f0c5e21c2c2449edfd")         # Your Telegram API Hash
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8388314171:AAFXrRKZU0d7XMRP5sRNi89ixXXzYGo0_Ws")       # Your Bot Token
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8111174619))     # Your Telegram ID (Admin)

# ===== MONGODB =====
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://codexkairnex:gm6xSxXfRkusMIug@cluster0.bplk1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")       # MongoDB connection string

# ===== OTHER SETTINGS =====
FLOOD_DELAY = int(os.environ.get("FLOOD_DELAY", 5))  # Delay between messages (seconds)
