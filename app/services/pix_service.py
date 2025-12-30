import os

class PixService:
    def __init__(self):
        self.pix_key = os.getenv("PIX_KEY")
        self.merchant = os.getenv("PIX_MERCHANT", "Doação")
        self.city = os.getenv("PIX_CITY", "GOIANIA")

    def get_pix_key(self):
        return self.pix_key

    def generate_static_payload(self):
        # Payload PIX estático simples
        payload = f"00020126360014BR.GOV.BCB.PIX0114{self.pix_key}52040000530398654040.005802BR5913{self.merchant}6009{self.city}62070503***6304"
        return payload
