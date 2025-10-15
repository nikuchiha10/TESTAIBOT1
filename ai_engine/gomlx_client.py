import requests
import logging
from typing import List, Optional
from config import config

logger = logging.getLogger(__name__)

class GoMLXClient:
    def __init__(self):
        self.base_url = f"http://{config.GOMLX_HOST}:{config.GOMLX_PORT}"
        
    def health_check(self) -> bool:
        """Check if GoMLX service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"GoMLX health check failed: {e}")
            return False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using GoMLX"""
        try:
            response = requests.post(
                f"{self.base_url}/embed",
                json={"text": text},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["embedding"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating embedding with GoMLX: {e}")
            return None
    
    def optimize_model(self, model_path: str) -> Optional[str]:
        """Optimize model using GoMLX"""
        try:
            response = requests.post(
                f"{self.base_url}/optimize",
                json={"model_path": model_path},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    return data["optimized_path"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing model with GoMLX: {e}")
            return None
