import json
import os
import re
from generate_samples import SimpleDataGenerator

def convert_to_problem_format(samples, output_dir="output"):
    """
    Chuyển dữ liệu sang format bài toán yêu cầu
    """
    # Tạo thư mục
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/input", exist_ok=True)
    
    results = []
    
    for idx, sample in enumerate(samples, 1):
        print(f"\n📄 Processing sample {idx}...")
        
        # 1. Lưu file input.txt
        text = sample.get('text', '')
        if not text:
            print(f"⚠️ Sample {idx} has no text")
            continue
        
        txt_path = f"{output_dir}/input/{idx}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"✅ Saved text to {txt_path}")
        
        # 2. Chuyển entities sang format bài toán
        entities = sample.get('entities', [])
        assertions = sample.get('assertions', {})
        
        output_entities = []
        for entity in entities:
            # Lấy text và position
            entity_text = entity.get('text', '')
            
            # Nếu không có start/end, tìm trong text
            if 'start' not in entity or 'end' not in entity:
                start = text.find(entity_text)
                if start != -1:
                    entity['start'] = start
                    entity['end'] = start + len(entity_text)
            
            # Xây dựng output entity
            output_entity = {
                "text": entity_text,
                "position": [entity.get('start', 0), entity.get('end', len(entity_text))],
                "type": entity.get('type', 'CHẨN_ĐOÁN'),
                "assertions": [],
                "candidates": []
            }
            
            # Thêm assertions
            if assertions:
                if assertions.get('isHistorical'):
                    output_entity['assertions'].append('isHistorical')
                if assertions.get('isFamily'):
                    output_entity['assertions'].append('isFamily')
                if assertions.get('isNegated'):
                    output_entity['assertions'].append('isNegated')
            
            # Thêm candidates (mã ICD-10 hoặc RxNorm)
            if output_entity['type'] == 'CHẨN_ĐOÁN':
                if 'E11.9' in entity_text or 'đái tháo đường' in entity_text.lower():
                    output_entity['candidates'] = ['E11.9']
                elif 'I10' in entity_text or 'tăng huyết áp' in entity_text.lower():
                    output_entity['candidates'] = ['I10']
                elif 'J45.909' in entity_text or 'hen suyễn' in entity_text.lower():
                    output_entity['candidates'] = ['J45.909']
                elif 'J18.9' in entity_text or 'viêm phổi' in entity_text.lower():
                    output_entity['candidates'] = ['J18.9']
            
            if output_entity['type'] == 'THUỐC':
                if 'metformin' in entity_text.lower():
                    output_entity['candidates'] = ['6809']
                elif 'lisinopril' in entity_text.lower():
                    output_entity['candidates'] = ['314076']
                elif 'albuterol' in entity_text.lower():
                    output_entity['candidates'] = ['432']
                elif 'amoxicillin' in entity_text.lower():
                    output_entity['candidates'] = ['723']
            
            output_entities.append(output_entity)
        
        # Lưu file JSON
        json_path = f"{output_dir}/{idx}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_entities, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved JSON to {json_path}")
        
        results.append({
            "sample_id": idx,
            "text": text,
            "entities": output_entities
        })
    
    return results

