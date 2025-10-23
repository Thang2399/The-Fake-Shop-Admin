from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
client = AsyncIOMotorClient(os.getenv("MONGOOSE_CONNECTION"))
db = client[os.getenv("DB_NAME")]