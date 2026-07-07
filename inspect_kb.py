import json

def inspect_sample():
    try:
        with open("data/clinical_kb_full.json", "r", encoding="utf-8") as f:
            # Nếu file đang bị dở, ta cần sửa lại thủ công hoặc chỉ lấy phần đã xong
            # Để đơn giản, ta đọc trực tiếp
            data = json.load(f)
            
            diseases = list(data["entities"].keys())
            if not diseases:
                print("File JSON đang rỗng hoặc chưa có dữ liệu!")
                return

            # In ra bệnh đầu tiên
            sample_disease = diseases[0]
            print(f"--- ĐANG XEM MẪU: {sample_disease} ---")
            print(json.dumps(data["entities"][sample_disease], indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Lỗi đọc file (có thể do file đang viết dở nên định dạng JSON chưa đóng): {e}")

if __name__ == "__main__":
    inspect_sample()