def create_sample_manually():
    """Tạo 3 sample thủ công để test nếu không có Ollama"""
    
    samples = [
        {
            "text": "Bệnh nhân nam 65 tuổi, tiền sử đái tháo đường type 2 và tăng huyết áp 5 năm. Hiện tại bệnh nhân đang dùng Metformin 500mg và Lisinopril 10mg. Triệu chứng: mệt mỏi, khát nước nhiều, tiểu nhiều. Gia đình có bố bị đái tháo đường.",
            "entities": [
                {"text": "đái tháo đường type 2", "type": "CHẨN_ĐOÁN", "start": 30, "end": 52},
                {"text": "tăng huyết áp", "type": "CHẨN_ĐOÁN", "start": 57, "end": 71},
                {"text": "Metformin 500mg", "type": "THUỐC", "start": 95, "end": 111},
                {"text": "Lisinopril 10mg", "type": "THUỐC", "start": 116, "end": 132},
                {"text": "mệt mỏi", "type": "TRIỆU_CHỨNG", "start": 145, "end": 153},
                {"text": "khát nước nhiều", "type": "TRIỆU_CHỨNG", "start": 155, "end": 170},
                {"text": "tiểu nhiều", "type": "TRIỆU_CHỨNG", "start": 175, "end": 185}
            ],
            "assertions": {
                "isHistorical": True,
                "isFamily": True
            }
        },
        {
            "text": "Bệnh nhân nữ 40 tuổi, đến cấp cứu vì khó thở, ho khan, tức ngực. Bệnh nhân không sốt, không có đờm. Tiền sử hen suyễn từ nhỏ. Đang điều trị với Albuterol inhaler và Fluticasone.",
            "entities": [
                {"text": "hen suyễn", "type": "CHẨN_ĐOÁN", "start": 89, "end": 98},
                {"text": "Albuterol inhaler", "type": "THUỐC", "start": 120, "end": 138},
                {"text": "Fluticasone", "type": "THUỐC", "start": 143, "end": 155},
                {"text": "khó thở", "type": "TRIỆU_CHỨNG", "start": 40, "end": 47},
                {"text": "ho khan", "type": "TRIỆU_CHỨNG", "start": 49, "end": 56},
                {"text": "tức ngực", "type": "TRIỆU_CHỨNG", "start": 58, "end": 66}
            ],
            "assertions": {
                "isHistorical": True,
                "isNegated": True
            }
        },
        {
            "text": "Bệnh nhân nam 55 tuổi, nhập viện vì sốt 39°C, ho có đờm xanh, khó thở. WBC: 14.5, Neutrophils: 80%. Chẩn đoán viêm phổi. Điều trị Amoxicillin 500mg.",
            "entities": [
                {"text": "viêm phổi", "type": "CHẨN_ĐOÁN", "start": 95, "end": 104},
                {"text": "Amoxicillin 500mg", "type": "THUỐC", "start": 112, "end": 130},
                {"text": "sốt 39°C", "type": "TRIỆU_CHỨNG", "start": 25, "end": 33},
                {"text": "ho có đờm xanh", "type": "TRIỆU_CHỨNG", "start": 35, "end": 51},
                {"text": "WBC", "type": "TÊN_XÉT_NGHIỆM", "start": 58, "end": 61},
                {"text": "14.5", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 63, "end": 67},
                {"text": "Neutrophils", "type": "TÊN_XÉT_NGHIỆM", "start": 73, "end": 84},
                {"text": "80%", "type": "KẾT_QUẢ_XÉT_NGHIỆM", "start": 86, "end": 90}
            ],
            "assertions": {}
        }
    ]
    
    return samples

def main():
    print("="*60)
    print("🎯 Synthetic Data Generator for Medical NLP")
    print("="*60)
    
    # Kiểm tra Ollama
    from ollama_client import OllamaClient
    client = OllamaClient()
    
    if client.check_health():
        print("\n✅ Connected to Ollama")
        print("🔄 Generating samples with Qwen2.5...\n")
        
        # Sinh dữ liệu với Ollama
        generator = SimpleDataGenerator()
        samples = generator.generate_all_samples()
        
    else:
        print("\n⚠️ Cannot connect to Ollama")
        print("📌 Using manual sample data instead\n")
        
        # Sử dụng sample thủ công
        samples = create_sample_manually()
    
    # Chuyển sang format bài toán
    print("\n" + "="*60)
    print("📦 Converting to problem format...")
    print("="*60)
    
    results = convert_to_problem_format(samples)
    
    print("\n" + "="*60)
    print("✅ Done! Output files:")
    print("="*60)
    print(f"📁 Input files: output/input/1.txt, 2.txt, 3.txt")
    print(f"📁 Output JSON: output/1.json, 2.json, 3.json")
    
    # Hiển thị preview
    print("\n📊 Sample preview:")
    for result in results:
        print(f"\n--- Sample {result['sample_id']} ---")
        print(f"Text: {result['text'][:100]}...")
        print(f"Entities: {len(result['entities'])} concepts")
    
if __name__ == "__main__":
    main()