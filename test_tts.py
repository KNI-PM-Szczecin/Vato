from elevenlabs.client import ElevenLabs
import traceback

try:
    client = ElevenLabs() 
    res = client.voices.get_all()
    v = res.voices[0]
    print("Voice attributes:", dir(v))
    print("Category:", getattr(v, "category", "N/A"))
except Exception as e:
    traceback.print_exc()

