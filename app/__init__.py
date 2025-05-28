import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Ensure data directory
os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)
