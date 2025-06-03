# Website Monitoring Configuration
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Hardcoded websites that should always be monitored
HARDCODED_WEBSITES = [
    "https://delfi.lt",
    "https://google.com"
]
