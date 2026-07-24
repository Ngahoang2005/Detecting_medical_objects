import json
import re

# 1. Định nghĩa ánh xạ nhãn
LABEL_MAPPING = {
    "SYMPTOM_AND_DISEASE": None,  # Cần xử lý đặc biệt
    "medical_procedure": "TÊN_XÉT_NGHIỆM",
    "MEDICINE": "THUỐC"
}

# 2. Hàm phân loại triệu chứng vs bệnh (cải thiện)
def classify_symptom_or_disease(entity_text, sentence=None, sent_label=None):
    """
    Phân loại entity là TRIỆU_CHỨNG hay CHẨN_ĐOÁN
    """
    # Từ khóa triệu chứng
    symptom_keywords = [
        "đau", "sốt", "ho", "mệt", "buồn nôn", "tức ngực", "khó thở",
        "ngứa", "sưng", "tê", "chóng mặt", "nhức", "ê buốt", "vàng",
        "khóc", "mẩn đỏ", "phát ban", "co giật", "run", "nôn", "ỉa chảy"
    ]
    
    # Từ khóa bệnh (để tránh nhầm lẫn)
    disease_keywords = [
        "ung thư", "viêm", "hội chứng", "bệnh", "tăng huyết áp", 
        "đái tháo đường", "suy tim", "thiếu máu", "vàng da nhân não"
    ]
    
    entity_lower = entity_text.lower()
    
    # Kiểm tra có phải bệnh không (ưu tiên cao hơn)
    for keyword in disease_keywords:
        if keyword in entity_lower:
            return "CHẨN_ĐOÁN"
    
    # Kiểm tra có phải triệu chứng không
    for keyword in symptom_keywords:
        if keyword in entity_lower:
            return "TRIỆU_CHỨNG"
    
    # Nếu không xác định, dùng sent_label để suy luận
    if sent_label:
        if sent_label in ["method_diagnosis", "causes"]:
            return "CHẨN_ĐOÁN"
        elif sent_label in ["treatment"]:
            return "TRIỆU_CHỨNG"
    
    # Mặc định là triệu chứng
    return "TRIỆU_CHỨNG"

# 3. Hàm lấy text từ vị trí index
def get_entity_text(sentence, start_idx, end_idx):
    """
    Lấy text từ vị trí index (dựa trên từ)
    """
    # Tách câu thành các từ
    words = sentence.split()
    
    # Lấy các từ từ start_idx đến end_idx
    if 0 <= start_idx < len(words) and 0 <= end_idx < len(words):
        entity_words = words[start_idx:end_idx + 1]
        return " ".join(entity_words)
    return None

# 4. Hàm chuyển đổi một sample
def convert_vimq_sample(sample):
    """
    Chuyển đổi sample từ định dạng ViMQ sang format bài toán
    """
    sentence = sample.get('sentence', '')
    seq_labels = sample.get('seq_label', [])
    sent_label = sample.get('sent_label', '')
    
    converted_entities = []
    
    # Duyệt qua các entity trong seq_label
    for entity_info in seq_labels:
        if len(entity_info) < 3:
            continue
            
        start_idx, end_idx, original_type = entity_info
        
        # Lấy text của entity từ câu
        entity_text = get_entity_text(sentence, start_idx, end_idx)
        if not entity_text:
            continue
        
        # Tìm nhãn mới
        new_type = LABEL_MAPPING.get(original_type)
        
        # Xử lý đặc biệt cho SYMPTOM_AND_DISEASE
        if original_type == "SYMPTOM_AND_DISEASE":
            new_type = classify_symptom_or_disease(
                entity_text, 
                sentence, 
                sent_label
            )
        
        if new_type is not None:
            # Tìm vị trí trong câu (tính theo ký tự)
            char_start = find_entity_position(sentence, entity_text, start_idx)
            char_end = char_start + len(entity_text)
            
            converted_entities.append({
                'text': entity_text,
                'type': new_type,
                'position': [char_start, char_end]
            })
    
    # Tạo sample mới
    return {
        'sentence': sentence,
        'ner_tags': converted_entities,
        'sent_label': sent_label
    }

# 5. Hàm tìm vị trí ký tự của entity
def find_entity_position(sentence, entity_text, word_start_idx):
    """
    Tìm vị trí ký tự bắt đầu của entity trong câu
    """
    words = sentence.split()
    
    # Tìm vị trí ký tự bắt đầu
    char_pos = 0
    for i in range(word_start_idx):
        char_pos += len(words[i]) + 1  # +1 cho khoảng trắng
    
    # Đảm bảo không bị lệch do dấu gạch dưới
    # (ViMQ dùng _ để nối các từ trong entity)
    # Tìm vị trí thực tế trong câu gốc
    word = words[word_start_idx]
    
    # Tìm từ trong câu từ vị trí char_pos
    while char_pos < len(sentence):
        if sentence[char_pos:char_pos + len(word)] == word:
            break
        char_pos += 1
    
    return char_pos

# 6. Hàm xử lý toàn bộ file
def convert_dataset(input_file_path, output_file_path):
    """
    Chuyển đổi toàn bộ dataset
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        converted_dataset = []
        for sample in dataset:
            converted_sample = convert_vimq_sample(sample)
            converted_dataset.append(converted_sample)
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(converted_dataset, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Chuyển đổi thành công! File được lưu tại: {output_file_path}")
        print(f"📊 Số samples: {len(converted_dataset)}")
        
        # In thử 1 sample để kiểm tra
        if converted_dataset:
            print("\n🔍 Ví dụ sample đầu tiên:")
            print(json.dumps(converted_dataset[0], ensure_ascii=False, indent=2))
    
    except FileNotFoundError:
        print(f"❌ Lỗi: Không tìm thấy file {input_file_path}")
    except json.JSONDecodeError:
        print(f"❌ Lỗi: File {input_file_path} không đúng định dạng JSON.")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi: {e}")
        import traceback
        traceback.print_exc()

# 7. Chạy chương trình
if __name__ == "__main__":
    input_file = "train.json"
    output_file = "train_converted.json"
    convert_dataset(input_file, output_file)