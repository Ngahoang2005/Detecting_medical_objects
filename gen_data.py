"""
SYNTHETIC DATA GENERATOR FOR MEDICAL NLP - FIXED VERSION
Tạo 3 file dữ liệu tổng hợp có nhãn từ 100 file test chưa nhãn
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
            print(f"Content: {self.samples[0]['content'][:200]}...")
        
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
        
        analysis_result = {
            'total_files': len(self.samples),
            'avg_length': sum(s['length'] for s in self.samples) / len(self.samples),
            'avg_words': sum(s['word_count'] for s in self.samples) / len(self.samples),
            'common_words': common_words[:10],
            'structures': structures,
            'info_types': info_types
        }
        
        print("✅ Analysis complete")
        return analysis_result
    
    def _analyze_structures(self) -> Dict:
        """Phân tích cấu trúc văn bản"""
        structures = {
            'has_diagnosis': 0, 'has_symptoms': 0, 'has_medication': 0,
            'has_lab': 0, 'has_history': 0, 'has_family': 0, 'has_negation': 0
        }
        
        diagnosis_keywords = ['chẩn đoán', 'mắc bệnh', 'được chẩn đoán', 'diagnosed', 'bị']
        symptom_keywords = ['ho', 'sốt', 'đau', 'mệt', 'khó thở', 'buồn nôn', 'tức ngực', 'triệu chứng']
        medication_keywords = ['thuốc', 'uống', 'dùng', 'điều trị', 'medication', 'mg']
        lab_keywords = ['xét nghiệm', 'kết quả', 'WBC', 'Hb', 'NEUT', 'LYMPH']
        history_keywords = ['tiền sử', 'trước đây', 'đã từng', 'có tiền sử', 'history']
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
        """Tạo prompt cho Qwen - ĐÃ SỬA để dễ parse hơn"""
        
        # Chọn 3 mẫu ngẫu nhiên làm few-shot
        few_shot = random.sample(self.samples, min(3, len(self.samples)))
        
        prompt = f"""Bạn là chuyên gia y tế, cần tạo dữ liệu tổng hợp cho bài toán xử lý văn bản y khoa.

THÔNG TIN VỀ 100 FILE MẪU:
- Tổng số: {analysis['total_files']} file
- Độ dài TB: {analysis['avg_length']:.0f} ký tự
- Số từ TB: {analysis['avg_words']:.0f} từ

CẤU TRÚC THƯỜNG GẶP:
"""
        for key, value in analysis.get('structures', {}).items():
            if value > 30:
                prompt += f"- {value:.1f}% có {key.replace('_', ' ')}\n"
        
        prompt += "\nVÍ DỤ MẪU (3 file ngẫu nhiên):\n"
        for idx, sample in enumerate(few_shot, 1):
            prompt += f"\n--- MẪU {idx} ---\n{sample['content'][:300]}\n"
        
        prompt += f"""

YÊU CẦU: Sinh CHÍNH XÁC {num_to_generate} văn bản y khoa MỚI với:
1. Phong cách TƯƠNG TỰ file mẫu
2. Độ dài ~{analysis['avg_length']:.0f} ký tự
3. Nội dung y tế CHÍNH XÁC và ĐA DẠNG
4. Bao gồm các loại thông tin: chẩn đoán, triệu chứng, thuốc, xét nghiệm

QUAN TRỌNG: 
- Với MỖI văn bản, GÁN NHÃN đầy đủ cho các khái niệm
- Trả về DUY NHẤT 1 JSON ARRAY, KHÔNG có text khác

Định dạng JSON CHÍNH XÁC cho MỖI file:
{{
    "text": "nội dung văn bản y khoa",
    "entities": [
        {{
            "text": "tên khái niệm (chính xác như trong text)",
            "type": "CHẨN_ĐOÁN hoặc THUỐC hoặc TRIỆU_CHỨNG hoặc TÊN_XÉT_NGHIỆM hoặc KẾT_QUẢ_XÉT_NGHIỆM",
            "start": vị_trí_bắt_đầu_(số_nguyên),
            "end": vị_trí_kết_thúc_(số_nguyên),
            "assertions": ["isHistorical"] hoặc ["isFamily"] hoặc ["isNegated"] hoặc [] (rỗng),
            "candidates": ["ICD-10 code"] (nếu là CHẨN_ĐOÁN) hoặc ["RxNorm code"] (nếu là THUỐC) hoặc [] (rỗng)
        }}
    ]
}}

