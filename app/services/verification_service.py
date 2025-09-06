from app.adapters.integritas_client import IntegritasClient
import json
import base64

class VerificationService:
    def __init__(self, integ: IntegritasClient):
        self.integ = integ

    def is_proof_file(self, file_data: dict) -> bool:
        """
        Check if uploaded file is a valid proof file with required JSON structure.
        Returns True if it's a valid proof file, False otherwise.
        """
        # print(f"Step 1: Checking if uploaded file is a proof file...")
        
        try:
            # Check if it's a JSON file
            if file_data.get("mime_type") != "application/json":
                # print(f"File is not JSON (mime_type: {file_data.get('mime_type')})")
                return False
            
            # Parse the JSON content (handle base64 encoding)
            contents = file_data.get("contents", "")
            if isinstance(contents, bytes):
                contents = contents.decode('utf-8')
            
            # Check if content is base64 encoded
            try:
                # Try to decode base64 first
                decoded_content = base64.b64decode(contents).decode('utf-8')
                # print(f"Content was base64 encoded, decoded successfully")
                contents = decoded_content
            except:
                # If base64 decode fails, assume it's plain text
                print(f"Content is not base64 encoded, using as-is")
            
            # print(f"File contents: {contents[:200]}...")  # Print first 200 chars
            
            data = json.loads(contents)
            # print(f"JSON parsed successfully: {type(data)}")
            
            # Check if it's a list
            if not isinstance(data, list):
                print("JSON is not a list")
                return False
            
            # Check if list has at least one item
            if len(data) == 0:
                print("JSON list is empty")
                return False
            
            # Check first item has required properties
            first_item = data[0]
            required_props = ["address", "data", "proof", "root"]
            
            for prop in required_props:
                if prop not in first_item:
                    print(f"Missing required property: {prop}")
                    return False
            
            print(f"✅ File is a valid proof file with {len(data)} proof(s)")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking proof file: {e}")
            return False

    def parse_proof_file(self, file_data: dict) -> dict:
        """
        Parse a proof file and return the first proof data.
        Assumes the file has already been validated by is_proof_file().
        """
        print(f"Step 4: Parsing proof file to extract verification data...")
        
        try:
            contents = file_data.get("contents", "")
            if isinstance(contents, bytes):
                contents = contents.decode('utf-8')
            
            # Handle base64 encoding
            try:
                decoded_content = base64.b64decode(contents).decode('utf-8')
                print(f"Content was base64 encoded, decoded successfully")
                contents = decoded_content
            except:
                print(f"Content is not base64 encoded, using as-is")
            
            proof_data = json.loads(contents)
            first_proof = proof_data[0]  # Use the first proof in the list
            
            print(f"✅ Successfully extracted proof data: {first_proof}")
            return first_proof
            
        except Exception as e:
            print(f"❌ Error parsing proof file: {e}")
            raise e

    async def verify(self, proof: str, root: str, address: str, data: str, request_id: str):
        payload = [{"proof": proof, "root": root, "address": address, "data": data}]
        return await self.integ.verify_proof(payload, request_id)
