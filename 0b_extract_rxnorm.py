import zipfile
import pandas as pd
import os

def main():
    zip_path = "RxNorm_full_prescribe_07062026.zip"
    print(f"Đang giải nén và đọc file {zip_path}...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # RxNorm cất file RRF trong thư mục 'rrf'
            with z.open('rrf/RXNCONSO.RRF') as f:
                # File RRF phân cách bằng dấu '|'
                df = pd.read_csv(f, sep='|', header=None, dtype=str, engine='python')
    except Exception as e:
        print(f"❌ LỖI: Không đọc được file ZIP. Chi tiết: {e}")
        return

    print("Đang lọc lấy Hoạt chất gốc (Ingredient)...")
    
    # Cấu trúc RxNorm: Cột 0: RXCUI, Cột 1: LAT (Ngôn ngữ), Cột 11: TTY (Loại từ), Cột 14: STR (Tên thuốc)
    # Chúng ta lọc lấy: Tiếng Anh (ENG) và Hoạt chất gốc (IN - Ingredient)
    df_filtered = df[(df[1] == 'ENG') & (df[11] == 'IN')]

    # Giữ lại đúng 2 cột quan trọng và đổi tên cho dễ hiểu
    df_clean = df_filtered[[0, 14]].rename(columns={0: 'RXCUI', 14: 'TenThuoc'})

    # Dọn dẹp trùng lặp
    df_clean = df_clean.drop_duplicates(subset=['TenThuoc'])

    os.makedirs("data", exist_ok=True)
    output_path = "data/rxnorm_clean.csv"
    df_clean.to_csv(output_path, index=False)
    
    print(f"✅ Đã tạo xong từ điển với {len(df_clean)} hoạt chất chuẩn!")
    print(df_clean.head())

if __name__ == "__main__":
    main()