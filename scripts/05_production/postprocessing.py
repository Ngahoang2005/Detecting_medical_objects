import os
import json
import zipfile

input_dir = "data/temp_input/input" # Thư mục chứa các file .txt gốc
raw_json_dir = "data/output_json" # Thư mục chứa JSON thô LLM vừa sinh ra
final_json_dir = "data/final_submission" # Thư mục chứa JSON đã làm sạch
zip_filename = "output.zip"

os.makedirs(final_json_dir, exist_ok=True)

print("--- BẮT ĐẦU POST-PROCESSING ---")

def clean_and_map_positions(raw_text, entities):
    cleaned_entities = []
    
    for ent in entities:
        # Bỏ qua nếu LLM sinh lỗi không có key 'text' hoặc 'type'
        if 'text' not in ent or 'type' not in ent:
            continue
            
        search_text = ent['text'].strip()
        
        # 1. TÌM POSITION CHUẨN XÁC TRONG VĂN BẢN GỐC
        start_idx = raw_text.find(search_text)
        
        # Nếu không tìm thấy text trong văn bản gốc (LLM ảo giác), thì bỏ qua luôn để tránh bị trừ điểm WER
        if start_idx == -1:
            continue 
            
        end_idx = start_idx + len(search_text)
        
        # 2. CHUẨN HÓA DATA TYPES THEO YÊU CẦU BTC
        # Ép candidates thành dạng List
        candidates = ent.get('candidates', [])
        if isinstance(candidates, str):
            candidates = [candidates]
            
        # Ép assertions thành dạng List
        assertions = ent.get('assertions', [])
        if isinstance(assertions, str):
            assertions = [assertions]
            
        # 3. ĐÓNG GÓI THỰC THỂ CHUẨN
        cleaned_ent = {
            "text": search_text,
            "type": ent['type'],
            "candidates": candidates,
            "assertions": assertions,
            "position": [start_idx, end_idx]
        }
        cleaned_entities.append(cleaned_ent)
        
    return cleaned_entities

# Xử lý từng file
file_count = 0
for filename in os.listdir(raw_json_dir):
    if not filename.endswith('.json'):
        continue
        
    txt_filename = filename.replace('.json', '.txt')
    txt_path = os.path.join(input_dir, txt_filename)
    json_path = os.path.join(raw_json_dir, filename)
    
    # Đọc file txt gốc
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    else:
        continue
        
    # Đọc file json thô
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_entities = json.load(f)
    except json.JSONDecodeError:
        # Nếu LLM sinh lỗi cú pháp JSON, gán mảng rỗng để không bị sập toàn bộ chương trình
        raw_entities = [] 

    # Hậu xử lý
    final_entities = clean_and_map_positions(raw_text, raw_entities)
    
    # Lưu ra thư mục final
    final_out_path = os.path.join(final_json_dir, filename)
    with open(final_out_path, 'w', encoding='utf-8') as f:
        json.dump(final_entities, f, ensure_ascii=False, indent=2)
    file_count += 1

print(f"✅ Đã dọn dẹp và gắn tọa độ chuẩn cho {file_count} files.")

# 4. NÉN FILE ĐỂ NỘP BTC
print("--- ĐÓNG GÓI FILE NỘP (output.zip) ---")
with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(final_json_dir):
        for file in files:
            # BTC yêu cầu cấu trúc thư mục output/1.json, nên mình cấu hình archive name cho chuẩn
            zipf.write(os.path.join(root, file), arcname=os.path.join("output", file))

print(f"🎉 Đã nén thành công file {zip_filename}. Cậu có thể nộp file này lên hệ thống!")