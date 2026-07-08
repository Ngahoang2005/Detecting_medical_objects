import json
import random

def inspect_10_samples():
    try:
        with open("data/clinical_kb_full.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        diseases = list(data.get("entities", {}).keys())
        if not diseases:
            print("❌ File rỗng hoặc không đúng cấu trúc.")
            return

        print(f"✅ Đã tải KB với tổng cộng {len(diseases)} bệnh lý.")
        print("🔍 Đang bốc ngẫu nhiên 10 mẫu...\n")
        print("=" * 50)
        
        # Bốc ngẫu nhiên 10 mẫu
        samples = random.sample(diseases, min(10, len(diseases)))
        
        for i, disease in enumerate(samples, 1):
            print(f"[{i}/10] Bệnh: {disease}")
            print(json.dumps(data["entities"][disease], indent=2, ensure_ascii=False))
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")

if __name__ == "__main__":
    inspect_10_samples()