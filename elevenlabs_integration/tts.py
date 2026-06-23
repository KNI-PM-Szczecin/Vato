import os
import threading
from dotenv import load_dotenv

load_dotenv()

def play_text(text: str, override_voice: str = None, show_errors: bool = False):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    
    if not api_key:
        if show_errors:
            from views.popup import PopupMessage
            PopupMessage("Błąd", "Brak klucza ELEVENLABS_API_KEY w zmiennych środowiskowych.", status="error")
        else:
            print("ElevenLabs API Key is missing. Skipping TTS.")
        return
        
    def _run_tts():
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs.play import play
            
            from services.config_manager import ConfigManager
            from services.i18n import get_language
            
            if override_voice:
                voice_name = override_voice
            else:
                lang = get_language()
                default_voice = "Adam" if lang == "pl" else "Rachel"
                voice_name = ConfigManager().get(f"tts_voice_{lang}", default_voice)
            
            client = ElevenLabs(api_key=api_key)
            
            # Find the ID for the requested voice name
            voice_id = "21m00Tcm4TlvDq8ikWAM" # default Rachel
            try:
                voices_res = client.voices.get_all()
                for v in voices_res.voices:
                    if v.name == voice_name:
                        voice_id = v.voice_id
                        break
            except Exception:
                pass

            audio = client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            play(audio)
        except Exception as e:
            if show_errors:
                from views.popup import PopupMessage
                
                err_msg = str(e)
                if "invalid_api_key" in err_msg:
                    err_msg = "Nieprawidłowy klucz API (Invalid API key)."
                    
                print(f"TTS Error: {e}")
                try:
                    PopupMessage("Błąd", f"Błąd ElevenLabs: {err_msg}", status="error")
                except:
                    pass
            else:
                print(f"TTS Error: {e}")
            
    threading.Thread(target=_run_tts, daemon=True).start()

