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
                    if voice_name == v.name or voice_name in v.name or v.name in voice_name:
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
            
            # The user considers the default generated audio volume as 33% (slider = 0.33)
            # So if slider is 0.33 -> multiplier 1.0. If slider is 1.0 -> multiplier ~3.0
            tts_vol = ConfigManager().get("tts_volume", 0.33)
            vol_multiplier = tts_vol * 3.0
            
            audio_data = b"".join(audio)
            import subprocess
            args = ["ffplay", "-autoexit", "-", "-nodisp", "-af", f"volume={vol_multiplier}"]
            proc = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            proc.communicate(input=audio_data)
        except Exception as e:
            if show_errors:
                from views.popup import PopupMessage
                from services.i18n import t
                
                err_msg = str(e)
                if "invalid_api_key" in err_msg:
                    err_msg = t("settings.invalid_api_key")
                    
                print(f"TTS Error: {e}")
                try:
                    PopupMessage(t("popup.error"), f"ElevenLabs: {err_msg}", status="error")
                except:
                    pass
            else:
                print(f"TTS Error: {e}")
            
    threading.Thread(target=_run_tts, daemon=True).start()

def get_available_voices():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None
        
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=api_key)
        res = client.voices.get_all()
        
        pl_voices = []
        en_voices = []
        
        for v in res.voices:
            is_pl = False
            is_en = False
            
            # Check labels for custom user voices
            if v.labels:
                lang = v.labels.get('language', '').lower()
                accent = v.labels.get('accent', '').lower()
                if 'pl' in lang or 'polish' in lang or 'pl' in accent or 'polish' in accent:
                    is_pl = True
                elif 'en' in lang or 'english' in lang or 'american' in accent or 'british' in accent:
                    is_en = True

            # Standard ElevenLabs voices that work well in Polish
            if any(name in v.name for name in ["Adam", "Antoni", "Domi", "Rachel"]):
                is_pl = True
                
            # Standard ElevenLabs voices for English
            if any(name in v.name for name in ["Bill", "Brian", "Callum", "Charlie", "Eric", "Harry", "Jessica", "Liam", "Matilda", "Roger", "Will", "Drew", "Clyde", "Mimi", "Fin", "Alice", "Bella", "Daniel", "Laura", "Lily", "River", "Sarah", "George", "Chris"]):
                is_en = True

            # If no explicit language labels and not a known standard voice, add to both
            if is_pl:
                pl_voices.append(v.name)
            elif is_en:
                en_voices.append(v.name)
            else:
                pl_voices.append(v.name)
                en_voices.append(v.name)
                
        if not pl_voices:
            pl_voices = ["Adam", "Antoni", "Domi", "Rachel"]
        if not en_voices:
            en_voices = ["Rachel", "Drew", "Clyde", "Mimi", "Fin"]
            
        return {"pl": sorted(list(set(pl_voices))), "en": sorted(list(set(en_voices)))}
    except Exception as e:
        print(f"Failed to fetch voices from API: {e}")
        return None

