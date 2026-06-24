import os
import sys
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(project_root, 'api', '.env')
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("ELEVENLABS_API_KEY")
if api_key:
    api_key = api_key.strip()

from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key=api_key)

try:
    audio = client.text_to_speech.convert(
        text="Test",
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model_id="eleven_multilingual_v2",
        output_format="pcm_44100"
    )
    raw_pcm = b"".join(audio)
    print(f"Success! Length: {len(raw_pcm)}")
except Exception as e:
    print(f"Failed: {e}")

