import hashlib
import os
import base64
from typing import Optional, Dict, Any

# TODO: look through this, and see if we can improve it
class HashingService:
    """Service for generating SHA3-256 hashes"""

    # Constructor method, 
    # Runs when instance is created, (empty, no setup needed here yet)
    def __init__(self):
        pass

    def hash_content(self, content: bytes) -> str:
        """
        Generate SHA3-256 hash of content directly
        
        Args:
            content: Bytes content to hash
            
        Returns:
            SHA3-256 hash as hex string
        """
        # Log the content being hashed
        try:
            # print(f"----> Hash content: {content}")
            content_str = content.decode('utf-8')
            # print(f"Content to hash: '{content_str}'")
        except UnicodeDecodeError:
            # print(f"Content to hash (raw bytes): {content}")
            print(f"UnicodeDecodeError")

        print(f"Using SHA3-256 hashing algorithm")
        sha3_256 = hashlib.sha3_256()
        sha3_256.update(content)
        
        result = sha3_256.hexdigest()
        print(f"Generated hash: {result}")
        return result

    def hash_uploaded_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hash an uploaded file from file data
        
        Args:
            file_data: Dictionary containing file data with 'contents' and 'filename' keys
            
        Returns:
            Dictionary containing hash result with file_id, filename, hash, and hashed_at
        """
        from datetime import datetime, timezone
        from uuid import uuid4
        
        file_contents = file_data["contents"]
        filename = file_data["filename"]
        
        # Log the raw file contents to see what we're getting
        # print(f"Raw file contents type: {type(file_contents)}")
        # print(f"Raw file contents: '{file_contents}'")
        
        # Convert to bytes if it's a string
        if isinstance(file_contents, str):
            # Check if it's base64 encoded
            try:
                # Try to decode base64 first
                decoded_content = base64.b64decode(file_contents)
                # print(f"Base64 decoded content: {decoded_content}")
                file_contents = decoded_content
            except Exception as e:
                print(f"Not base64 encoded, treating as UTF-8: {e}")
                file_contents = file_contents.encode("utf-8")
        
        hash_value = self.hash_content(file_contents)

        # Create hash record
        file_id = f"file_{uuid4().hex[:8]}"
        hash_record = {
            "file_id": file_id,
            "filename": filename,
            "hash": hash_value,
            "hashed_at": datetime.now(timezone.utc).isoformat()
        }
        
        return hash_record

    # async def hash_file(self, file_path: str) -> Optional[str]:
    #     """
    #     Generate SHA3-256 hash of a file
        
    #     Args:
    #         file_path: Path to the file to hash
            
    #     Returns:
    #         SHA3-256 hash as hex string, or None if file doesn't exist
    #     """
    #     try:
    #         print(f"----> Hash file: {file_path}")
    #         # Check if the file actually exists
    #         if not os.path.exists(file_path):
    #             print(f"File does not exist: {file_path}")
    #             return None
                
    #         # Check if it's a file (not a directory)
    #         if not os.path.isfile(file_path):
    #             print(f"Path is not a file: {file_path}")
    #             return None
                
    #         # Check if we have read permissions
    #         if not os.access(file_path, os.R_OK):
    #             print(f"No read permission for file: {file_path}")
    #             return None
            
    #         # Read and log file content (for logs only, ok to remove)
    #         with open(file_path, "r", encoding='utf-8') as f:
    #             file_content = f.read()
    #             print(f"File content: '{file_content}'")
            
    #         print(f"Using SHA3-256 hashing algorithm")
                
    #         # Create SHA3-256 hash object
    #         sha3_256 = hashlib.sha3_256()

    #         # Open file and read in chunks of 4096 bytes
    #         with open(file_path, "rb") as f:
    #             for chunk in iter(lambda: f.read(4096), b""):
    #                 sha3_256.update(chunk)

    #         # Return the final hash value as a hexadecimal string
    #         result = sha3_256.hexdigest()
    #         print(f"Generated hash: {result}")
    #         return result
        
    #     except FileNotFoundError as e:
    #         print(f"File not found: {file_path} - {e}")
    #         return None
    #     except PermissionError as e:
    #         print(f"Permission denied for file: {file_path} - {e}")
    #         return None
    #     except Exception as e:
    #         # If anything goes wrong (bad path, permission error, etc.),
    #         # print the error and return None
    #         print(f"Error hashing file {file_path}: {e}")
    #         return None