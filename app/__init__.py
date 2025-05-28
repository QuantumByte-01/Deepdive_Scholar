import os
from dotenv import load_dotenv

load_dotenv()

os.makedirs(os.path.join(os.getcwd(), "data"), exist_ok=True)
