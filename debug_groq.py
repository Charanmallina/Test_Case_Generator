# FILE: debug_groq.py

import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

def debug_api_key():
    """Debug the Groq API key issue"""
    
    print("🔍 DEBUGGING GROQ API KEY")
    print("=" * 40)
    
    # Get the API key
    raw_key = os.getenv('GROQ_API_KEY')
    
    if not raw_key:
        print("❌ No API key found in environment")
        return
    
    print(f"✅ Raw key found: {len(raw_key)} characters")
    print(f"📝 First 10 chars: {raw_key[:10]}")
    print(f"📝 Last 5 chars: {raw_key[-5:]}")
    
    # Check for common issues
    print(f"\n🔍 Key Analysis:")
    print(f"  • Contains quotes: {'"' in raw_key or "'" in raw_key}")
    print(f"  • Contains spaces: {' ' in raw_key}")
    print(f"  • Contains newlines: {'\\n' in raw_key or '\\r' in raw_key}")
    print(f"  • Starts with 'gsk_': {raw_key.startswith('gsk_')}")
    
    # Clean the key
    clean_key = raw_key.strip().strip('"').strip("'")
    print(f"\n🧹 Cleaned key: {len(clean_key)} characters")
    print(f"📝 Clean first 10: {clean_key[:10]}")
    print(f"📝 Clean last 5: {clean_key[-5:]}")
    
    # Test the API key
    print(f"\n🧪 Testing API key...")
    
    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 10
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers=headers, 
            json=test_payload, 
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key works!")
            result = response.json()
            print(f"🤖 AI Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ API Error: {response.text}")
            
            # Check if it's a rate limit or other issue
            if response.status_code == 429:
                print("💡 Rate limit - try again later")
            elif response.status_code == 401:
                print("💡 Invalid API key - check key in Groq console")
                print("💡 Make sure you copied the FULL key without extra characters")
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        print("💡 Check your internet connection")


def fix_env_file():
    """Help fix the .env file"""
    
    print(f"\n🔧 ENV FILE TROUBLESHOOTING")
    print("=" * 40)
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
        
        # Read the file
        with open('.env', 'r') as f:
            content = f.read()
        
        print(f"📄 File content preview:")
        print(content[:100] + "..." if len(content) > 100 else content)
        
        # Look for the GROQ_API_KEY line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'GROQ_API_KEY' in line:
                print(f"\n📝 Line {i+1}: {line}")
                
                # Check the format
                if '=' not in line:
                    print("❌ Missing '=' sign")
                elif line.count('=') > 1:
                    print("❌ Multiple '=' signs")
                elif line.strip().endswith('='):
                    print("❌ No value after '='")
                else:
                    print("✅ Format looks correct")
    else:
        print("❌ .env file not found!")
        print("💡 Create .env file in project root with:")
        print("   GROQ_API_KEY=your_actual_key_here")


if __name__ == "__main__":
    debug_api_key()
    fix_env_file()
    
    print(f"\n💡 NEXT STEPS:")
    print("1. If API key is invalid, get a new one from https://console.groq.com/")
    print("2. Make sure .env file format is: GROQ_API_KEY=your_key_here")
    print("3. No quotes, no spaces, no extra characters")
    print("4. Run this debug script again to verify")