import zipfile
import pandas as pd
import os

def main():
    zip_path = "RxNorm_full_prescribe_07062026.zip"
    print(f"Đang giải nén và đọc file {zip_path}...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            with z.open('rrf/RXNCONSO.RRF') as f:
                # Đọc file RRF phân cách bằng dấu '|'
                df = pd.read_csv(f, sep='|', header=None, dtype=str, engine='python')
    except Exception as e:
        print(f"❌ LỖI: Không đọc được file ZIP. Chi tiết: {e}")
        return

    print("Đang định vị cột và lọc Hoạt chất gốc (Ingredient)...")
    
    # Lọc dữ liệu dựa trên các cột đã đối chiếu:
    # Cột 1 = Ngôn ngữ (ENG)
    # Cột 11 = Nguồn (RXNORM) - Để tránh lấy nhầm các nguồn phụ như MTHSPL
    # Cột 12 = Loại thuật ngữ (IN - Ingredient)
    df_filtered = df[(df[1] == 'ENG') & (df[11] == 'RXNORM') & (df[12] == 'IN')]

    # Trích xuất đúng Cột 0 (Mã RXCUI) và Cột 14 (Tên thuốc)
    df_clean = df_filtered[[0, 14]].rename(columns={0: 'RXCUI', 14: 'TenThuoc'})

    # Dọn dẹp trùng lặp
    df_clean = df_clean.drop_duplicates(subset=['TenThuoc'])

    os.makedirs("data", exist_ok=True)
    output_path = "data/rxnorm_clean.csv"
    df_clean.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"✅ Đã tạo xong từ điển với {len(df_clean)} hoạt chất chuẩn!")
    print(df_clean.head())

if __name__ == "__main__":
    main()