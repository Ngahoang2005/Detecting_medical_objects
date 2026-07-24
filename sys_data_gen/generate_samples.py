import json
import random
from ollama_client import OllamaClient

class SimpleDataGenerator:
    """Generator đơn giản để tạo 3 sample"""
    
    def __init__(self):
        self.client = OllamaClient()
        
    def generate_sample_1(self):
        """Sample 1: Bệnh nhân bị đái tháo đường và tăng huyết áp"""
        prompt = """
Bạn là một bác sĩ lâm sàng. Hãy viết một đoạn ghi chú y khoa cho bệnh nhân có các thông tin sau:
- Chẩn đoán: Đái tháo đường type 2 (E11.9) và Tăng huyết áp (I10)
- Thuốc đang dùng: Metformin 500mg, Lisinopril 10mg
- Triệu chứng: Mệt mỏi, khát nước nhiều, tiểu nhiều
- Tiền sử: Đã mắc bệnh 5 năm
- Context: Bệnh nhân có tiền sử gia đình bị đái tháo đường

Yêu cầu:
1. Viết một đoạn văn 50-80 từ, phong cách ghi chú bác sĩ
2. Đánh dấu các khái niệm y tế bằng cách liệt kê sau đoạn văn
3. Bao gồm thông tin về: CHẨN_ĐOÁN, THUỐC, TRIỆU_CHỨNG

Trả về định dạng JSON như sau:
{
    "text": "đoạn văn bản y khoa",
    "entities": [
        {"text": "tên khái niệm", "type": "CHẨN_ĐOÁN", "start": 0, "end": 10},
        {"text": "tên khái niệm", "type": "THUỐC", "start": 20, "end": 30},
        {"text": "tên khái niệm", "type": "TRIỆU_CHỨNG", "start": 40, "end": 50}
    ],
    "assertions": {
        "text": "tên khái niệm", 
        "isHistorical": true/false,
        "isFamily": true/false,
        "isNegated": true/false
    }
}
"""
        response = self.client.generate(prompt, temperature=0.7)
        return self._parse_response(response, "Sample 1")
    
    def generate_sample_2(self):
        """Sample 2: Bệnh nhân hen suyễn - có phủ định"""
        prompt = """
Bạn là một bác sĩ lâm sàng. Hãy viết một đoạn ghi chú y khoa cho bệnh nhân có các thông tin sau:
- Chẩn đoán: Hen suyễn (J45.909)
- Thuốc: Albuterol inhaler, Fluticasone
- Triệu chứng: Khó thở, ho, tức ngực
- Lưu ý: Bệnh nhân KHÔNG sốt, KHÔNG có đờm
- Tiền sử: Bệnh nhân đã từng bị hen suyễn từ nhỏ
- Context: Đang khám cấp cứu

Yêu cầu:
1. Viết đoạn văn 50-80 từ, phong cách ghi chú cấp cứu
2. Đánh dấu các khái niệm y tế
3. Đánh dấu các assertion: phủ định, tiền sử

Trả về định dạng JSON.
"""
        response = self.client.generate(prompt, temperature=0.7)
        return self._parse_response(response, "Sample 2")
    
    def generate_sample_3(self):
        """Sample 3: Bệnh nhân viêm phổi - kết quả xét nghiệm"""
        prompt = """
Bạn là một bác sĩ lâm sàng. Hãy viết một đoạn ghi chú y khoa cho bệnh nhân có các thông tin sau:
- Chẩn đoán: Viêm phổi (J18.9)
- Thuốc: Amoxicillin 500mg
- Triệu chứng: Sốt 39°C, ho có đờm xanh
- Kết quả xét nghiệm: WBC 14.5, Neutrophils 80%
- Context: Bệnh nhân nhập viện 2 ngày trước

Yêu cầu:
1. Viết đoạn văn 50-80 từ, phong cách bệnh án nội trú
2. Đánh dấu các khái niệm: CHẨN_ĐOÁN, THUỐC, TRIỆU_CHỨNG, TÊN_XÉT_NGHIỆM, KẾT_QUẢ_XÉT_NGHIỆM

Trả về định dạng JSON.
"""
        response = self.client.generate(prompt, temperature=0.7)
        return self._parse_response(response, "Sample 3")
    
    def _parse_response(self, response, sample_name):
        """Parse response từ Qwen sang JSON"""
        try:
            # Tìm JSON trong response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                print(f"✅ {sample_name} generated successfully")
                return data
            else:
                # Fallback: tạo cấu trúc cơ bản
                print(f"⚠️ No JSON found in {sample_name}, creating basic structure")
                return {
                    "text": response.strip(),
                    "entities": [],
                    "assertions": {}
                }
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error in {sample_name}: {e}")
            return {
                "text": response.strip(),
                "entities": [],
                "assertions": {}
            }
    
    def generate_all_samples(self):
        """Sinh tất cả 3 samples"""
        print("="*60)
        print("🚀 Generating 3 Synthetic Samples with Qwen2.5")
        print("="*60)
        
        print("\n📝 Generating Sample 1...")
        sample1 = self.generate_sample_1()
        
        print("\n📝 Generating Sample 2...")
        sample2 = self.generate_sample_2()
        
        print("\n📝 Generating Sample 3...")
        sample3 = self.generate_sample_3()
        
        return [sample1, sample2, sample3]

if __name__ == "__main__":
    # Test sinh 1 sample
    generator = SimpleDataGenerator()
    if generator.client.check_health():
        print("✅ Connected to Ollama\n")
        samples = generator.generate_all_samples()
        print(f"\n✅ Generated {len(samples)} samples")
    else:
        print("❌ Cannot connect to Ollama. Please start Ollama first.")