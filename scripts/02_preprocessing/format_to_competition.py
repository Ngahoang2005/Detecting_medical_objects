import json
import os
import random

def format_to_competition_schema(input_file, output_dir, train_ratio=0.8, valid_ratio=0.1):
    print(f"🔄 Đang chuyển đổi {input_file} sang cấu trúc chuẩn của đề bài...")
    
    if not os.path.exists(input_file):
        print(f"❌ Lỗi: Không tìm thấy file {input_file}")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    
    # Xáo trộn dữ liệu
    random.seed(42)
    random.shuffle(data)
    
    formatted_data = []
    
    for sample in data:
        text = sample['text']
        entities = sample['entities']
        
        comp_entities = []
        for ent in entities:
            # 1. Chuyển đổi Vị trí (Position)
            position = [ent['start'], ent['end']]
            
            # 2. Ánh xạ Loại nhãn (Type)
            old_type = ent['type']
            comp_type = ""
            assertions = []
            
            if old_type == "DISEASE":
                comp_type = "CHẨN_ĐOÁN"
            elif old_type == "DRUG":
                comp_type = "THUỐC"
            elif old_type == "TEST":
                comp_type = "TÊN_XÉT_NGHIỆM"
            elif old_type == "SYMPTOM_PRESENT":
                comp_type = "TRIỆU_CHỨNG"
            elif old_type == "SYMPTOM_NEGATED":
                comp_type = "TRIỆU_CHỨNG"
                assertions.append("isNegated")
                
            # Xử lý Candidates (Mã chuẩn)
            # Lưu ý: Cần thêm logic lookup mã ICD/RxNorm thực tế tại đây nếu muốn đạt điểm tối đa
            candidates = [] 
            if comp_type in ["CHẨN_ĐOÁN", "THUỐC"]:
                candidates = [ent.get("normalized", "UNKNOWN_CODE")]
                
            # 3. Đóng gói thành Dictionary chuẩn theo yêu cầu đề
            comp_ent = {
                "text": ent['text'],
                "position": position,
                "type": comp_type
            }
            
            # Thêm trường tùy chọn nếu có
            if comp_type in ["CHẨN_ĐOÁN", "THUỐC", "TRIỆU_CHỨNG"]:
                comp_ent["assertions"] = assertions
            
            if comp_type in ["CHẨN_ĐOÁN", "THUỐC"]:
                comp_ent["candidates"] = candidates
                
            comp_entities.append(comp_ent)
            
        formatted_data.append({
            "input_text": text,
            "output_json": comp_entities
        })

    # Chia tập Train / Valid / Test
    total = len(formatted_data)
    train_end = int(total * train_ratio)
    valid_end = train_end + int(total * valid_ratio)
    
    train_data = formatted_data[:train_end]
    valid_data = formatted_data[train_end:valid_end]
    test_data = formatted_data[valid_end:]
    
    os.makedirs(output_dir, exist_ok=True)
    
    def write_jsonl(data_list, filename):
        path = os.path.join(output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
    write_jsonl(train_data, 'train_comp.jsonl')
    write_jsonl(valid_data, 'valid_comp.jsonl')
    write_jsonl(test_data, 'test_comp.jsonl')
    
    print(f"✅ Đã chia tập và định dạng xong theo yêu cầu cuộc thi!")
    print(f"Tổng cộng: {total} mẫu. Lưu tại: {output_dir}")

if __name__ == "__main__":
    # Trỏ vào file cleaned chính của bạn
    INPUT_PATH = "data/emr_cleaned_dataset.jsonl"
    OUTPUT_DIR = "data/competition_ready"
    format_to_competition_schema(INPUT_PATH, OUTPUT_DIR)