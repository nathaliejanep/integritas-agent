from app.adapters.integritas_client import IntegritasClient

class VerificationService:
    def __init__(self, integ: IntegritasClient):
        self.integ = integ

    async def verify(self, proof: str, root: str, address: str, data: str, request_id: str):
        payload = [{"proof": proof, "root": root, "address": address, "data": data}]
        return await self.integ.verify_proof(payload, request_id)
