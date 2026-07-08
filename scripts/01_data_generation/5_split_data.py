import json
import random
import os

def split_dataset(input_file, output_dir, train_ratio=0.8, valid_ratio=0.1):
    print("✂️ Đang tiến hành xáo trộn và chia tập dữ liệu...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
        
    # Xáo trộn ngẫu nhiên để phá vỡ thứ tự bệnh
    random.seed(42) # Cố định seed để có thể tái tạo lại đúng kết quả này
    random.shuffle(data)
    
    total = len(data)
    train_end = int(total * train_ratio)
    valid_end = train_end + int(total * valid_ratio)
    
    train_data = data[:train_end]
    valid_data = data[train_end:valid_end]
    test_data = data[valid_end:]
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Hàm ghi file
    def write_jsonl(data_list, filename):
        path = os.path.join(output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"  -> Lưu {len(data_list):>4} mẫu vào {path}")

    write_jsonl(train_data, 'train.jsonl')
    write_jsonl(valid_data, 'valid.jsonl')
    write_jsonl(test_data, 'test.jsonl')
    
    print("✅ Hoàn tất chia tập!")

if __name__ == "__main__":
    split_dataset("data/emr_cleaned_dataset.jsonl", "data/split_dataset")