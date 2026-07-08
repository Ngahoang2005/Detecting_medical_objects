import json
import matplotlib.pyplot as plt
import seaborn as sns

def plot_word_count_distribution(file_path):
    print(f"📊 Đang đọc dữ liệu từ {file_path}...")
    lengths = []
    
    # 1. Đọc và đếm số từ của từng mẫu
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                word_count = len(data['text'].split())
                lengths.append(word_count)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {file_path}")
        return

    if not lengths:
        print("⚠️ File trống hoặc không đọc được dữ liệu.")
        return

    avg_len = sum(lengths) / len(lengths)
    
    # 2. Cấu hình và vẽ biểu đồ
    plt.figure(figsize=(12, 6))
    
    # Dùng Seaborn vẽ Histogram kết hợp đường cong mật độ (KDE)
    sns.histplot(lengths, bins=40, kde=True, color='#2c3e50', edgecolor='white')
    
    # Vẽ thêm đường kẻ đỏ đánh dấu mức Trung bình
    plt.axvline(avg_len, color='#e74c3c', linestyle='dashed', linewidth=2, 
                label=f'Trung bình ({avg_len:.1f} từ)')
    
    # Trang trí biểu đồ
    plt.title('Phân phối Độ dài Văn bản (Tập dữ liệu Bệnh án EMR)', fontsize=16, pad=15)
    plt.xlabel('Số lượng từ (Word Count)', fontsize=12)
    plt.ylabel('Số lượng mẫu (Frequency)', fontsize=12)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    print("✨ Đang hiển thị biểu đồ...")
    plt.show()

if __name__ == "__main__":
    # Đảm bảo đường dẫn này trỏ đúng vào file SẠCH cuối cùng của bạn
    DATA_PATH = "data/emr_dataset_cleaned_final.jsonl"
    plot_word_count_distribution(DATA_PATH)