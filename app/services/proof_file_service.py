import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path
from app.adapters.integritas_client import IntegritasClient


class ProofFileService:
    """
    Service for saving proof data to JSON files and generating proof files.
    """
    
    def __init__(self, integritas_client: IntegritasClient, output_dir: str = "proofs"):
        """
        Initialize the proof file service.
        
        Args:
            integritas_client: Client for interacting with Integritas API
            output_dir: Directory where proof files will be saved (default: "proofs")
        """
        self.integ = integritas_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_proof_data(self, proof_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Save proof data to a JSON file.
        
        Args:
            proof_data: Dictionary containing proof, root, address, and data
        
        Returns:
            Dict containing success status, file path, and any error message
        """
        try:
            # Validate proof data
            required_keys = ["proof", "root", "address", "data"]
            missing_keys = [key for key in required_keys if key not in proof_data]
            
            if missing_keys:
                return {
                    "success": False,
                    "file_path": None,
                    "error": f"Missing required keys: {', '.join(missing_keys)}"
                }
            
            # Generate filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"proof_{timestamp}.json"
            
            # Create full file path
            file_path = self.output_dir / filename
            
            # Prepare the data for saving
            file_data = {
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "proof_count": 1,
                    "version": "1.0"
                },
                "proofs": [proof_data]
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "filename": filename
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": None,
                "error": f"Failed to save proof data: {str(e)}"
            }

    async def generate_proof_file_from_uids(self, uids: List[str], custom_filename: str = None) -> Dict[str, Any]:
        """
        Generate a proof file by calling the /get-proof-file endpoint with UIDs.
        
        Args:
            uids: List of UIDs to generate proof file for
            custom_filename: Optional custom filename
            
        Returns:
            Dict containing success status, file path, and any error message
        """
        try:
            # Use the IntegritasClient to get the proof file
            filename = await self.integ.get_proof_file(uids, custom_filename)
            
            return {
                "success": True,
                "file_path": filename,
                "filename": os.path.basename(filename)
            }
            
        except Exception as e:
            return {
                "success": False,
                "file_path": None,
                "error": f"Failed to generate proof file: {str(e)}"
            }
