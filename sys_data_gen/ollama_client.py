import requests
import json
import time

class OllamaClient:
    """Client đơn giản để gọi Ollama API"""
    
    def __init__(self, model_name="qwen2.5:7b", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def generate(self, prompt, temperature=0.8, max_tokens=500):
        """Gọi Ollama để sinh text"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            print(f"Error: {e}")
            return ""
    
    def check_health(self):
        """Kiểm tra Ollama đang chạy"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

if __name__ == "__main__":
    # Test kết nối
    client = OllamaClient()
    if client.check_health():
        print("✅ Ollama is running")
        print(f"📌 Using model: {client.model_name}")
    else:
        print("❌ Cannot connect to Ollama")
        print("Please run: ollama run qwen2.5:7b")