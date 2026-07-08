import json
import os
from underthesea import word_tokenize
from tqdm import tqdm

def align_tokens_and_labels(text, entities):
    """
    Thuật toán dán nhãn BIO chính xác tuyệt đối bằng Mặt nạ Ký tự (Character Masking)
    """
    # 1. Tạo mặt nạ nhãn cho từng ký tự một
    char_tags = ['O'] * len(text)
    for ent in entities:
        start, end = ent['start'], ent['end']
        label = ent['type']
        
        # Bỏ qua nếu tọa độ bị lỗi (vượt quá chiều dài chuỗi)
        if start >= len(text) or end > len(text):
            continue
            
        char_tags[start] = f"B-{label}"
        for i in range(start + 1, end):
            char_tags[i] = f"I-{label}"

    # 2. Tách từ tiếng Việt (Word Segmentation)
    # underthesea sẽ gom "Bệnh nhân" thành 1 token
    raw_tokens = word_tokenize(text)
    
    aligned_tokens = []
    aligned_labels = []
    curr_char_idx = 0
    
    for token in raw_tokens:
        # Tìm vị trí bắt đầu của token này trong chuỗi gốc
        start_idx = text.find(token, curr_char_idx)
        if start_idx == -1:
            start_idx = curr_char_idx # Fallback an toàn
            
        end_idx = start_idx + len(token)
        
        # 3. Quyết định nhãn cho Token dựa trên mặt nạ ký tự
        token_tags = char_tags[start_idx:end_idx]
        token_label = 'O'
        
        # Ưu tiên nhãn B- (Begin), nếu không có thì lấy I- (Inside)
        for tag in token_tags:
            if tag.startswith('B-'):
                token_label = tag
                break
            elif tag.startswith('I-'):
                token_label = tag
                
        # 4. Nối từ ghép tiếng Việt bằng dấu gạch dưới (Chuẩn đầu vào của PhoBERT)
        formatted_token = token.replace(" ", "_")
        
        aligned_tokens.append(formatted_token)
        aligned_labels.append(token_label)
        
        curr_char_idx = end_idx
        
    return aligned_tokens, aligned_labels

def convert_to_huggingface_format(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    splits = ['train.jsonl', 'valid.jsonl', 'test.jsonl']
    
    # Gom tất cả các nhãn (tags) lại để làm từ điển
    unique_tags = set(['O'])
    
    for split in splits:
        input_path = os.path.join(input_dir, split)
        output_path = os.path.join(output_dir, split.replace('.jsonl', '_bio.json'))
        
        if not os.path.exists(input_path):
            print(f"⚠️ Bỏ qua {split} vì không tìm thấy file.")
            continue
            
        print(f"⚙️ Đang xử lý file: {split}...")
        hf_dataset = []
        
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for i, line in enumerate(tqdm(lines)):
            data = json.loads(line)
            tokens, ner_tags = align_tokens_and_labels(data['text'], data['entities'])
            
            unique_tags.update(ner_tags)
            
            # Format chuẩn của HuggingFace Datasets
            hf_dataset.append({
                "id": str(i),
                "tokens": tokens,
                "ner_tags": ner_tags
            })
            
        # Ghi ra file JSON chuẩn
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(hf_dataset, f, ensure_ascii=False, indent=2)
            
        print(f"  -> Đã lưu {len(hf_dataset)} mẫu chuẩn BIO vào {output_path}")

    # Lưu lại danh sách nhãn (Label list) để dùng lúc Training
    labels_list = sorted(list(unique_tags))
    with open(os.path.join(output_dir, 'label_list.json'), 'w', encoding='utf-8') as f:
        json.dump(labels_list, f, ensure_ascii=False, indent=2)
        
    print("\n" + "="*50)
    print("✅ TIỀN XỬ LÝ HOÀN TẤT!")
    print("Danh sách các Nhãn (Labels) đã phát hiện:")
    for idx, tag in enumerate(labels_list):
        print(f"  {idx}: {tag}")
    print("="*50)

if __name__ == "__main__":
    # Đọc dữ liệu từ thư mục split_dataset của bạn
    INPUT_DIR = "data/split_dataset"
    
    # Lưu dữ liệu đã tiền xử lý vào thư mục mới
    OUTPUT_DIR = "data/hf_ready_dataset"
    
    convert_to_huggingface_format(INPUT_DIR, OUTPUT_DIR)