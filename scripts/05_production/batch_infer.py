import os
import json
import zipfile
from unsloth import FastLanguageModel
# 1. Đường dẫn
zip_path = "data/input.zip"
extract_to = "data/temp_input"
output_dir = "data/output_json"

# 2. Tự động giải nén
os.makedirs(extract_to, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)
print(f"✅ Đã giải nén xong vào: {extract_to}")
# Load model 1 lần duy nhất để tối ưu tốc độ
model, tokenizer = FastLanguageModel.from_pretrained("models/final_model", local_files_only=True)
FastLanguageModel.for_inference(model)

def extract_entities(text):
    prompt = f"<|im_start|>system\nTrích xuất các thực thể y khoa từ văn bản dưới đây thành định dạng JSON chuẩn.\n<|im_end|>\n<|im_user|>\n{text}<|im_end|>\n<|im_assistant|>\n"
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=2048)
    return tokenizer.decode(outputs[0], skip_special_tokens=True).split("<|im_assistant|>\n")[-1]

for filename in os.listdir(extract_to):
    if filename.endswith(".txt"):
        filepath = os.path.join(extract_to, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        result_json = extract_entities(text)
        
        # Lưu kết quả
        with open(os.path.join(output_dir, filename.replace('.txt', '.json')), 'w', encoding='utf-8') as f:
            f.write(result_json)
        print(f"✅ Đã xử lý xong: {filename}")