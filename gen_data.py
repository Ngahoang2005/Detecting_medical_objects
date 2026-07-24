"""
SYNTHETIC DATA GENERATOR FOR MEDICAL NLP - FIXED PARSING
Tạo 3 file dữ liệu tổng hợp chất lượng cao có nhãn
Sử dụng Qwen2.5 qua Ollama

Cách chạy:
    python generate_synthetic_data.py
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
        if not self.samples:
            return {}
        
        print("🔍 Analyzing 100 files...")
        
        all_words = []
        for sample in self.samples:
            all_words.extend(sample['content'].split())
        word_freq = Counter(all_words)
        common_words = word_freq.most_common(20)
        
        structures = self._analyze_structures()
        info_types = self._analyze_info_types()
        
        # Lấy 3 mẫu dài nhất
        sorted_samples = sorted(self.samples, key=lambda x: x['length'], reverse=True)
        long_samples = sorted_samples[:3]
        
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
        structures = {
            'has_diagnosis': 0, 'has_symptoms': 0, 'has_medication': 0,
            'has_lab': 0, 'has_history': 0, 'has_family': 0, 'has_negation': 0
        }
        
        diagnosis_keywords = ['chẩn đoán', 'mắc bệnh', 'được chẩn đoán', 'bị', 'mắc']
        symptom_keywords = ['ho', 'sốt', 'đau', 'mệt', 'khó thở', 'buồn nôn', 'tức ngực', 'triệu chứng']
        medication_keywords = ['thuốc', 'uống', 'dùng', 'điều trị', 'mg', 'ml']
        lab_keywords = ['xét nghiệm', 'kết quả', 'WBC', 'Hb', 'NEUT', 'LYMPH']
        history_keywords = ['tiền sử', 'trước đây', 'đã từng', 'có tiền sử', 'từ nhỏ']
        family_keywords = ['gia đình', 'bố', 'mẹ', 'anh', 'chị', 'em', 'người nhà']
        negation_keywords = ['không', 'chưa', 'không có', 'không thấy']
        
        for sample in self.samples:
            content = sample['content'].lower()
            if any(kw in content for kw in diagnosis_keywords): structures['has_diagnosis'] += 1
            if any(kw in content for kw in symptom_keywords): structures['has_symptoms'] += 1
            if any(kw in content for kw in medication_keywords): structures['has_medication'] += 1
            if any(kw in content for kw in lab_keywords): structures['has_lab'] += 1
            if any(kw in content for kw in history_keywords): structures['has_history'] += 1
            if any(kw in content for kw in family_keywords): structures['has_family'] += 1
            if any(kw in content for kw in negation_keywords): structures['has_negation'] += 1
        
        total = len(self.samples)
        for key in structures:
            structures[key] = round((structures[key] / total) * 100, 1)
        
        return structures
    
    def _analyze_info_types(self) -> Dict:
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
        """Tạo prompt với format rõ ràng"""
        
        few_shot = analysis.get('long_samples', [])[:3]
        if len(few_shot) < 3:
            few_shot = random.sample(self.samples, min(3, len(self.samples)))
        
        prompt = f"""Bạn là chuyên gia y tế, cần tạo dữ liệu tổng hợp chất lượng cao.

THÔNG TIN VỀ 100 FILE MẪU:
- Độ dài TB: {analysis['avg_length']:.0f} ký tự
- Số từ TB: {analysis['avg_words']:.0f} từ

VÍ DỤ MẪU:
"""
        for idx, sample in enumerate(few_shot, 1):
            prompt += f"\n--- MẪU {idx} ---\n{sample['content'][:500]}...\n"

        prompt += f"""

{"="*60}
YÊU CẦU SINH 3 VĂN BẢN MỚI:
{"="*60}

Mỗi văn bản phải:
1. Dài ~200-500 ký tự
2. Có cấu trúc tương tự mẫu
3. Bao gồm: CHẨN_ĐOÁN, THUỐC, TRIỆU_CHỨNG, XÉT_NGHIỆM (nếu có)
4. Có các assertion: isHistorical, isFamily, isNegated (nếu phù hợp)

{"="*60}
FORMAT JSON BẮT BUỘC - MỖI VĂN BẢN LÀ 1 OBJECT:
{"="*60}

[
    {{
        "text": "Nội dung văn bản y khoa đầy đủ ở đây...",
        "entities": [
            {{
                "text": "tên khái niệm (chính xác)",
                "type": "CHẨN_ĐOÁN",
                "start": 10,
                "end": 25,
                "assertions": ["isHistorical"],
                "candidates": ["E11.9"]
            }},
            {{
                "text": "tên thuốc",
                "type": "THUỐC",
                "start": 30,
                "end": 45,
                "assertions": [],
                "candidates": ["6809"]
            }},
            {{
                "text": "triệu chứng",
                "type": "TRIỆU_CHỨNG",
                "start": 50,
                "end": 60,
                "assertions": [],
                "candidates": []
            }}
        ]
    }},
    {{...}},
    {{...}}
]

