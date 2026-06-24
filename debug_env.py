import os
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(project_root, '.env')
print("Does .env exist in root?", os.path.exists(env_path))
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

for k, v in os.environ.items():
    if "ELEVEN" in k.upper() or "API" in k.upper() or "KEY" in k.upper():
        print(f"ENV VAR: {k} = {v[:4]}...{v[-4:] if len(v) > 8 else ''}")
