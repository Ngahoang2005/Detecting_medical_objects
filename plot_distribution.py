import json

def terminal_histogram(file_path, bins=20):
    print(f"⏳ Đang quét dữ liệu từ {file_path}...")
    lengths = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    text = json.loads(line)['text']
                    lengths.append(len(text.split()))
                except Exception:
                    pass
    except FileNotFoundError:
        print("❌ Không tìm thấy file!")
        return

    if not lengths:
        print("⚠️ File trống!")
        return

    # Sắp xếp để tính Percentile (Giá trị cực kỳ quan trọng khi Train NLP)
    lengths.sort()
    total = len(lengths)
    min_val, max_val = lengths[0], lengths[-1]
    avg_len = sum(lengths) / total
    
    p90 = lengths[int(total * 0.90)]
    p95 = lengths[int(total * 0.95)]
    p99 = lengths[int(total * 0.99)]

    print("\n" + "="*60)
    print(f"📊 THỐNG KÊ PHÂN PHỐI ĐỘ DÀI ({total} mẫu)")
    print("="*60)
    print(f" • Ngắn nhất : {min_val} từ")
    print(f" • Dài nhất  : {max_val} từ")
    print(f" • Trung bình: {avg_len:.1f} từ")
    print("-" * 60)
    print("🎯 ĐÁNH GIÁ RỦI RO CHIỀU DÀI CONTEXT (PERCENTILE):")
    print(f" • 90% bệnh án ngắn hơn hoặc bằng : {p90} từ")
    print(f" • 95% bệnh án ngắn hơn hoặc bằng : {p95} từ")
    print(f" • 99% bệnh án ngắn hơn hoặc bằng : {p99} từ")
    print("="*60)

    # Vẽ biểu đồ ASCII
    bin_width = (max_val - min_val) / bins
    histogram = [0] * bins
    
    for l in lengths:
        index = int((l - min_val) / bin_width)
        if index == bins: 
            index -= 1
        histogram[index] += 1
        
    max_freq = max(histogram)
    max_bar_length = 40 # Độ dài tối đa của thanh biểu đồ
    
    print("\n📉 BIỂU ĐỒ HISTOGRAM (Số từ -> Số lượng mẫu):")
    print("-" * 60)
    for i in range(bins):
        bin_start = min_val + i * bin_width
        bin_end = min_val + (i + 1) * bin_width
        count = histogram[i]
        
        # Tính toán chiều dài thanh Bar
        bar_len = int((count / max_freq) * max_bar_length)
        bar = "█" * bar_len
        
        print(f" [{bin_start:>3.0f} - {bin_end:>3.0f} từ] | {bar} ({count})")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    DATA_PATH = "data/emr_dataset_master.jsonl"
    terminal_histogram(DATA_PATH)