{"="*60}
VÍ DỤ CỤ THỂ:
{"="*60}

{{
    "text": "Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) 5 năm. Hiện tại đang dùng Metformin 500mg và Lisinopril 10mg. Triệu chứng: mệt mỏi, khát nước nhiều, tiểu nhiều. Kết quả xét nghiệm: HbA1c 8.5%.",
    "entities": [
        {{"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]}},
        {{"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]}},
        {{"text": "Metformin 500mg", "type": "THUỐC", "start": 94, "end": 110, "assertions": ["isHistorical"], "candidates": ["6809"]}},
        {{"text": "Lisinopril 10mg", "type": "THUỐC", "start": 115, "end": 131, "assertions": ["isHistorical"], "candidates": ["314076"]}},
        {{"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 144, "end": 152, "assertions": [], "candidates": []}},
        {{"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 154, "end": 169, "assertions": [], "candidates": []}},
        {{"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 174, "end": 184, "assertions": [], "candidates": []}},
        {{"text": "HbA1c", "type": "TÊN_XÉT_NGHIỆM", "start": 210, "end": 215, "assertions": [], "candidates": []}},
        {{"text": "8.5%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 216, "end": 220, "assertions": [], "candidates": []}}
    ]
}}

{"="*60}
BẮT ĐẦU JSON NGAY BÂY GIỜ (CHỈ JSON, KHÔNG GIẢI THÍCH):
{"="*60}

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
        
    def run(self):
        print("="*60)
        print("🚀 Starting Data Generation Pipeline")
        print("="*60)
        
        if not self.ollama.check_health():
            print("❌ Cannot connect to Ollama")
            print("Please run: ollama serve")
            return []
        
        analyzer = StyleAnalyzer(self.samples)
        prompt = analyzer.create_prompt(self.analysis, num_to_generate=3)
        
        with open("debug_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        print("📝 Saved prompt to debug_prompt.txt")
        
        print("🔄 Generating 3 high-quality samples...")
        print("⏳ This may take 2-3 minutes...")
        
        response = self.ollama.generate(prompt, temperature=0.8, max_tokens=3000)
        
        with open("debug_response.txt", 'w', encoding='utf-8') as f:
            f.write(response)
        print("📝 Saved response to debug_response.txt")
        
        # Parse response - THỬ NHIỀU CÁCH
        samples = self._parse_response_advanced(response)
        
        if not samples:
            print("⚠️ Parse failed, using fallback samples")
            samples = self._create_fallback_samples()
        else:
            print(f"✅ Successfully parsed {len(samples)} samples")
            for idx, s in enumerate(samples, 1):
                print(f"   Sample {idx}: {len(s.get('text', ''))} chars, {len(s.get('entities', []))} entities")
        
        self._save_samples(samples)
        return samples
    
    def _parse_response_advanced(self, response):
        """Parse response với nhiều chiến lược"""
        
        # Chiến lược 1: Tìm JSON array
        result = self._parse_json_array(response)
        if result:
            return result
        
        # Chiến lược 2: Tìm các object riêng lẻ và ghép lại
        result = self._parse_individual_objects(response)
        if result:
            return result
        
        # Chiến lược 3: Tìm text và tự tạo entities
        result = self._parse_text_only(response)
        if result:
            return result
        
        return None
    
    def _parse_json_array(self, response):
        """Tìm và parse JSON array [...]"""
        try:
            # Tìm vị trí của [
            start = response.find('[')
            if start == -1:
                return None
            
            # Tìm vị trí của ] đóng
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
                return None
            
            json_str = response[start:end]
            data = json.loads(json_str)
            
            # Kiểm tra data là list các object
            if isinstance(data, list):
                valid_samples = []
                for item in data:
                    if isinstance(item, dict):
                        # Nếu có 'text' và 'entities'
                        if 'text' in item:
                            if 'entities' not in item:
                                item['entities'] = []
                            if len(item.get('text', '')) > 50:
                                valid_samples.append(item)
                        # Nếu là entity riêng lẻ (format sai)
                        elif 'type' in item and 'text' in item:
                            # Tạo text từ các entity
                            text_parts = []
                            entities = []
                            for e in data:
                                if 'text' in e:
                                    text_parts.append(e['text'])
                                    entities.append(e)
                            if text_parts:
                                return [{
                                    'text': '. '.join(text_parts[:3]),
                                    'entities': entities
                                }]
                
                if valid_samples:
                    return valid_samples[:3]
            
            return None
        except Exception as e:
            print(f"⚠️ JSON array parse error: {e}")
            return None
    
    def _parse_individual_objects(self, response):
        """Tìm các object riêng lẻ {...}"""
        try:
            objects = []
            in_object = False
            current = ""
            brace_count = 0
            
            for char in response:
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
                            # Kiểm tra nếu có text hoặc type
                            if 'text' in data:
                                if 'entities' not in data:
                                    data['entities'] = []
                                if len(data.get('text', '')) > 50:
                                    objects.append(data)
                            elif 'type' in data and 'text' in data:
                                # Là entity riêng lẻ
                                objects.append(data)
                        except:
                            pass
                        in_object = False
                        current = ""
                elif in_object:
                    current += char
            
            if objects:
                # Nếu tìm thấy các entity riêng lẻ, gộp lại
                if all('type' in o for o in objects):
                    text_parts = [o.get('text', '') for o in objects if 'text' in o]
                    if text_parts:
                        return [{
                            'text': '. '.join(text_parts),
                            'entities': objects
                        }]
                # Nếu là các object đầy đủ
                elif all('text' in o for o in objects):
                    return objects[:3]
            
            return None
        except Exception as e:
            print(f"⚠️ Individual objects parse error: {e}")
            return None
    
    def _parse_text_only(self, response):
        """Nếu chỉ có text, tạo entities cơ bản"""
        try:
            # Tìm text trong response
            text_match = re.search(r'"text"\s*:\s*"([^"]+)"', response)
            if text_match:
                text = text_match.group(1)
                # Tìm các entity trong text
                entities = []
                
                # Tìm các keywords y tế
                medical_terms = {
                    'đái tháo đường': 'CHẨN_ĐOÁN',
                    'tăng huyết áp': 'CHẨN_ĐOÁN',
                    'hen suyễn': 'CHẨN_ĐOÁN',
                    'viêm phổi': 'CHẨN_ĐOÁN',
                    'Metformin': 'THUỐC',
                    'Lisinopril': 'THUỐC',
                    'Albuterol': 'THUỐC',
                    'Amoxicillin': 'THUỐC',
                    'ho': 'TRIỆU_CHỨNG',
                    'sốt': 'TRIỆU_CHỨNG',
                    'đau': 'TRIỆU_CHỨNG',
                    'mệt': 'TRIỆU_CHỨNG',
                }
                
                for term, term_type in medical_terms.items():
                    if term in text:
                        start = text.find(term)
                        if start != -1:
                            entities.append({
                                'text': term,
                                'type': term_type,
                                'start': start,
                                'end': start + len(term),
                                'assertions': [],
                                'candidates': []
                            })
                
                if entities:
                    return [{'text': text, 'entities': entities}]
            
            return None
        except:
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
            
            # Nếu entities là dict (format sai), chuyển thành list
            if isinstance(entities, dict):
                entities = [entities]
            
            print(f"\n📊 Sample {idx}:")
            print(f"   Text length: {len(text)} chars")
            print(f"   Entities: {len(entities)}")
            
            # Lưu .txt
            txt_path = self.output_dir / "input" / f"{idx}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ Saved {txt_path}")
            
            # Chuyển entities sang format chuẩn
            output_entities = []
            for entity in entities:
                if not isinstance(entity, dict):
                    continue
                
                entity_text = entity.get('text', '')
                if not entity_text:
                    continue
                
                # Tìm vị trí
                start = entity.get('start', -1)
                end = entity.get('end', -1)
                
                if start == -1 or end == -1 or start >= end:
                    found = text.find(entity_text)
                    if found != -1:
                        start = found
                        end = found + len(entity_text)
                    else:
                        continue
                
                # Chuẩn hóa type
                entity_type = entity.get('type', '')
                if entity_type and entity_type not in ['CHẨN_ĐOÁN', 'THUỐC', 'TRIỆU_CHỨNG', 'TÊN_XÉT_NGHIỆM', 'KẾT_QUẢ_XÉT_NGHIỆM']:
                    # Map các type khác về đúng chuẩn
                    type_map = {
                        'Bệnh lý': 'CHẨN_ĐOÁN',
                        'bệnh': 'CHẨN_ĐOÁN',
                        'thuốc': 'THUỐC',
                        'drug': 'THUỐC',
                        'symptom': 'TRIỆU_CHỨNG',
                        'triệu chứng': 'TRIỆU_CHỨNG'
                    }
                    entity_type = type_map.get(entity_type, 'CHẨN_ĐOÁN')
                
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
        
        print(f"\n🎉 Successfully saved {len(samples)} samples to {self.output_dir}/")
    
    def _create_fallback_samples(self):
        """Fallback samples chất lượng cao"""
        return [
            {
                "text": """Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) đã 5 năm. Bệnh nhân không có tiền sử bệnh tim mạch hay đột quỵ. Hiện tại bệnh nhân đang dùng Metformin 500mg uống 2 lần/ngày và Lisinopril 10mg uống 1 lần/ngày. Triệu chứng hiện tại bao gồm mệt mỏi, khát nước nhiều, tiểu nhiều, đôi khi hoa mắt chóng mặt. Kết quả xét nghiệm mới nhất: HbA1c 8.5%, Creatinine 1.2 mg/dL, Glucose máu đói 180 mg/dL. Gia đình có bố bị đái tháo đường type 2 từ năm 60 tuổi.""",
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
                "text": """Bệnh nhân nữ 42 tuổi, đến khám tại phòng khám hô hấp vì khó thở, ho khan, tức ngực kéo dài 1 tuần. Bệnh nhân không sốt, không có đờm, không có tiền sử hen suyễn. Tiền sử gia đình: mẹ bị hen suyễn từ nhỏ. Bệnh nhân đã được điều trị với Albuterol inhaler 2 nhát/ngày và Fluticasone 100mcg/ngày trong 3 ngày, nhưng triệu chứng không đỡ. Xét nghiệm chức năng hô hấp: FEV1 65%, FEV1/FVC 70%. Bác sĩ chẩn đoán hen suyễn khởi phát muộn và đề nghị nhập viện theo dõi.""",
                "entities": [
                    {"text": "hen suyễn", "type": "CHẨN_ĐOÁN", "start": 197, "end": 206, "assertions": ["isFamily"], "candidates": ["J45.909"]},
                    {"text": "Albuterol inhaler", "type": "THUỐC", "start": 237, "end": 255, "assertions": ["isHistorical"], "candidates": ["432"]},
                    {"text": "Fluticasone 100mcg", "type": "THUỐC", "start": 260, "end": 279, "assertions": ["isHistorical"], "candidates": ["312938"]},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 51, "end": 58, "assertions": [], "candidates": []},
                    {"text": "ho khan", "type": "TRIỆU_CHỨNG", "start": 60, "end": 67, "assertions": [], "candidates": []},
                    {"text": "tức ngực", "type": "TRIỆU_CHỨNG", "start": 69, "end": 77, "assertions": [], "candidates": []},
                    {"text": "FEV1 65%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 348, "end": 357, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": """Bệnh nhân nam 55 tuổi, nhập viện cấp cứu vì sốt cao 39.5°C, ho có đờm xanh, khó thở tăng dần trong 3 ngày. Bệnh nhân có tiền sử hút thuốc lá 30 năm. Kết quả xét nghiệm máu: WBC 18.5 x10^9/L, NEUT% 85%, CRP 120 mg/L. X-quang ngực cho thấy đông đặc thùy phổi phải. Bệnh nhân được chẩn đoán viêm phổi cộng đồng (J18.9) và điều trị với Amoxicillin 500mg tiêm tĩnh mạch mỗi 6 giờ.""",
                "entities": [
                    {"text": "viêm phổi cộng đồng", "type": "CHẨN_ĐOÁN", "start": 370, "end": 390, "assertions": [], "candidates": ["J18.9"]},
                    {"text": "Amoxicillin 500mg", "type": "THUỐC", "start": 414, "end": 432, "assertions": [], "candidates": ["723"]},
                    {"text": "sốt cao 39.5°C", "type": "TRIỆU_CHỨNG", "start": 30, "end": 43, "assertions": [], "candidates": []},
                    {"text": "ho có đờm xanh", "type": "TRIỆU_CHỨNG", "start": 45, "end": 61, "assertions": [], "candidates": []},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 63, "end": 70, "assertions": [], "candidates": []},
                    {"text": "WBC", "type": "TÊN_XÉT_NGHIỆM", "start": 148, "end": 151, "assertions": [], "candidates": []},
                    {"text": "18.5 x10^9/L", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 152, "end": 165, "assertions": [], "candidates": []},
                    {"text": "NEUT% 85%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 167, "end": 177, "assertions": [], "candidates": []}
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
        print("📄 Các file đã tạo:")
        print("   - input/1.txt, 2.txt, 3.txt")
        print("   - output/1.json, 2.json, 3.json")
        print("\n📝 Debug files:")
        print("   - debug_prompt.txt")
        print("   - debug_response.txt")


if __name__ == "__main__":
    main()