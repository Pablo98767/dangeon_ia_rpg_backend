import asyncio, os
from dotenv import load_dotenv
from app.services.firebase_identity_svc import signin_email_password

load_dotenv()

async def main():
    email = os.environ.get("TEST_EMAIL") or input("Email: ").strip()
    password = os.environ.get("TEST_PASSWORD") or input("Senha: ").strip()
    data = await signin_email_password(email, password)
    print("Login OK.")
    print({
        "idToken": data["idToken"],
        "refreshToken": data["refreshToken"],
        "localId": data["localId"],
        "expiresIn": data["expiresIn"],
    })

if __name__ == "__main__":
    asyncio.run(main())
