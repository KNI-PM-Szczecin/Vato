import os
import threading
import re
from dotenv import load_dotenv

import sys
if getattr(sys, 'frozen', False):
    project_root = sys._MEIPASS
else:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(project_root, '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

_is_playing = False
_tts_busy_popup_open = False
_current_tts_process = None

def stop_tts(show_popup=True):
    global _current_tts_process, _is_playing, _tts_busy_popup_open
    interrupted = False
    
    if _current_tts_process is not None:
        try:
            _current_tts_process.kill()
            interrupted = True
        except Exception:
            pass
        _current_tts_process = None
        
    if _is_playing and not interrupted:
        # It was loading from network but hasn't started playing yet
        interrupted = True
        
    _is_playing = False
    _tts_busy_popup_open = False
    
    if interrupted and show_popup:
        from views.popup import PopupMessage
        from services.i18n import t
        # We don't want this popup to block the UI aggressively, so we'll just show it briefly or let the user click OK.
        # But wait, maybe just a simple information is enough.
        PopupMessage(t("popup.warning"), "Poprzedni lektor został przerwany przez nowe żądanie.", status="warning")

def play_text(text: str, override_voice: str = None, show_errors: bool = False, on_start=None):
    global _is_playing, _tts_busy_popup_open, _current_tts_process
    
    if _is_playing:
        if show_errors and not _tts_busy_popup_open:
            _tts_busy_popup_open = True
            from views.popup import PopupMessage
            from services.i18n import t
            
            def _on_close(e):
                global _tts_busy_popup_open
                _tts_busy_popup_open = False
                
            p = PopupMessage(t("popup.warning"), t("settings.tts_busy"), status="warning")
            p.bind("<Destroy>", lambda e: _on_close(e) if e.widget == p else None)
        return
        
    from services.i18n import get_language
    lang = get_language()

    # Preprocess text for ElevenLabs
    text = re.sub(r'\bpkt\.?', 'punkty', text, flags=re.IGNORECASE)
    text = re.sub(r'\b\d{10}\b', lambda m: ' '.join(m.group(0)), text)
    
    if lang == "pl":
        text = re.sub(r'\btrue\b', 'prawda', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfalse\b', 'fałsz', text, flags=re.IGNORECASE)
    elif lang == "de":
        text = re.sub(r'\btrue\b', 'wahr', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfalse\b', 'falsch', text, flags=re.IGNORECASE)
        replacements = {
            r'\baktywna\b': 'aktiv', r'\baktywny\b': 'aktiv', r'\bczynny\b': 'aktiv',
            r'\bzawieszona\b': 'ausgesetzt', r'\bzawieszony\b': 'ausgesetzt',
            r'\bwykreślona\b': 'gelöscht', r'\bwykreślony\b': 'gelöscht', r'\bwykreslony\b': 'gelöscht',
            r'\btak\b': 'ja', r'\bnie\b': 'nein',
            r'\bbrak danych\b': 'keine Daten', r'\bnieznany\b': 'unbekannt'
        }
        for pat, repl in replacements.items():
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    elif lang == "en":
        text = re.sub(r'\btrue\b', 'true', text, flags=re.IGNORECASE)
        text = re.sub(r'\bfalse\b', 'false', text, flags=re.IGNORECASE)
        replacements = {
            r'\baktywna\b': 'active', r'\baktywny\b': 'active', r'\bczynny\b': 'active',
            r'\bzawieszona\b': 'suspended', r'\bzawieszony\b': 'suspended',
            r'\bwykreślona\b': 'removed', r'\bwykreślony\b': 'removed', r'\bwykreslony\b': 'removed',
            r'\btak\b': 'yes', r'\bnie\b': 'no',
            r'\bbrak danych\b': 'no data', r'\bnieznany\b': 'unknown'
        }
        for pat, repl in replacements.items():
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if api_key:
        api_key = api_key.strip()
    
    if not api_key:
        if on_start:
            try: on_start()
            except: pass
        if show_errors:
            from views.popup import PopupMessage
            from services.i18n import t
            PopupMessage(t("popup.error"), "Brak klucza ELEVENLABS_API_KEY w zmiennych środowiskowych.", status="error")
        else:
            print("ElevenLabs API Key is missing. Skipping TTS.")
        return
        
    def _run_tts():
        global _current_tts_process, _is_playing
        try:
            from elevenlabs.client import ElevenLabs
            
            from services.config_manager import ConfigManager
            from services.i18n import get_language
            
            if override_voice:
                voice_name = override_voice
            else:
                lang = get_language()
                default_voice = {"pl": "Adam", "de": "Rachel"}.get(lang, "Rachel")
                voice_name = ConfigManager().get(f"tts_voice_{lang}", default_voice)
            
            client = ElevenLabs(api_key=api_key)
            
            voice_id = "21m00Tcm4TlvDq8ikWAM"
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
            
            if not _is_playing:
                if on_start:
                    try: on_start()
                    except: pass
                return
            
            tts_vol = ConfigManager().get("tts_volume", 0.33)
            vol_multiplier = tts_vol * 3.0
            
            audio_data = b"".join(audio)
            
            if not _is_playing:
                if on_start:
                    try: on_start()
                    except: pass
                return
            
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
            
            import subprocess
            import sys
            args = ["ffplay", "-autoexit", "-", "-nodisp", "-af", f"volume={vol_multiplier}"]
            try:
                proc = subprocess.Popen(
                    args=args,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                _current_tts_process = proc
                proc.communicate(input=audio_data)
            except FileNotFoundError:
                if sys.platform.startswith("win"):
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                        f.write(audio_data)
                        tmp_path = f.name
                    
                    vol = int(33 * vol_multiplier)
                    vol = max(0, min(100, vol))
                    
                    ps_script = f"""
$player = New-Object -ComObject WMPlayer.OCX
$player.settings.volume = {vol}
$player.URL = '{tmp_path}'
while ($player.playState -ne 3 -and $player.playState -ne 1 -and $player.playState -ne 10) {{ Start-Sleep -Milliseconds 100 }}
while ($player.playState -eq 3) {{ Start-Sleep -Milliseconds 100 }}
"""
                    proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script], creationflags=0x08000000)
                    _current_tts_process = proc
                    proc.wait()
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                else:
                    raise
            finally:
                _current_tts_process = None
        except Exception as e:
            if on_start:
                try:
                    on_start()
                except Exception:
                    pass
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
        finally:
            _is_playing = False
            
    _is_playing = True
    threading.Thread(target=_run_tts, daemon=True).start()

def get_available_voices():
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if api_key:
        api_key = api_key.strip()
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=api_key) if api_key else ElevenLabs()
        res = client.voices.get_all()
        
        formatted_voices = []
        
        for v in res.voices:
            tag = ""
            name_check = v.name.lower()
            
            if any(n in name_check for n in ["adam", "antoni", "domi", "marek"]):
                tag = "[PL]"
            elif any(n in name_check for n in ["markus", "hans", "arnold", "fritz", "klaus", "marlene"]):
                tag = "[DE]"
            elif v.labels and 'language' in v.labels:
                lang = str(v.labels['language']).upper()
                if "POLISH" in lang or lang == "PL": tag = "[PL]"
                elif "GERMAN" in lang or lang == "DE": tag = "[DE]"
                elif "ENGLISH" in lang or lang == "EN": tag = "[EN]"
                else: tag = f"[{lang[:2]}]"
            else:
                if getattr(v, "category", "") != "premade":
                    tag = "[CUSTOM]"
                else:
                    tag = "[EN]"
                    
            formatted_name = f"{tag} {v.name}"
            formatted_voices.append(formatted_name)
            
        formatted_voices = sorted(list(set(formatted_voices)))
        return {"pl": formatted_voices, "en": formatted_voices, "de": formatted_voices}
    except Exception as e:
        print(f"Failed to fetch voices from API: {e}")
        return None

