"""
SYNTHETIC DATA GENERATOR FOR MEDICAL NLP - IMPROVED VERSION
Tạo 3 file dữ liệu tổng hợp chất lượng cao có nhãn
Sử dụng Qwen2.5 qua Ollama

Cách chạy:
    python generate_synthetic_data.py

Yêu cầu:
    - Ollama đang chạy: ollama serve
    - File dữ liệu: data/input_turn2_vong1.zip
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
    """Giải nén và đọc dữ liệu từ file zip"""
    
    def __init__(self, zip_path="data/input_turn2_vong1.zip"):
        self.zip_path = Path(zip_path)
        self.extract_dir = Path("temp_extracted")
        self.samples = []
        
    def extract_and_read(self) -> List[Dict]:
        """Giải nén file zip và đọc tất cả file txt"""
        
        if not self.zip_path.exists():
            print(f"❌ File not found: {self.zip_path}")
            print(f"📂 Current directory: {os.getcwd()}")
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
        
        # Tìm thư mục input
        input_dir = self.extract_dir / "input"
        if not input_dir.exists():
            possible_dirs = list(self.extract_dir.glob("*/input"))
            if possible_dirs:
                input_dir = possible_dirs[0]
            else:
                print(f"❌ Cannot find 'input' directory")
                return []
        
        # Đọc tất cả file .txt
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
        
        # Hiển thị mẫu đầu tiên
        if self.samples:
            print(f"\n📝 First sample preview:")
            print(f"Content: {self.samples[0]['content'][:300]}...")
            print(f"Length: {self.samples[0]['length']} chars, {self.samples[0]['word_count']} words")
        
        return self.samples
    
    def cleanup(self):
        if self.extract_dir.exists():
            shutil.rmtree(self.extract_dir)
            print("🧹 Cleaned up temp directory")


# ==================== PHẦN 2: PHÂN TÍCH PHONG CÁCH ====================

class StyleAnalyzer:
    """Phân tích phong cách từ 100 file và tạo prompt"""
    
    def __init__(self, samples: List[Dict]):
        self.samples = samples
        
    def analyze(self) -> Dict:
        """Phân tích toàn diện các file"""
        if not self.samples:
            return {}
        
        print("🔍 Analyzing 100 files...")
        
        # 1. Phân tích từ vựng
        all_words = []
        for sample in self.samples:
            all_words.extend(sample['content'].split())
        word_freq = Counter(all_words)
        common_words = word_freq.most_common(20)
        
        # 2. Phân tích cấu trúc
        structures = self._analyze_structures()
        
        # 3. Phân tích loại thông tin
        info_types = self._analyze_info_types()
        
        # 4. Lấy 10 mẫu dài nhất để làm ví dụ
        sorted_samples = sorted(self.samples, key=lambda x: x['length'], reverse=True)
        long_samples = sorted_samples[:5]
        
        analysis_result = {
            'total_files': len(self.samples),
            'avg_length': sum(s['length'] for s in self.samples) / len(self.samples),
            'avg_words': sum(s['word_count'] for s in self.samples) / len(self.samples),
            'max_length': max(s['length'] for s in self.samples),
            'min_length': min(s['length'] for s in self.samples),
            'common_words': common_words[:10],
            'structures': structures,
            'info_types': info_types,
            'long_samples': long_samples
        }
        
        print("✅ Analysis complete")
        print(f"📊 Average length: {analysis_result['avg_length']:.0f} chars")
        print(f"📊 Max length: {analysis_result['max_length']} chars")
        return analysis_result
    
    def _analyze_structures(self) -> Dict:
        """Phân tích cấu trúc văn bản"""
        structures = {
            'has_diagnosis': 0, 'has_symptoms': 0, 'has_medication': 0,
            'has_lab': 0, 'has_history': 0, 'has_family': 0, 'has_negation': 0,
            'has_lab_values': 0
        }
        
        diagnosis_keywords = ['chẩn đoán', 'mắc bệnh', 'được chẩn đoán', 'diagnosed', 'bị', 'mắc']
        symptom_keywords = ['ho', 'sốt', 'đau', 'mệt', 'khó thở', 'buồn nôn', 'tức ngực', 'triệu chứng', 'đờm']
        medication_keywords = ['thuốc', 'uống', 'dùng', 'điều trị', 'medication', 'mg', 'ml']
        lab_keywords = ['xét nghiệm', 'kết quả', 'WBC', 'Hb', 'NEUT', 'LYMPH', 'Hct']
        history_keywords = ['tiền sử', 'trước đây', 'đã từng', 'có tiền sử', 'history', 'từ nhỏ']
        family_keywords = ['gia đình', 'bố', 'mẹ', 'anh', 'chị', 'em', 'người nhà', 'họ hàng']
        negation_keywords = ['không', 'chưa', 'không có', 'không thấy', 'không ghi nhận']
        lab_values = ['\d+[,.]\d+', '\d+%']
        
        for sample in self.samples:
            content = sample['content'].lower()
            if any(kw in content for kw in diagnosis_keywords): structures['has_diagnosis'] += 1
            if any(kw in content for kw in symptom_keywords): structures['has_symptoms'] += 1
            if any(kw in content for kw in medication_keywords): structures['has_medication'] += 1
            if any(kw in content for kw in lab_keywords): structures['has_lab'] += 1
            if any(kw in content for kw in history_keywords): structures['has_history'] += 1
            if any(kw in content for kw in family_keywords): structures['has_family'] += 1
            if any(kw in content for kw in negation_keywords): structures['has_negation'] += 1
            if any(re.search(p, content) for p in lab_values): structures['has_lab_values'] += 1
        
        total = len(self.samples)
        for key in structures:
            structures[key] = round((structures[key] / total) * 100, 1)
        
        return structures
    
    def _analyze_info_types(self) -> Dict:
        """Phân tích loại thông tin"""
        info_types = {'has_icd': 0, 'has_rxnorm': 0, 'has_lab_values': 0, 'has_dosage': 0}
        
        for sample in self.samples:
            content = sample['content']
            if 'ICD' in content or 'ICD-10' in content: info_types['has_icd'] += 1
            if 'RxNorm' in content or 'Rx' in content: info_types['has_rxnorm'] += 1
            if re.search(r'\d+[,.]\d+', content): info_types['has_lab_values'] += 1
            if re.search(r'\d+\s*mg', content): info_types['has_dosage'] += 1
        
        total = len(self.samples)
        for key in info_types:
            info_types[key] = round((info_types[key] / total) * 100, 1)
        
        return info_types
    
    def create_prompt(self, analysis: Dict, num_to_generate: int = 3) -> str:
        """Tạo prompt chi tiết cho Qwen"""
        
        # Lấy 3 mẫu dài nhất làm ví dụ
        few_shot = analysis.get('long_samples', [])[:3]
        if len(few_shot) < 3:
            few_shot = random.sample(self.samples, min(3, len(self.samples)))
        
        prompt = f"""Bạn là chuyên gia y tế, cần tạo dữ liệu tổng hợp CHẤT LƯỢNG CAO cho bài toán xử lý văn bản y khoa.

