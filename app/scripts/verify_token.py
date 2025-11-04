import os
from dotenv import load_dotenv
from app.services.firebase_admin_svc import verify_id_token

load_dotenv()

def main():
    token = os.environ.get("TEST_ID_TOKEN") or input("ID Token (Bearer): ").strip()
    decoded = verify_id_token(token)
    print("Token válido. Claims decodificadas:")
    print(decoded)

if __name__ == "__main__":
    main()
