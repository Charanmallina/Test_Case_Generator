import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Test if API key is loaded
api_key = os.getenv('GROQ_API_KEY')

if api_key:
    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-5:]}")
    print("🚀 Ready to run the AI generator!")
else:
    print("❌ API key not found")