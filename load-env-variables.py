from dotenv import load_dotenv,find_dotenv

dotnev_path = find_dotenv()
print(f"found .env at {dotnev_path}")
load_dotenv(dotnev_path)
