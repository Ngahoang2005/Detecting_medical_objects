import json
import re

def is_clean_text(text):
    """
    Màng lọc 3 lớp: Bắt Hán tự, Pinyin có dấu, và cấu trúc Pinyin lạ.
    """
    # 1. MÀNG LỌC HÁN TỰ (Unicode CJK)
    has_chinese = bool(re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))
    if has_chinese:
        return False
        
    # 2. MÀNG LỌC PINYIN CÓ DẤU (Macron & Caron)
    # Bắt các nguyên âm có thanh điệu đặc trưng của tiếng Trung (ā, ǎ, ě...)
    has_toned_pinyin = bool(re.search(r'[āǎēěīǐōǒūǔǖǘǚǜĀǍĒĚĪǏŌǑŪǓǕǗǙǛ]', text))
    if has_toned_pinyin:
        return False
        
    # 3. MÀNG LỌC PINYIN KHÔNG DẤU (Heuristic ngữ âm)
    # Tìm các từ ĐỨNG ĐỘC LẬP (word boundary \b) có cấu trúc đặc sệt Pinyin 
    # mà không phải là từ tiếng Việt hay viết tắt y khoa phổ biến.
    # Không hard-code cụ thể chữ JU, mà bắt theo pattern phụ âm + nguyên âm lạ.
    suspicious_phonetics = r'\b([Jj][UuAaEeIiOo]|[Zz][Hh][IiEeUuAaOo]|[Qq][IiUuAa]|[Xx][IiUuOo])\b'
    if re.search(suspicious_phonetics, text):
        return False
        
    return True

def clean_and_analyze_dataset(input_file, output_file):
    print(f"🔍 Đang đọc dữ liệu gốc từ: {input_file}")
    
    valid_samples = []
    removed_count = 0
    lengths = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                sample = json.loads(line)
                text = sample['text']
                
                # Màng lọc Unicode
                if is_clean_text(text):
                    valid_samples.append(sample)
                    # Tính toán độ dài (số lượng từ)
                    word_count = len(text.split())
                    lengths.append(word_count)
                else:
                    removed_count += 1
            except json.JSONDecodeError:
                removed_count += 1
                
    print(f"💾 Đang ghi dữ liệu SẠCH ra file an toàn: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for sample in valid_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
            
    # Phân tích thống kê độ dài để đánh giá rủi ro Train vs Test
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    max_len = max(lengths) if lengths else 0
    min_len = min(lengths) if lengths else 0
            
    print("\n" + "=" * 50)
    print("📊 BÁO CÁO NGHIỆM THU DỮ LIỆU:")
    print("=" * 50)
    print(f" 🗑️  Số mẫu dính Hán tự/Lỗi đã xóa bỏ : {removed_count}")
    print(f" ✅  Số mẫu SẠCH ĐẠT CHUẨN (Mang đi Train) : {len(valid_samples)}")
    print("-" * 50)
    print("📏 THỐNG KÊ PHÂN PHỐI ĐỘ DÀI (Số lượng từ/mẫu):")
    print(f" - Ngắn nhất : {min_len} từ")
    print(f" - Dài nhất  : {max_len} từ")
    print(f" - Trung bình: {avg_len:.1f} từ")
    print("=" * 50)

if __name__ == "__main__":
    # Trỏ vào file 4 tiếng của bạn
    INPUT_PATH = "data/emr_dataset_master.jsonl"
    # LƯU RA FILE MỚI, KHÔNG GHI ĐÈ
    OUTPUT_PATH = "data/emr_cleaned_dataset.jsonl" 
    
    clean_and_analyze_dataset(INPUT_PATH, OUTPUT_PATH)