Ví dụ JSON đúng:
[
    {{
        "text": "Bệnh nhân nam 65 tuổi bị đái tháo đường type 2",
        "entities": [
            {{
                "text": "đái tháo đường type 2",
                "type": "CHẨN_ĐOÁN",
                "start": 29,
                "end": 51,
                "assertions": ["isHistorical"],
                "candidates": ["E11.9"]
            }}
        ]
    }}
]

BẮT ĐẦU JSON NGAY BÂY GIỜ (KHÔNG giải thích, KHÔNG mở đầu):
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
        
    def generate(self, prompt, temperature=0.7, max_tokens=2000):
        """Gọi Ollama sinh text"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "stop": ["```"]  # Dừng khi gặp code block
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.Timeout:
            print("⏰ Timeout, retrying...")
            time.sleep(2)
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
        
        print("🔄 Generating 3 new samples with Qwen2.5...")
        print("⏳ This may take 1-2 minutes...")
        
        # Sinh dữ liệu
        response = self.ollama.generate(prompt, temperature=0.7, max_tokens=2000)
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
        
        # Lưu samples
        self._save_samples(samples)
        
        return samples
    
    def _parse_response_improved(self, response):
        """Parse JSON từ response - CẢI THIỆN để bắt nhiều format"""
        
        # Thử các cách khác nhau
        strategies = [
            self._extract_json_array,
            self._extract_json_object,
            self._extract_with_regex,
            self._extract_multiple_objects
        ]
        
        for strategy in strategies:
            result = strategy(response)
            if result:
                return result
        
        print("❌ All parsing strategies failed")
        print(f"Response preview: {response[:500]}...")
        return None
    
    def _extract_json_array(self, text):
        """Tìm JSON array [...]"""
        try:
            # Tìm từ [ đầu tiên đến ] cuối cùng
            start = text.find('[')
            if start == -1:
                return None
            
            # Đếm ngoặc để tìm đúng vị trí đóng
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
                # Kiểm tra mỗi phần tử có đủ fields
                valid_samples = []
                for item in data[:3]:
                    if isinstance(item, dict) and 'text' in item:
                        if 'entities' not in item:
                            item['entities'] = []
                        valid_samples.append(item)
                
                if valid_samples:
                    return valid_samples[:3]
            
            return None
        except:
            return None
    
    def _extract_json_object(self, text):
        """Tìm JSON object {...}"""
        try:
            # Tìm { từ đầu tiên
            start = text.find('{')
            if start == -1:
                return None
            
            # Đếm ngoặc
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
                return [data]  # Trả về list với 1 object
            
            return None
        except:
            return None
    
    def _extract_with_regex(self, text):
        """Dùng regex để tìm JSON"""
        try:
            # Tìm tất cả các cặp {...}
            pattern = r'\{[^{}]*"text"[^{}]*"entities"[^{}]*\}'
            matches = re.findall(pattern, text, re.DOTALL)
            
            samples = []
            for match in matches[:3]:
                try:
                    data = json.loads(match)
                    if 'text' in data:
                        if 'entities' not in data:
                            data['entities'] = []
                        samples.append(data)
                except:
                    continue
            
            if samples:
                return samples
            return None
        except:
            return None
    
    def _extract_multiple_objects(self, text):
        """Tìm nhiều JSON object trong text và ghép lại"""
        try:
            # Tìm tất cả các object riêng lẻ
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
                                objects.append(data)
                        except:
                            pass
                        in_object = False
                        current = ""
                elif in_object:
                    current += char
            
            if objects:
                return objects[:3]
            return None
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
            
            # Lưu .txt
            txt_path = self.output_dir / "input" / f"{idx}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✅ Saved {txt_path}")
            
            # Chuyển entities sang format bài toán
            output_entities = []
            for entity in entities:
                output_entity = {
                    "text": entity.get('text', ''),
                    "position": [
                        entity.get('start', 0),
                        entity.get('end', len(entity.get('text', '')))
                    ],
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
        """Tạo sample thủ công nếu không sinh được"""
        return [
            {
                "text": "Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 (E11.9) và tăng huyết áp (I10) 5 năm. Hiện tại bệnh nhân đang dùng Metformin 500mg và Lisinopril 10mg. Triệu chứng: mệt mỏi, khát nước nhiều, tiểu nhiều. Gia đình có bố bị đái tháo đường.",
                "entities": [
                    {"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 29, "end": 51, "assertions": ["isHistorical"], "candidates": ["E11.9"]},
                    {"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 56, "end": 70, "assertions": ["isHistorical"], "candidates": ["I10"]},
                    {"text": "Metformin 500mg", "type": "THUỐC", "start": 94, "end": 110, "assertions": ["isHistorical"], "candidates": ["6809"]},
                    {"text": "Lisinopril 10mg", "type": "THUỐC", "start": 115, "end": 131, "assertions": ["isHistorical"], "candidates": ["314076"]},
                    {"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 144, "end": 152, "assertions": [], "candidates": []},
                    {"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 154, "end": 169, "assertions": [], "candidates": []},
                    {"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 174, "end": 184, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": "Bệnh nhân nữ 40 tuổi, đến khám vì khó thở, ho khan, tức ngực. Bệnh nhân không sốt, không có đờm. Tiền sử hen suyễn từ nhỏ. Đang điều trị với Albuterol inhaler và Fluticasone.",
                "entities": [
                    {"text": "hen suyễn", "type": "CHẨN_ĐOÁN", "start": 88, "end": 97, "assertions": ["isHistorical"], "candidates": ["J45.909"]},
                    {"text": "Albuterol inhaler", "type": "THUỐC", "start": 119, "end": 137, "assertions": ["isHistorical"], "candidates": ["432"]},
                    {"text": "Fluticasone", "type": "THUỐC", "start": 142, "end": 154, "assertions": ["isHistorical"], "candidates": ["312938"]},
                    {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 39, "end": 46, "assertions": [], "candidates": []},
                    {"text": "ho khan", "type": "TRIỆU_CHỨNG", "start": 48, "end": 55, "assertions": [], "candidates": []},
                    {"text": "tức ngực", "type": "TRIỆU_CHỨNG", "start": 57, "end": 65, "assertions": [], "candidates": []}
                ]
            },
            {
                "text": "Bệnh nhân nam 55 tuổi, nhập viện vì sốt 39°C, ho có đờm xanh, khó thở. WBC: 14.5, NEUT%: 80%. Chẩn đoán viêm phổi. Điều trị Amoxicillin 500mg.",
                "entities": [
                    {"text": "viêm phổi", "type": "CHẨN_ĐOÁN", "start": 95, "end": 104, "assertions": [], "candidates": ["J18.9"]},
                    {"text": "Amoxicillin 500mg", "type": "THUỐC", "start": 112, "end": 130, "assertions": [], "candidates": ["723"]},
                    {"text": "sốt 39°C", "type": "TRIỆU_CHỨNG", "start": 25, "end": 33, "assertions": [], "candidates": []},
                    {"text": "ho có đờm xanh", "type": "TRIỆU_CHỨNG", "start": 35, "end": 51, "assertions": [], "candidates": []},
                    {"text": "WBC", "type": "TÊN_XÉT_NGHIỆM", "start": 58, "end": 61, "assertions": [], "candidates": []},
                    {"text": "14.5", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 63, "end": 67, "assertions": [], "candidates": []},
                    {"text": "NEUT%", "type": "TÊN_XÉT_NGHIỆM", "start": 73, "end": 78, "assertions": [], "candidates": []},
                    {"text": "80%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 80, "end": 84, "assertions": [], "candidates": []}
                ]
            }
        ]


# ==================== PHẦN 5: MAIN ====================

def main():
    print("="*60)
    print("🎯 SYNTHETIC DATA GENERATOR FOR MEDICAL NLP")
    print("📊 Tạo 3 file dữ liệu có nhãn từ 100 file test")
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
    else:
        print("❌ Không tạo được dữ liệu. Kiểm tra Ollama.")


if __name__ == "__main__":
    main()