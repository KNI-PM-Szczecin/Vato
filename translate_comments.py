import os
import glob

replacements = {
    "# 1. Status prawny": "# 1. Legal status",
    "# 2. Doświadczenie": "# 2. Experience",
    "# 3. Podatki VAT / Biała Lista": "# 3. VAT Taxes / Whitelist",
    "# 4. Stabilność": "# 4. Stability",
    "# Docelowo tutaj można skonfigurować SMTP, np. smtplib.SMTP_SSL()": "# Ideally SMTP can be configured here, e.g. smtplib.SMTP_SSL()",
    "# lub połączyć się z zewnętrznym API do maili np. SendGrid / Resend.": "# or connect to an external email API e.g. SendGrid / Resend.",
    "Symuluje wysyłanie e-maila z ładnym formatowaniem HTML, CSS i ewentualnymi załącznikami.": "Simulates sending an email with nice HTML formatting, CSS, and potential attachments.",
    "Na tym etapie tylko wypisuje w konsoli informacje o wysyłce.": "At this stage it only prints the sending info to the console.",
    "# Type podmiotu: P → spółka (KRS), F/LP/LF → osoba fizyczna (CEIDG)": "# Entity type: P -> company (KRS), F/LP/LF -> natural person (CEIDG)",
    "# --- Card 1: Pliki ---": "# --- Card 1: Files ---",
    "# Zródło": "# Source",
    "# Zapis": "# Destination",
    "# --- Card 2: Akcje ---": "# --- Card 2: Actions ---",
    "# --- Card 3: Status ---": "# --- Card 3: Status ---",
    "# --- Card 1: Wyszukiwanie ---": "# --- Card 1: Search ---",
    "# --- Card 2: Raportowanie ---": "# --- Card 2: Reporting ---",
    "# --- Card 3: Wyniki ---": "# --- Card 3: Results ---",
    "# Używamy wątku, aby nie blokować GUI (responsivity fix)": "# We use a thread to avoid blocking the GUI (responsivity fix)",
    "# Wypisanie w obszarze tekstowym": "# Print to text area",
    "# Aktualizacja GUI z wątku głównego": "# GUI update from main thread"
}

files = glob.glob("**/*.py", recursive=True)
for f in files:
    if "venv" in f or "__pycache__" in f or f.startswith("translate_comments.py"):
        continue
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = content
    for k, v in replacements.items():
        new_content = new_content.replace(k, v)
        
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Updated comments in {f}")