THÔNG TIN VỀ 100 FILE MẪU:
- Tổng số: {analysis['total_files']} file
- Độ dài TB: {analysis['avg_length']:.0f} ký tự (tối thiểu {analysis['min_length']}, tối đa {analysis['max_length']})
- Số từ TB: {analysis['avg_words']:.0f} từ

CẤU TRÚC THƯỜNG GẶP (tỉ lệ %):
"""
        for key, value in analysis.get('structures', {}).items():
            if value > 20:
                prompt += f"- {value:.1f}% có {key.replace('_', ' ')}\n"
        
        prompt += f"""

VÍ DỤ MẪU CHI TIẾT (từ dữ liệu thật, đã được gán nhãn):
"""
        for idx, sample in enumerate(few_shot, 1):
            prompt += f"\n--- MẪU {idx} (dài {sample['length']} ký tự) ---\n"
            prompt += f"{sample['content']}\n"
        
        prompt += f"""

{"="*60}
YÊU CẦU SINH {num_to_generate} VĂN BẢN Y KHOA MỚI CHẤT LƯỢNG CAO:
{"="*60}

MỖI văn bản phải:
1. Dài TỐI THIỂU 100-150 từ hoặc 300-500 ký tự
2. Có CẤU TRÚC TƯƠNG TỰ file mẫu
3. Bao gồm ĐẦY ĐỦ các thông tin:
   - CHẨN_ĐOÁN (có mã ICD-10)
   - THUỐC điều trị (có mã RxNorm)
   - TRIỆU_CHỨNG chi tiết
   - TÊN_XÉT_NGHIỆM và KẾT_QUẢ_XÉT_NGHIỆM (nếu có)
   - Các assertion: isHistorical, isFamily, isNegated (nếu phù hợp)
