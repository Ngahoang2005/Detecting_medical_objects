import json
import requests
import re
import pandas as pd
from tqdm import tqdm
import os
import difflib

# Cấu hình API của Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

print("Đang nạp bộ từ điển RxNorm (5820 hoạt chất) vào RAM...")
# Load từ điển thuốc và tạo dict để tra cứu nhanh
rxnorm_df = pd.read_csv("data/rxnorm_clean.csv")
valid_drugs_lower = rxnorm_df['TenThuoc'].str.lower().tolist()
drug_mapping = dict(zip(rxnorm_df['TenThuoc'].str.lower(), rxnorm_df['TenThuoc']))

def map_to_rxnorm(drug_name):
    """Màng lọc Fuzzy Match: Tìm tên thuốc chuẩn RxNorm gần giống nhất với kết quả LLM nhả ra"""
    matches = difflib.get_close_matches(drug_name.lower(), valid_drugs_lower, n=1, cutoff=0.7)
    if matches:
        return drug_mapping[matches[0]]
    return None

def get_medical_triad(disease):
    prompt = f"""
    Bạn là một từ điển Y khoa chuyên nghiệp. Đối với chẩn đoán bệnh: "{disease}"
    Hãy suy luận và liệt kê:
    1. symptoms: 4-6 triệu chứng lâm sàng phổ biến nhất (tiếng Việt).
    2. tests: 2-4 chỉ định cận lâm sàng/xét nghiệm.
    3. drugs: 3-5 tên HOẠT CHẤT THUỐC (Generic name - tiếng Anh quốc tế) dùng để điều trị.

    Chỉ trả về ĐÚNG cấu trúc JSON sau:
    {{
        "symptoms": ["..."],
        "tests": ["..."],
        "drugs": ["..."]
    }}
    """
    
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": MODEL, 
            "prompt": prompt, 
            "format": "json", 
            "stream": False, 
            "options": {"temperature": 0.1}
        })
        match = re.search(r'\{.*\}', res.json()['response'], re.DOTALL)
        if not match: return None
        
        data = json.loads(match.group(0))
        
        # --- BƯỚC ĐỐI CHIẾU RXNORM KỲ DIỆU TẠI ĐÂY ---
        clean_drugs = []
        for d in data.get("drugs", []):
            mapped_drug = map_to_rxnorm(d)
            if mapped_drug:
                clean_drugs.append(mapped_drug)
                
        # Cập nhật lại mảng thuốc chỉ với những từ đã qua kiểm duyệt RxNorm
        data["drugs"] = clean_drugs
        
        # Nếu LLM kê thuốc mà không khớp được cái nào trong RxNorm, trả về None để bắt nó làm lại ca khác
        if not data["drugs"]: return None 
        
        return data
    except Exception as e:
        return None

def main():
    print("🚀 Bắt đầu xây dựng Knowledge Base với cơ chế bảo chứng RxNorm...")
    
    # Đọc danh sách ICD-10
    df = pd.read_csv("data/icd10_top.csv")
    diseases = df['TenBenh'].tolist()[:5]
    
    kb = {
        "distributions": {
            "symptom_counts": {"1": 0.05, "2": 0.25, "3": 0.35, "4": 0.25, "5": 0.10},
            "assertion_rates": {"negation": 0.15, "history": 0.30, "family": 0.05},
            "has_test_rate": 0.60,
            "has_drug_rate": 0.75
        },
        "entities": {}
    }
    
    # Quét qua từng bệnh
    for d in tqdm(diseases, desc="Đang trích xuất & Chuẩn hóa Tri thức"):
        triad = get_medical_triad(d)
        if triad:
            kb["entities"][d] = triad
            
    # Phân phối
    total_valid = len(kb["entities"])
    if total_valid > 0:
        kb["distributions"]["diseases"] = {d: 1.0/total_valid for d in kb["entities"]}
    
    with open("data/clinical_kb_full.json", "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Đã chưng cất thành công Đồ thị tri thức cho {total_valid} bệnh lý!")
    print("Mọi tên thuốc trong file này đều bảo đảm 100% xuất hiện trong hệ thống RxNorm.")

if __name__ == "__main__":
    main()