import json
import re
import os
import pandas as pd
from typing import List, Dict, Any

class MedicalDataCleaner:
    def __init__(self, rxnorm_path: str = "data/rxnorm_clean.csv"):
        print("⚙️ Đang khởi tạo bộ lọc toàn diện...")
        # Lớp 4: Nạp từ điển chuẩn y khoa
        self.valid_drugs = set()
        if os.path.exists(rxnorm_path):
            df = pd.read_csv(rxnorm_path)
            self.valid_drugs = set(df['TenThuoc'].dropna().str.lower().str.strip())
            print(f"   -> Đã nạp {len(self.valid_drugs)} hoạt chất chuẩn từ RxNorm.")
        else:
            print("   -> ⚠️ Không tìm thấy file RxNorm, sẽ bỏ qua bước đối chiếu từ điển.")

    def layer1_unicode_scrubbing(self, text: str) -> str:
        """Lớp 1: Loại bỏ triệt để chữ Trung/Nhật/Hàn, Emoji, và ký tự rác"""
        if not isinstance(text, str):
            return ""
        
        # Xóa CJK (Chữ Hán, Hiragana, Katakana, Hangul)
        text = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+', '', text)
        
        # Xóa các ký tự điều khiển vô hình (zero-width space, BOM, v.v.)
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        
        return text

    def layer2_text_normalization(self, text: str, is_drug: bool = False) -> str:
        """Lớp 2: Chuẩn hóa khoảng trắng, dấu câu và định dạng"""
        # Xóa khoảng trắng thừa và khoảng trắng kép
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return ""

        if is_drug:
            # Thuốc: Ép về chữ thường, xóa dấu câu ở cuối (vd: "aspirin." -> "aspirin")
            text = text.lower().rstrip('.,;:')
        else:
            # Triệu chứng/Xét nghiệm: Viết hoa chữ cái đầu, xóa dấu câu thừa ở cuối
            text = text.rstrip('.,;:')
            if len(text) > 1:
                text = text[0].upper() + text[1:]
                
        return text

    def layer3_and_4_process_list(self, items: List[str], item_type: str) -> List[str]:
        """Lớp 3 & 4: Lọc mảng, loại bỏ phần tử rỗng và kiểm chứng chuyên ngành"""
        if not isinstance(items, list):
            return []

        cleaned_list = []
        for item in items:
            # Chạy qua Lớp 1 & Lớp 2
            raw = self.layer1_unicode_scrubbing(str(item))
            is_drug = (item_type == 'drugs')
            clean_item = self.layer2_text_normalization(raw, is_drug=is_drug)

            # Lớp 3: Bỏ qua nếu sau khi lọc bị rỗng hoặc quá ngắn (< 2 ký tự)
            if len(clean_item) < 2:
                continue

            # Lớp 4: Kiểm chứng chuyên ngành riêng cho Thuốc
            if is_drug and self.valid_drugs:
                # Chỉ giữ lại nếu thuốc nằm trong danh mục chuẩn RxNorm
                if clean_item not in self.valid_drugs:
                    continue 

            cleaned_list.append(clean_item)

        # Loại bỏ các phần tử trùng lặp (Deduplication) nhưng giữ nguyên thứ tự
        return list(dict.fromkeys(cleaned_list))

    def process_kb(self, input_file: str, output_file: str):
        print(f"🚀 Bắt đầu xử lý file: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        entities = data.get("entities", {})
        cleaned_entities = {}
        
        stats = {"total": len(entities), "passed": 0, "dropped": 0}

        for disease, triad in entities.items():
            # Chuẩn hóa tên bệnh
            clean_disease = self.layer2_text_normalization(self.layer1_unicode_scrubbing(disease))
            if not clean_disease:
                continue

            symptoms = self.layer3_and_4_process_list(triad.get("symptoms", []), "symptoms")
            tests = self.layer3_and_4_process_list(triad.get("tests", []), "tests")
            drugs = self.layer3_and_4_process_list(triad.get("drugs", []), "drugs")

            # Lớp 5: Quality Gating (Đánh giá chất lượng tổng thể của mẫu)
            # Một bệnh hợp lệ bắt buộc phải có ít nhất 1 triệu chứng và 1 thuốc
            if len(symptoms) >= 1 and len(drugs) >= 1:
                cleaned_entities[clean_disease] = {
                    "symptoms": symptoms,
                    "tests": tests,
                    "drugs": drugs
                }
                stats["passed"] += 1
            else:
                # Nếu mẫu bị vỡ nặng (ví dụ: toàn thuốc rác bị lọc hết), vứt bỏ mẫu này
                stats["dropped"] += 1

        data["entities"] = cleaned_entities

        # Ghi file kết quả
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("-" * 50)
        print(f"📊 BÁO CÁO CHẤT LƯỢNG SAU XỬ LÝ:")
        print(f"   - Tổng số bệnh ban đầu : {stats['total']}")
        print(f"   - Số mẫu ĐẠT CHUẨN     : {stats['passed']} (Đã lưu vào {output_file})")
        print(f"   - Số mẫu BỊ LOẠI BỎ    : {stats['dropped']} (Do không đạt tiêu chuẩn tối thiểu)")
        print("-" * 50)

if __name__ == "__main__":
    cleaner = MedicalDataCleaner(rxnorm_path="data/rxnorm_clean.csv")
    cleaner.process_kb(
        input_file="data/clinical_kb_full.json",
        output_file="data/clinical_kb_perfect.json"
    )