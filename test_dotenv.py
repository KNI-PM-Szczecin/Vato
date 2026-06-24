import os
from dotenv import load_dotenv

load_dotenv('api/.env')
print(f"KEY='{os.environ.get('ELEVENLABS_API_KEY')}'")
