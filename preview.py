import json
import random
import os
from pprint import pprint

# Import thẳng hàm sinh mẫu từ file master của bạn
# Đảm bảo file 2_generate_emr.py nằm cùng thư mục ddeer import generate_golden_sample, KB_DATA, ALL_DISEASES
from generate_emr import generate_golden_sample, KB_DATA, ALL_DISEASES

def preview_mode():
    print("🔍 ĐANG KHỞI ĐỘNG CHẾ ĐỘ XEM TRƯỚC (PREVIEW MODE)...")
    
    # 1. Bốc ngẫu nhiên 1 bệnh trong danh sách
    target_disease = random.choice(ALL_DISEASES)
    kb_info = KB_DATA[target_disease]
    
    print(f"\n🎯 Đã chọn bệnh: {target_disease.upper()}")
    print("-" * 60)
    
    # 2. Sinh 10 mẫu cho bệnh này
    success_count = 0
    attempts = 0
    
    while success_count < 10 and attempts < 20:
        attempts += 1
        print(f"\n⏳ Đang sinh mẫu thứ {success_count + 1}/10... (Lần thử: {attempts})")
        
        result = generate_golden_sample(target_disease, kb_info)
        
        if result:
            success_count += 1
            meta = result['meta_data']
            
            print(f"\n{'='*60}")
            print(f"📄 MẪU {success_count} | LOẠI VĂN BẢN: {meta['document_type']}")
            print(f"📊 ĐỘ PHỨC TẠP: {meta['complexity_level']} bệnh nền")
            print(f"{'='*60}")
            print(f"[VĂN BẢN]:\n{result['text']}\n")
            
            # Chỉ in ra text và type của entity để dễ nhìn bằng mắt
            print("[THỰC THỂ ĐÃ BÓC TÁCH & ĐÁNH NHÃN]:")
            for ent in result['entities']:
                print(f"  - {ent['text']}  --> [{ent['type']}] (Gốc: {ent['normalized']})")
                
    print(f"\n✅ Đã xem trước xong 10 mẫu của bệnh {target_disease}!")

if __name__ == "__main__":
    # Đảm bảo Ollama đang chạy trước khi test
    preview_mode()