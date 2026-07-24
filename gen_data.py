"""
SYNTHETIC DATA GENERATOR - FINAL FIX
Tạo 3 file dữ liệu tổng hợp DÀI và CHẤT LƯỢNG
"""

import zipfile
import os
import json
import re
import time
import shutil
import random
from pathlib import Path
from typing import List, Dict
from collections import Counter
import requests


# ==================== PHẦN 1: ĐỌC DỮ LIỆU ====================

class DataExtractor:
    def __init__(self, zip_path="data/input_turn2_vong1.zip"):
        self.zip_path = Path(zip_path)
        self.extract_dir = Path("temp_extracted")
        self.samples = []
        
    def extract_and_read(self) -> List[Dict]:
        if not self.zip_path.exists():
            print(f"❌ File not found: {self.zip_path}")
            return []
        
        if self.extract_dir.exists():
            shutil.rmtree(self.extract_dir)
        
        print(f"📦 Extracting {self.zip_path.name}...")
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_dir)
            print("✅ Extraction complete")
        except Exception as e:
            print(f"❌ Error extracting: {e}")
            return []
        
        input_dir = self.extract_dir / "input"
        if not input_dir.exists():
            possible_dirs = list(self.extract_dir.glob("*/input"))
            if possible_dirs:
                input_dir = possible_dirs[0]
            else:
                print(f"❌ Cannot find 'input' directory")
                return []
        
        txt_files = sorted(input_dir.glob("*.txt"))
        print(f"📂 Found {len(txt_files)} .txt files")
        
        for file_path in txt_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.samples.append({
                            'filename': file_path.name,
                            'content': content,
                            'length': len(content),
                            'word_count': len(content.split()),
                            'file_id': int(file_path.stem) if file_path.stem.isdigit() else 0
                        })
            except Exception as e:
                print(f"⚠️ Error reading {file_path.name}: {e}")
        
        print(f"✅ Read {len(self.samples)} valid files")
        return self.samples
    
    def cleanup(self):
        if self.extract_dir.exists():
            shutil.rmtree(self.extract_dir)
            print("🧹 Cleaned up temp directory")


# ==================== PHẦN 2: PHÂN TÍCH ====================

