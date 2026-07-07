import pandas as pd
import re
import os

os.makedirs("data", exist_ok=True)

def clean_disease_name(text):
    if pd.isna(text): return ""
    cleaned = re.sub(r'\s*\(.*?\)\s*', '', str(text))
    return cleaned.strip()

def is_clinical_term(name):
    """Bộ lọc loại bỏ ngôn ngữ bảo hiểm, giữ lại ngôn ngữ lâm sàng"""
    name_lower = name.lower()
    
    # 1. Loại bỏ các từ khóa thường dùng trong thống kê
    bad_words = [
        "không đặc hiệu", "không xác định", "chưa phân loại", "khác", 
        "do", "tổn thương", "di chứng", "hậu quả", "bất thường", "nghi ngờ"
    ]
    if any(bw in name_lower for bw in bad_words):
        return False
        
    # 2. Loại bỏ các tên bệnh dài dòng lê thê (quá 6-7 từ)
    if len(name.split()) > 6:
        return False
        
    return True

def main():
    print("Đang đọc file ICD-10.xlsx và lọc ngôn ngữ lâm sàng...")
    
    try:
        df = pd.read_excel("ICD-10.xlsx", sheet_name="E - ICD10 Mã bệnh chính", header=2, engine='openpyxl')
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return

    df['TenBenh'] = df['Tên bệnh'].apply(clean_disease_name)
    df = df[df['TenBenh'] != ""]
    df = df.drop_duplicates(subset=['TenBenh'])
    
    # ÁP DỤNG BỘ LỌC LÂM SÀNG
    df_filtered = df[df['TenBenh'].apply(is_clinical_term)]
    
    # Lấy mẫu từ danh sách đã được làm sạch
    sample_size = min(1000, len(df_filtered))
    df_sampled = df_filtered.sample(n=sample_size, random_state=42)
    
    output_path = "data/icd10_top.csv"
    df_sampled[['TenBenh']].to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ Đã lọc ra {len(df_sampled)} tên bệnh 'chuẩn bác sĩ'.")
    print("\n--- Mẫu 5 bệnh đầu tiên ---")
    print(df_sampled['TenBenh'].head(5).tolist())

if __name__ == "__main__":
    main()