4. Nội dung y tế CHÍNH XÁC và ĐA DẠNG
5. Phong cách viết TỰ NHIÊN như bác sĩ viết

VÍ DỤ VỀ ANNOTATION ĐÚNG CHO MỘT VĂN BẢN DÀI:

Input text:
"Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch. Hiện tại bệnh nhân đang dùng Metformin 500mg và Lisinopril 10mg. Triệu chứng: mệt mỏi, khát nước nhiều, tiểu nhiều. Kết quả xét nghiệm: HbA1c 8.5%, Creatinine 1.2 mg/dL. Gia đình có bố bị đái tháo đường."

Entities (phải liệt kê ĐẦY ĐỦ):
[
    {{"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]}},
    {{"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]}},
    {{"text": "Metformin 500mg", "type": "THUỐC", "start": 129, "end": 145, "assertions": ["isHistorical"], "candidates": ["6809"]}},
    {{"text": "Lisinopril 10mg", "type": "THUỐC", "start": 150, "end": 166, "assertions": ["isHistorical"], "candidates": ["314076"]}},
    {{"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 184, "end": 192, "assertions": [], "candidates": []}},
    {{"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 194, "end": 209, "assertions": [], "candidates": []}},
    {{"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 214, "end": 224, "assertions": [], "candidates": []}},
    {{"text": "HbA1c", "type": "TÊN_XÉT_NGHIỆM", "start": 242, "end": 247, "assertions": [], "candidates": []}},
    {{"text": "8.5%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 248, "end": 252, "assertions": [], "candidates": []}},
    {{"text": "Creatinine", "type": "TÊN_XÉT_NGHIỆM", "start": 254, "end": 264, "assertions": [], "candidates": []}},
    {{"text": "1.2 mg/dL", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 265, "end": 275, "assertions": [], "candidates": []}}
]

LƯU Ý QUAN TRỌNG:
1. Mỗi văn bản phải có ÍT NHẤT 5-8 entities
2. Phải có ít nhất 2 loại entity khác nhau
3. start và end phải là vị trí CHÍNH XÁC trong text
4. candidates: dùng mã ICD-10 cho CHẨN_ĐOÁN, mã RxNorm cho THUỐC

BẮT ĐẦU JSON NGAY BÂY GIỜ (KHÔNG giải thích thêm):
[
"""
        return prompt


# ==================== PHẦN 3: GỌI OLLAMA ====================

class OllamaClient:
    """Client kết nối Ollama"""
    
    def __init__(self, model_name="qwen2.5:7b", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def generate(self, prompt, temperature=0.7, max_tokens=3000):
        """Gọi Ollama sinh text"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "stop": ["```", "```json"]
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.Timeout:
            print("⏰ Timeout, retrying...")
            time.sleep(3)
            return self.generate(prompt, temperature, max_tokens)
        except Exception as e:
            print(f"❌ Error: {e}")
            return ""
    
    def check_health(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


# ==================== PHẦN 4: SINH VÀ LƯU DỮ LIỆU ====================

class DataGenerator:
    """Sinh và lưu 3 file dữ liệu mới"""
    
    def __init__(self, samples, analysis):
        self.samples = samples
        self.analysis = analysis
        self.ollama = OllamaClient()
        self.output_dir = Path("output")
        self.debug_response = None
        
    def run(self):
        """Chạy toàn bộ quy trình"""
        print("="*60)
        print("🚀 Starting Data Generation Pipeline")
        print("="*60)
        
        # Kiểm tra Ollama
        if not self.ollama.check_health():
            print("❌ Cannot connect to Ollama")
            print("Please run: ollama serve")
            return []
        
        # Tạo prompt
        analyzer = StyleAnalyzer(self.samples)
        prompt = analyzer.create_prompt(self.analysis, num_to_generate=3)
        
        # Lưu prompt để debug
        with open("debug_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        print("📝 Saved prompt to debug_prompt.txt")
        
        print("🔄 Generating 3 high-quality samples with Qwen2.5...")
        print("⏳ This may take 2-3 minutes...")
        
        # Sinh dữ liệu
        response = self.ollama.generate(prompt, temperature=0.8, max_tokens=3000)
        self.debug_response = response
        
        # Lưu response để debug
        with open("debug_response.txt", 'w', encoding='utf-8') as f:
            f.write(response)
        print("📝 Saved response to debug_response.txt")
        
        if not response:
            print("❌ No response from Ollama")
            print("Using fallback samples...")
            samples = self._create_fallback_samples()
        else:
            # Thử parse
            samples = self._parse_response_improved(response)
            if not samples:
                print("⚠️ Parse failed, using fallback")
                samples = self._create_fallback_samples()
            else:
                print(f"✅ Successfully generated {len(samples)} samples")
                # Hiển thị thông tin samples
                for idx, s in enumerate(samples, 1):
                    print(f"   Sample {idx}: {len(s.get('text', ''))} chars, {len(s.get('entities', []))} entities")
        
        # Lưu samples
        self._save_samples(samples)
        
        return samples
    
    def _parse_response_improved(self, response):
        """Parse JSON từ response - cải thiện"""
        
        # Thử các cách khác nhau
        strategies = [
            self._extract_json_array,
            self._extract_multiple_objects,
            self._extract_json_object,
        ]
        
        for strategy in strategies:
            result = strategy(response)
            if result:
                # Kiểm tra chất lượng
                valid = [s for s in result if len(s.get('text', '')) > 100 and len(s.get('entities', [])) >= 3]
                if valid:
                    return valid[:3]
        
        print("❌ All parsing strategies failed or samples too short")
        print(f"Response preview: {response[:500]}...")
        return None
    
    def _extract_json_array(self, text):
        """Tìm JSON array [...]"""
        try:
            start = text.find('[')
            if start == -1:
                return None
            
            bracket_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '[':
                    bracket_count += 1
                elif text[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if end == -1:
                return None
            
            json_str = text[start:end]
            data = json.loads(json_str)
            
            if isinstance(data, list) and len(data) > 0:
                valid_samples = []
                for item in data[:3]:
                    if isinstance(item, dict) and 'text' in item:
                        if 'entities' not in item:
                            item['entities'] = []
                        # Kiểm tra độ dài
                        if len(item.get('text', '')) > 100:
                            valid_samples.append(item)
                        else:
                            print(f"⚠️ Sample too short: {len(item.get('text', ''))} chars")
                return valid_samples[:3] if valid_samples else None
            
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return None
    
    def _extract_json_object(self, text):
        """Tìm JSON object {...}"""
        try:
            start = text.find('{')
            if start == -1:
                return None
            
            bracket_count = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    bracket_count += 1
                elif text[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if end == -1:
                return None
            
            json_str = text[start:end]
            data = json.loads(json_str)
            
            if isinstance(data, dict) and 'text' in data:
                if 'entities' not in data:
                    data['entities'] = []
                if len(data.get('text', '')) > 100:
                    return [data]
            return None
        except:
            return None
    
    def _extract_multiple_objects(self, text):
        """Tìm nhiều JSON object trong text"""
        try:
            objects = []
            in_object = False
            current = ""
            brace_count = 0
            
            for char in text:
                if char == '{':
                    if not in_object:
                        in_object = True
                        current = ""
                    brace_count += 1
                    current += char
                elif char == '}':
                    brace_count -= 1
                    current += char
                    if brace_count == 0 and in_object:
                        try:
                            data = json.loads(current)
                            if 'text' in data:
                                if 'entities' not in data:
                                    data['entities'] = []
                                if len(data.get('text', '')) > 100:
                                    objects.append(data)
                        except:
                            pass
                        in_object = False
                        current = ""
                elif in_object:
                    current += char
            
            return objects[:3] if objects else None
        except:
            return None
    
    def _save_samples(self, samples):
        """Lưu samples vào file"""
        if not samples:
            print("❌ No samples to save")
            return
        
        # Tạo thư mục
        os.makedirs(self.output_dir / "input", exist_ok=True)
        os.makedirs(self.output_dir / "output", exist_ok=True)
        
        print("\n💾 Saving samples...")
        
        for idx, sample in enumerate(samples, 1):
            text = sample.get('text', '')
            entities = sample.get('entities', [])
            
            # Kiểm tra chất lượng
            print(f"\n📊 Sample {idx}:")
            print(f"   Text length: {len(text)} chars")
            print(f"   Entities: {len(entities)}")
            
            # Lưu .txt
            txt_path = self.output_dir / "input" / f"{idx}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ Saved {txt_path}")
            
            # Chuyển entities sang format bài toán
            output_entities = []
            for entity in entities:
                # Đảm bảo có text
                entity_text = entity.get('text', '')
                if not entity_text:
                    continue
                
                # Tìm vị trí nếu chưa có
                start = entity.get('start', 0)
                end = entity.get('end', len(entity_text))
                
                # Nếu start/end không hợp lệ, tìm trong text
                if start >= end or start < 0 or end > len(text):
                    found = text.find(entity_text)
                    if found != -1:
                        start = found
                        end = found + len(entity_text)
                    else:
                        # Nếu không tìm thấy, bỏ qua entity
                        continue
                
                output_entity = {
                    "text": entity_text,
                    "position": [start, end],
                    "type": entity.get('type', 'CHẨN_ĐOÁN'),
                    "assertions": entity.get('assertions', []),
                    "candidates": entity.get('candidates', [])
                }
                output_entities.append(output_entity)
            
            # Lưu .json
            json_path = self.output_dir / "output" / f"{idx}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_entities, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {json_path}")
        
        print(f"\n🎉 Successfully saved {len(samples)} samples to {self.output_dir}/")
    
    def _create_fallback_samples(self):
        """Tạo sample thủ công chất lượng cao"""
        return [
            {
                "text": """Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) đã 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch hay đột quỵ. Hiện tại bệnh nhân đang dùng Metformin 500mg uống 2 lần/ngày và Lisinopril 10mg uống 1 lần/ngày. Triệu chứng hiện tại bao gồm mệt mỏi, khát nước nhiều, tiểu nhiều, đôi khi hoa mắt chóng mặt. Kết quả xét nghiệm mới nhất: HbA1c 8.5%, Creatinine 1.2 mg/dL, Glucose máu đói 180 mg/dL. Gia đình có bố bị đái tháo đường type 2 từ năm 60 tuổi. Bệnh nhân được tư vấn điều chỉnh chế độ ăn và tăng liều Metformin.""",
                "entities": [
                    {"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]},
                    {"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]},
                    {"text": "Metformin 500mg", "type": "THUỐC", "start": 131, "end": 147, "assertions": ["isHistorical"], "candidates": ["6809"]},
                    {"text": "Lisinopril 10mg", "type": "THUỐC", "start": 168, "end": 184, "assertions": ["isHistorical"], "candidates": ["314076"]},
                    {"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 222, "end": 230, "assertions": [], "candidates": []},
                    {"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 232, "end": 247, "assertions": [], "candidates": []},
                    {"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 252, "end": 262, "assertions": [], "candidates": []},
                    {"text": "HbA1c", "type": "TÊN_XÉT_NGHIỆM", "start": 302, "end": 307, "assertions": [], "candidates": []},
                    {"text": "8.5%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 308, "end": 312, "assertions": [], "candidates": []},
                    {"text": "Creatinine", "type": "TÊN_XÉT_NGHIỆM", "start": 314, "end": 324, "assertions": [], "candidates": []},
                    {"text": "1.2 mg/dL", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 325, "end": 335, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": """Bệnh nhân nữ 42 tuổi, đến khám tại phòng khám hô hấp vì khó thở, ho khan, tức ngực kéo dài 1 tuần. Bệnh nhân không sốt, không có đờm, không có tiền sử hen suyễn. Tiền sử gia đình: mẹ bị hen suyễn từ nhỏ. Bệnh nhân đã được điều trị với Albuterol inhaler 2 nhát/ngày và Fluticasone 100mcg/ngày trong 3 ngày, nhưng triệu chứng không đỡ. Xét nghiệm chức năng hô hấp: FEV1 65%, FEV1/FVC 70%. Bác sĩ chẩn đoán hen suyễn khởi phát muộn và đề nghị nhập viện theo dõi.""",
                "entities": [
                    {"text": "hen suyễn", "type": "CHẨN_ĐOÁN", "start": 198, "end": 207, "assertions": ["isFamily"], "candidates": ["J45.909"]},
                    {"text": "Albuterol inhaler", "type": "THUỐC", "start": 238, "end": 256, "assertions": ["isHistorical"], "candidates": ["432"]},
                    {"text": "Fluticasone 100mcg", "type": "THUỐC", "start": 261, "end": 280, "assertions": ["isHistorical"], "candidates": ["312938"]},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 51, "end": 58, "assertions": [], "candidates": []},
                    {"text": "ho khan", "type": "TRIỆU_CHỨNG", "start": 60, "end": 67, "assertions": [], "candidates": []},
                    {"text": "tức ngực", "type": "TRIỆU_CHỨNG", "start": 69, "end": 77, "assertions": [], "candidates": []},
                    {"text": "FEV1 65%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 349, "end": 358, "assertions": [], "candidates": []},
                    {"text": "FEV1/FVC 70%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 360, "end": 373, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": """Bệnh nhân nam 55 tuổi, nhập viện cấp cứu vì sốt cao 39.5°C, ho có đờm xanh, khó thở tăng dần trong 3 ngày. Bệnh nhân có tiền sử hút thuốc lá 30 năm, không có tiền sử bệnh phổi mạn tính. Kết quả xét nghiệm máu: WBC 18.5 x10^9/L, NEUT% 85%, CRP 120 mg/L. X-quang ngực cho thấy đông đặc thùy phổi phải. Bệnh nhân được chẩn đoán viêm phổi cộng đồng (J18.9) và điều trị khởi đầu với Amoxicillin 500mg tiêm tĩnh mạch mỗi 6 giờ kèm theo Oseltamivir 75mg uống 2 lần/ngày. Bệnh nhân được theo dõi sát và chăm sóc hô hấp tích cực.""",
                "entities": [
                    {"text": "viêm phổi cộng đồng", "type": "CHẨN_ĐOÁN", "start": 376, "end": 396, "assertions": [], "candidates": ["J18.9"]},
                    {"text": "Amoxicillin 500mg", "type": "THUỐC", "start": 420, "end": 438, "assertions": [], "candidates": ["723"]},
                    {"text": "Oseltamivir 75mg", "type": "THUỐC", "start": 465, "end": 483, "assertions": [], "candidates": ["3605"]},
                    {"text": "sốt cao 39.5°C", "type": "TRIỆU_CHỨNG", "start": 30, "end": 43, "assertions": [], "candidates": []},
                    {"text": "ho có đờm xanh", "type": "TRIỆU_CHỨNG", "start": 45, "end": 61, "assertions": [], "candidates": []},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 63, "end": 70, "assertions": [], "candidates": []},
                    {"text": "WBC", "type": "TÊN_XÉT_NGHIỆM", "start": 164, "end": 167, "assertions": [], "candidates": []},
                    {"text": "18.5 x10^9/L", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 168, "end": 181, "assertions": [], "candidates": []},
                    {"text": "NEUT% 85%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 183, "end": 193, "assertions": [], "candidates": []},
                    {"text": "CRP 120 mg/L", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 195, "end": 208, "assertions": [], "candidates": []}
                ]
            }
        ]


# ==================== PHẦN 5: MAIN ====================

def main():
    print("="*60)
    print("🎯 SYNTHETIC DATA GENERATOR FOR MEDICAL NLP")
    print("📊 Tạo 3 file dữ liệu CHẤT LƯỢNG CAO có nhãn")
    print("="*60)
    print()
    
    # 1. Đọc dữ liệu từ zip
    extractor = DataExtractor("data/input_turn2_vong1.zip")
    samples = extractor.extract_and_read()
    
    if not samples:
        print("\n❌ Không thể đọc dữ liệu. Kiểm tra:")
        print("1. File path: data/input_turn2_vong1.zip")
        print("2. File tồn tại và hợp lệ")
        return
    
    # 2. Phân tích
    analyzer = StyleAnalyzer(samples)
    analysis = analyzer.analyze()
    
    # 3. Sinh 3 sample mới
    generator = DataGenerator(samples, analysis)
    generated = generator.run()
    
    # 4. Dọn dẹp
    extractor.cleanup()
    
    print("\n" + "="*60)
    print("🎉 HOÀN THÀNH!")
    print("="*60)
    if generated:
        print(f"📂 Output: {generator.output_dir}/")
        print("📄 Các file đã tạo:")
        print("   - input/1.txt, 2.txt, 3.txt")
        print("   - output/1.json, 2.json, 3.json")
        print("\n📝 Debug files:")
        print("   - debug_prompt.txt (prompt gửi cho Qwen)")
        print("   - debug_response.txt (response từ Qwen)")
        print("\n✅ Bạn có thể dùng 3 file này làm dữ liệu huấn luyện!")
        print("\n💡 Nếu dữ liệu vẫn ngắn, hãy xem debug_response.txt để biết Qwen trả về gì")
    else:
        print("❌ Không tạo được dữ liệu. Kiểm tra Ollama.")


if __name__ == "__main__":
    main()