class StyleAnalyzer:
    def __init__(self, samples: List[Dict]):
        self.samples = samples
        
    def analyze(self) -> Dict:
        if not self.samples:
            return {}
        
        print("🔍 Analyzing 100 files...")
        
        all_words = []
        for sample in self.samples:
            all_words.extend(sample['content'].split())
        word_freq = Counter(all_words)
        
        # Lấy 2 mẫu DÀI NHẤT
        sorted_samples = sorted(self.samples, key=lambda x: x['length'], reverse=True)
        long_samples = sorted_samples[:2]
        
        analysis_result = {
            'total_files': len(self.samples),
            'avg_length': sum(s['length'] for s in self.samples) / len(self.samples),
            'avg_words': sum(s['word_count'] for s in self.samples) / len(self.samples),
            'long_samples': long_samples,
            'common_words': word_freq.most_common(10)
        }
        
        print("✅ Analysis complete")
        print(f"📊 Average length: {analysis_result['avg_length']:.0f} chars")
        print(f"📊 Max length: {analysis_result['long_samples'][0]['length']} chars")
        return analysis_result
    
    def create_prompt(self, analysis: Dict) -> str:
        """Tạo prompt với VÍ DỤ CỤ THỂ về text DÀI"""
        
        # Lấy 2 mẫu dài nhất
        examples = analysis.get('long_samples', [])
        
        prompt = f"""Bạn là chuyên gia y tế. Nhiệm vụ: Tạo 3 văn bản y khoa CHI TIẾT và DÀI.

================================================================================
YÊU CẦU BẮT BUỘC:
================================================================================
1. Mỗi văn bản phải dài ÍT NHẤT 200 ký tự (khoảng 50-80 từ)
2. Phải có ĐẦY ĐỦ các phần: chẩn đoán, triệu chứng, thuốc, xét nghiệm
3. Phong cách giống như ví dụ bên dưới

================================================================================
VÍ DỤ VỀ VĂN BẢN DÀI (300+ ký tự):
================================================================================
Ví dụ 1:
"Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) đã 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch hay đột quỵ. Hiện tại bệnh nhân đang dùng Metformin 500mg uống 2 lần/ngày và Lisinopril 10mg uống 1 lần/ngày. Triệu chứng hiện tại bao gồm mệt mỏi, khát nước nhiều, tiểu nhiều, đôi khi hoa mắt chóng mặt. Kết quả xét nghiệm mới nhất: HbA1c 8.5%, Creatinine 1.2 mg/dL, Glucose máu đói 180 mg/dL. Gia đình có bố bị đái tháo đường type 2 từ năm 60 tuổi. Bệnh nhân được tư vấn điều chỉnh chế độ ăn và tăng liều Metformin."

Ví dụ 2 (từ dữ liệu thật):
{examples[0]['content'][:500] if examples else "..."}

================================================================================
VÍ DỤ VỀ JSON ĐÚNG (text phải DÀI):
================================================================================
[
    {{
        "text": "Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) đã 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch hay đột quỵ. Hiện tại bệnh nhân đang dùng Metformin 500mg uống 2 lần/ngày và Lisinopril 10mg uống 1 lần/ngày. Triệu chứng hiện tại bao gồm mệt mỏi, khát nước nhiều, tiểu nhiều, đôi khi hoa mắt chóng mặt. Kết quả xét nghiệm mới nhất: HbA1c 8.5%, Creatinine 1.2 mg/dL, Glucose máu đói 180 mg/dL. Gia đình có bố bị đái tháo đường type 2 từ năm 60 tuổi.",
        "entities": [
            {{"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]}},
            {{"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]}},
            {{"text": "Metformin 500mg", "type": "THUỐC", "start": 131, "end": 147, "assertions": ["isHistorical"], "candidates": ["6809"]}},
            {{"text": "Lisinopril 10mg", "type": "THUỐC", "start": 168, "end": 184, "assertions": ["isHistorical"], "candidates": ["314076"]}},
            {{"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 222, "end": 230, "assertions": [], "candidates": []}},
            {{"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 232, "end": 247, "assertions": [], "candidates": []}},
            {{"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 252, "end": 262, "assertions": [], "candidates": []}},
            {{"text": "HbA1c", "type": "TÊN_XÉT_NGHIỆM", "start": 302, "end": 307, "assertions": [], "candidates": []}},
            {{"text": "8.5%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 308, "end": 312, "assertions": [], "candidates": []}}
        ]
    }}
]

================================================================================
LƯU Ý:
================================================================================
- text phải dài ÍT NHẤT 200 ký tự (KHÔNG được ngắn)
- entities phải có ÍT NHẤT 5-8 thực thể
- Mỗi entity phải có start và end CHÍNH XÁC

BẮT ĐẦU JSON NGAY BÂY GIỜ (3 objects trong 1 array):
[
"""
        return prompt


# ==================== PHẦN 3: OLLAMA CLIENT ====================

