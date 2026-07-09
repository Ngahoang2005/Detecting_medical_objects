import os
import json
from unsloth import FastLanguageModel

# 1. Đường dẫn thư mục (Chỉ đích danh thư mục 'input' của cậu)
input_dir = "input"
output_dir = "output_json"

os.makedirs(output_dir, exist_ok=True)

print("--- 1. ĐANG LOAD MODEL VÀO VRAM ---")
# Lưu ý: Nếu cậu chưa copy model sang final_model, hãy sửa thành "models/outputs/checkpoint-500"
model, tokenizer = FastLanguageModel.from_pretrained("models/final_model", local_files_only=True)
FastLanguageModel.for_inference(model)

def extract_entities(text):
    prompt = f"<|im_start|>system\nTrích xuất các thực thể y khoa từ văn bản dưới đây thành định dạng JSON chuẩn.\n<|im_end|>\n<|im_user|>\n{text}<|im_end|>\n<|im_assistant|>\n"
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=2048)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).split("<|im_assistant|>\n")[-1]

print("--- 2. BẮT ĐẦU INFERENCE ---")
file_list = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
print(f"🔍 Tìm thấy {len(file_list)} file trong thư mục '{input_dir}'. Bắt đầu xử lý...")

# 3. Chạy vòng lặp xử lý từng file
for filename in file_list:
    filepath = os.path.join(input_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Chạy model
    result_json = extract_entities(text)
    
    # Lưu ra file mới
    out_filepath = os.path.join(output_dir, filename.replace('.txt', '.json'))
    with open(out_filepath, 'w', encoding='utf-8') as f:
        f.write(result_json)
    
    print(f"✅ Đã xử lý xong: {filename}")

print("--- 🎉 HOÀN THÀNH TẤT CẢ ---")