class OllamaClient:
    def __init__(self, model_name="qwen2.5:7b", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def generate(self, prompt, temperature=0.7, max_tokens=4000):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def check_health(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# ==================== PHẦN 4: DATA GENERATOR ====================

class DataGenerator:
    def __init__(self, samples, analysis):
        self.samples = samples
        self.analysis = analysis
        self.ollama = OllamaClient()
        self.output_dir = Path("output")
        
    def run(self):
        print("="*60)
        print("🚀 Starting Data Generation Pipeline")
        print("="*60)
        
        if not self.ollama.check_health():
            print("❌ Cannot connect to Ollama")
            print("Please run: ollama serve")
            return []
        
        analyzer = StyleAnalyzer(self.samples)
        prompt = analyzer.create_prompt(self.analysis)
        
        with open("debug_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        print("📝 Saved prompt to debug_prompt.txt")
        
        print("🔄 Generating 3 long samples with Qwen2.5...")
        print("⏳ This may take 2-3 minutes...")
        
        response = self.ollama.generate(prompt, temperature=0.8, max_tokens=4000)
        
        with open("debug_response.txt", 'w', encoding='utf-8') as f:
            f.write(response)
        print("📝 Saved response to debug_response.txt")
        
        # Parse
        samples = self._parse_qwen_response(response)
        
        if not samples:
            print("⚠️ Parse failed, using fallback (LONG samples)")
            samples = self._create_fallback_samples()
        else:
            print(f"✅ Parsed {len(samples)} samples")
            for idx, s in enumerate(samples, 1):
                text_len = len(s.get('text', ''))
                entity_count = len(s.get('entities', []))
                print(f"   Sample {idx}: {text_len} chars, {entity_count} entities")
                if text_len < 200:
                    print(f"   ⚠️ WARNING: Sample {idx} is only {text_len} chars!")
        
        self._save_samples(samples)
        return samples
    
    def _parse_qwen_response(self, response):
        """Parse response từ Qwen"""
        
        print(f"\n📋 Response preview (first 300 chars):\n{response[:300]}\n")
        
        try:
            # Tìm JSON array
            start = response.find('[')
            if start == -1:
                print("❌ No '[' found")
                return None
            
            # Đếm ngoặc
            bracket_count = 0
            end = -1
            for i in range(start, len(response)):
                if response[i] == '[':
                    bracket_count += 1
                elif response[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if end == -1:
                print("❌ No matching ']'")
                return None
            
            json_str = response[start:end]
            print(f"📋 JSON length: {len(json_str)} chars")
            
            data = json.loads(json_str)
            
            if isinstance(data, list):
                valid_samples = []
                for item in data:
                    if isinstance(item, dict) and 'text' in item:
                        text_len = len(item.get('text', ''))
                        if 'entities' not in item:
                            item['entities'] = []
                        
                        # CHỈ chấp nhận text dài >= 150 chars
                        if text_len >= 150:
                            valid_samples.append(item)
                            print(f"✅ Valid: {text_len} chars, {len(item['entities'])} entities")
                        else:
                            print(f"⚠️ Too short: {text_len} chars")
                
                if valid_samples:
                    # Nếu có ít hơn 3, thêm fallback
                    while len(valid_samples) < 3:
                        valid_samples.append(self._create_fallback_samples()[len(valid_samples)])
                    return valid_samples[:3]
                else:
                    print("❌ No valid samples (all too short)")
                    return None
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return None
        except Exception as e:
            print(f"❌ Parse error: {e}")
            return None
    
    def _save_samples(self, samples):
        if not samples:
            print("❌ No samples to save")
            return
        
        os.makedirs(self.output_dir / "input", exist_ok=True)
        os.makedirs(self.output_dir / "output", exist_ok=True)
        
        print("\n💾 Saving samples...")
        
        for idx, sample in enumerate(samples, 1):
            text = sample.get('text', '')
            entities = sample.get('entities', [])
            
            if isinstance(entities, dict):
                entities = [entities]
            
            print(f"\n📊 Sample {idx}: {len(text)} chars, {len(entities)} entities")
            
            # Lưu .txt
            txt_path = self.output_dir / "input" / f"{idx}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ Saved {txt_path}")
            
            # Chuyển entities
            output_entities = []
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                
                entity_text = entity.get('text', '')
                if not entity_text:
                    continue
                
                start = entity.get('start', -1)
                end = entity.get('end', -1)
                
                if start == -1 or end == -1 or start >= end:
                    found = text.find(entity_text)
                    if found != -1:
                        start = found
                        end = found + len(entity_text)
                    else:
                        continue
                
                entity_type = entity.get('type', 'CHẨN_ĐOÁN')
                type_map = {
                    'bệnh': 'CHẨN_ĐOÁN',
                    'Bệnh lý': 'CHẨN_ĐOÁN',
                    'diagnosis': 'CHẨN_ĐOÁN',
                    'thuốc': 'THUỐC',
                    'drug': 'THUỐC',
                    'triệu chứng': 'TRIỆU_CHỨNG',
                    'symptom': 'TRIỆU_CHỨNG',
                    'xét nghiệm': 'TÊN_XÉT_NGHIỆM',
                }
                entity_type = type_map.get(entity_type.lower(), entity_type)
                
                output_entity = {
                    "text": entity_text,
                    "position": [start, end],
                    "type": entity_type,
                    "assertions": entity.get('assertions', []),
                    "candidates": entity.get('candidates', [])
                }
                output_entities.append(output_entity)
            
            # Lưu .json
            json_path = self.output_dir / "output" / f"{idx}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_entities, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {json_path}")
        
        print(f"\n🎉 Saved {len(samples)} samples to {self.output_dir}/")
    
    def _create_fallback_samples(self):
        """Fallback - TEXT DÀI"""
        return [
            {
                "text": """Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) đã 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch hay đột quỵ. Hiện tại bệnh nhân đang dùng Metformin 500mg uống 2 lần/ngày và Lisinopril 10mg uống 1 lần/ngày. Triệu chứng hiện tại bao gồm mệt mỏi, khát nước nhiều, tiểu nhiều, đôi khi hoa mắt chóng mặt. Kết quả xét nghiệm mới nhất: HbA1c 8.5%, Creatinine 1.2 mg/dL, Glucose máu đói 180 mg/dL. Gia đình có bố bị đái tháo đường type 2 từ năm 60 tuổi. Bệnh nhân được tư vấn điều chỉnh chế độ ăn và tăng liều Metformin. Tái khám sau 1 tháng để đánh giá đáp ứng điều trị.""",
                "entities": [
                    {"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]},
                    {"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]},
                    {"text": "Metformin 500mg", "type": "THUỐC", "start": 131, "end": 147, "assertions": ["isHistorical"], "candidates": ["6809"]},
                    {"text": "Lisinopril 10mg", "type": "THUỐC", "start": 168, "end": 184, "assertions": ["isHistorical"], "candidates": ["314076"]},
                    {"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 222, "end": 230, "assertions": [], "candidates": []},
                    {"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 232, "end": 247, "assertions": [], "candidates": []},
                    {"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 252, "end": 262, "assertions": [], "candidates": []},
                    {"text": "HbA1c", "type": "TÊN_XÉT_NGHIỆM", "start": 302, "end": 307, "assertions": [], "candidates": []},
                    {"text": "8.5%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 308, "end": 312, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": """Bệnh nhân nữ 42 tuổi, đến khám tại phòng khám hô hấp vì khó thở, ho khan, tức ngực kéo dài 1 tuần. Bệnh nhân không sốt, không có đờm, không có tiền sử hen suyễn. Tiền sử gia đình: mẹ bị hen suyễn từ nhỏ. Bệnh nhân đã được điều trị với Albuterol inhaler 2 nhát/ngày và Fluticasone 100mcg/ngày trong 3 ngày, nhưng triệu chứng không đỡ. Xét nghiệm chức năng hô hấp: FEV1 65%, FEV1/FVC 70%. Bác sĩ chẩn đoán hen suyễn khởi phát muộn và đề nghị nhập viện theo dõi. Bệnh nhân được chỉ định thêm Montelukast 10mg uống mỗi tối và theo dõi đáp ứng. Tái khám sau 2 tuần để đánh giá hiệu quả điều trị.""",
                "entities": [
                    {"text": "hen suyễn", "type": "CHẨN_ĐOÁN", "start": 197, "end": 206, "assertions": ["isFamily"], "candidates": ["J45.909"]},
                    {"text": "Albuterol inhaler", "type": "THUỐC", "start": 237, "end": 255, "assertions": ["isHistorical"], "candidates": ["432"]},
                    {"text": "Fluticasone 100mcg", "type": "THUỐC", "start": 260, "end": 279, "assertions": ["isHistorical"], "candidates": ["312938"]},
                    {"text": "Montelukast 10mg", "type": "THUỐC", "start": 416, "end": 433, "assertions": [], "candidates": ["189"]},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 51, "end": 58, "assertions": [], "candidates": []},
                    {"text": "ho khan", "type": "TRIỆU_CHỨNG", "start": 60, "end": 67, "assertions": [], "candidates": []},
                    {"text": "tức ngực", "type": "TRIỆU_CHỨNG", "start": 69, "end": 77, "assertions": [], "candidates": []},
                    {"text": "FEV1 65%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 348, "end": 357, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": """Bệnh nhân nam 55 tuổi, nhập viện cấp cứu vì sốt cao 39.5°C, ho có đờm xanh, khó thở tăng dần trong 3 ngày. Bệnh nhân có tiền sử hút thuốc lá 30 năm, không có tiền sử bệnh phổi mạn tính. Kết quả xét nghiệm máu: WBC 18.5 x10^9/L, NEUT% 85%, CRP 120 mg/L. X-quang ngực cho thấy đông đặc thùy phổi phải. Bệnh nhân được chẩn đoán viêm phổi cộng đồng (J18.9) và điều trị khởi đầu với Amoxicillin 500mg tiêm tĩnh mạch mỗi 6 giờ kèm theo Oseltamivir 75mg uống 2 lần/ngày. Bệnh nhân được theo dõi sát và chăm sóc hô hấp tích cực. Các chỉ số sinh tồn ổn định sau 24 giờ điều trị. Dự kiến xuất viện sau 5-7 ngày nếu tiến triển tốt.""",
                "entities": [
                    {"text": "viêm phổi cộng đồng", "type": "CHẨN_ĐOÁN", "start": 376, "end": 396, "assertions": [], "candidates": ["J18.9"]},
                    {"text": "Amoxicillin 500mg", "type": "THUỐC", "start": 420, "end": 438, "assertions": [], "candidates": ["723"]},
                    {"text": "Oseltamivir 75mg", "type": "THUỐC", "start": 465, "end": 483, "assertions": [], "candidates": ["3605"]},
                    {"text": "sốt cao 39.5°C", "type": "TRIỆU_CHỨNG", "start": 30, "end": 43, "assertions": [], "candidates": []},
                    {"text": "ho có đờm xanh", "type": "TRIỆU_CHỨNG", "start": 45, "end": 61, "assertions": [], "candidates": []},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 63, "end": 70, "assertions": [], "candidates": []},
                    {"text": "WBC", "type": "TÊN_XÉT_NGHIỆM", "start": 166, "end": 169, "assertions": [], "candidates": []},
                    {"text": "18.5 x10^9/L", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 170, "end": 183, "assertions": [], "candidates": []},
                    {"text": "NEUT% 85%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 185, "end": 195, "assertions": [], "candidates": []},
                    {"text": "CRP 120 mg/L", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 197, "end": 210, "assertions": [], "candidates": []}
                ]
            }
        ]


# ==================== PHẦN 5: MAIN ====================

def main():
    print("="*60)
    print("🎯 SYNTHETIC DATA GENERATOR - FINAL FIX")
    print("="*60)
    print()
    
    extractor = DataExtractor("data/input_turn2_vong1.zip")
    samples = extractor.extract_and_read()
    
    if not samples:
        print("\n❌ Không thể đọc dữ liệu.")
        return
    
    analyzer = StyleAnalyzer(samples)
    analysis = analyzer.analyze()
    
    generator = DataGenerator(samples, analysis)
    generated = generator.run()
    
    extractor.cleanup()
    
    print("\n" + "="*60)
    print("🎉 HOÀN THÀNH!")
    print("="*60)
    if generated:
        print(f"📂 Output: {generator.output_dir}/")
        for i in range(1, 4):
            txt_path = generator.output_dir / "input" / f"{i}.txt"
            if txt_path.exists():
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"   Sample {i}: {len(content)} chars")
        print("\n📝 Debug files: debug_prompt.txt, debug_response.txt")


if __name__ == "__main__":
    main()