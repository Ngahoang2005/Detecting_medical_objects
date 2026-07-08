import json
import random
import requests
import re
import os
from tqdm import tqdm

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & KHUNG VĂN BẢN
# ==========================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"  # Khuyến nghị dùng bản 14b nếu đủ VRAM
SAMPLES_PER_DISEASE = 10   # Số mẫu cho mỗi bệnh

DOCUMENT_TYPES = [
    {
        "name": "Bệnh án khám vào viện",
        "style": "Chia rõ các phần: [Lý do vào viện], [Bệnh sử - mô tả diễn biến chi tiết], [Khám lâm sàng], và [Cận lâm sàng].",
        "base_length": "CHI TIẾT (Khoảng 2 đến 3 đoạn văn)."
    },
    {
        "name": "Giấy ra viện",
        "style": "Văn phong hành chính, tổng kết quá trình. Gồm: Tóm tắt bệnh án, Chẩn đoán, Phương pháp điều trị, Lời dặn.",
        "base_length": "DÀI VÀ TOÀN DIỆN (Từ 2 đến 4 đoạn văn)."
    },
    {
        "name": "Ghi chú tiến triển hàng ngày (SOAP)",
        "style": "Cấu trúc 4 phần: S (Chủ quan), O (Khách quan), A (Đánh giá), P (Kế hoạch).",
        "base_length": "TRUNG BÌNH. Dùng gạch đầu dòng chi tiết cho từng mục."
    },
    {
        "name": "Phiếu khám Cấp cứu",
        "style": "Văn phong khẩn trương. Tập trung ngay vào tình trạng nhập viện, sinh hiệu, và xử trí ban đầu.",
        "base_length": "VỪA PHẢI (Khoảng 1 đến 2 đoạn). Nhịp độ nhanh, y khoa đặc."
    },
    {
        "name": "Sổ tay ghi chú Điều dưỡng",
        "style": "Ngôn ngữ thực dụng, vắn tắt. Chỉ liệt kê dấu hiệu sinh tồn và xác nhận thực hiện y lệnh.",
        "base_length": "NGẮN GỌN (Khoảng 2 đến 4 dòng). Trực diện, không phân tích sâu."
    }
]

# ==========================================
# 2. NẠP DỮ LIỆU & TỪ ĐIỂN NHIỄU
# ==========================================
def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"❌ Lỗi: Không tìm thấy {filepath}")
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

print("📦 Đang nạp hệ sinh thái dữ liệu...")
KB_DATA = load_json("data/clinical_kb_perfect.json").get("entities", {})
SYNONYMS = load_json("data/synonyms.json")
ABBREVIATIONS = load_json("data/medical_abbreviations.json")
ALL_DISEASES = list(KB_DATA.keys())

# Hợp nhất từ điển (Ưu tiên Abbreviations)
NOISE_ENGINE = {}
for k, v in SYNONYMS.items(): NOISE_ENGINE[k.lower()] = v
for k, v in ABBREVIATIONS.items():
    if k.lower() in NOISE_ENGINE:
        NOISE_ENGINE[k.lower()] = list(set(NOISE_ENGINE[k.lower()] + v))
    else:
        NOISE_ENGINE[k.lower()] = v

# ==========================================
# 3. CÁC HÀM XỬ LÝ LÕI
# ==========================================
def get_noisy_variant(base_term, noise_prob):
    term_lower = base_term.lower().strip()
    if term_lower in NOISE_ENGINE and random.random() < noise_prob:
        return random.choice(NOISE_ENGINE[term_lower])
    return base_term

def call_llm(prompt):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL_NAME, 
            "prompt": prompt, 
            "stream": False,
            "options": {"temperature": 0.3, "top_p": 0.9}
        }, timeout=60)
        return response.json().get('response', '').strip()
    except Exception as e:
        return None

def generate_golden_sample(primary_disease, kb_info):
    noise_prob = random.choice([0.2, 0.5, 0.8])
    
    # Lấy ngẫu nhiên Document Type
    doc_config = random.choice(DOCUMENT_TYPES)
    
    # ---------------------------------------------------------
    # ĐỘNG CƠ ĐỘ PHỨC TẠP (COMPLEXITY ENGINE)
    # ---------------------------------------------------------
    # Sinh 0 đến 3 bệnh kèm theo (Tỷ lệ: 0: 40%, 1: 30%, 2: 20%, 3: 10%)
    num_comorb = random.choices([0, 1, 2, 3], weights=[0.4, 0.3, 0.2, 0.1])[0]
    comorbidities = []
    if num_comorb > 0:
        available_diseases = [d for d in ALL_DISEASES if d != primary_disease]
        comorbidities = random.sample(available_diseases, min(num_comorb, len(available_diseases)))
    
    complexity_level = len(comorbidities)
    if complexity_level == 0:
        complexity_instruction = "Bệnh cảnh ĐƠN GIẢN (chỉ 1 bệnh chính). Không cần viết quá dài dòng, đi thẳng vào trọng tâm."
    elif complexity_level == 1:
        complexity_instruction = "Bệnh cảnh TRUNG BÌNH (có 1 bệnh nền). Cần nhắc sơ qua bệnh nền nhưng tập trung xử lý bệnh chính."
    else:
        complexity_instruction = f"Bệnh cảnh PHỨC TẠP (có {complexity_level} bệnh nền). YÊU CẦU DÀNH THỜI GIAN PHÂN TÍCH sự tương tác của đa bệnh lý. Độ dài văn bản phải DÀI HƠN mức bình thường để phản ánh độ khó của ca bệnh."
    # ---------------------------------------------------------

    sym_raw = kb_info.get('symptoms', [])
    symptoms = random.sample(sym_raw, max(1, int(len(sym_raw) * random.uniform(0.6, 0.9))))
    present_sym = [s for s in symptoms if random.random() >= 0.2]
    negated_sym = [s for s in symptoms if s not in present_sym]
    
    drugs = random.sample(kb_info.get('drugs', []), max(1, int(len(kb_info.get('drugs', [])) * 0.8))) if kb_info.get('drugs') else []
    tests = random.sample(kb_info.get('tests', []), max(1, int(len(kb_info.get('tests', [])) * 0.7))) if kb_info.get('tests') else []
    
    expected_entities = {
        "DISEASE": [primary_disease] + comorbidities,
        "SYMPTOM_PRESENT": present_sym,
        "SYMPTOM_NEGATED": negated_sym,
        "TEST": tests,
        "DRUG": drugs
    }
    
    required_keywords = set()
    for lst in expected_entities.values(): required_keywords.update(lst)

    input_str = f"- CHẨN ĐOÁN CHÍNH: {primary_disease}\n"
    if comorbidities: input_str += f"- BỆNH NỀN / KÈM THEO: {', '.join(comorbidities)}\n"
    if present_sym: input_str += f"- TRIỆU CHỨNG CÓ: {', '.join(present_sym)}\n"
    if negated_sym: input_str += f"- TRIỆU CHỨNG KHÔNG CÓ: {', '.join(negated_sym)}\n"
    if tests: input_str += f"- XÉT NGHIỆM: {', '.join(tests)}\n"
    if drugs: input_str += f"- THUỐC: {', '.join(drugs)}\n"

    base_prompt = f"""Bạn là bác sĩ. Viết 1 bệnh án thuộc loại: {doc_config['name']}.
Dựa trên thông tin cốt lõi sau:
{input_str}

YÊU CẦU VỀ VĂN PHONG VÀ ĐỘ DÀI:
- Phong cách: {doc_config['style']}
- Khung độ dài cơ bản: {doc_config['base_length']}
- CHỈ ĐẠO ĐỘ PHỨC TẠP CA BỆNH: {complexity_instruction}

LUẬT:
1. KHÔNG thêm bệnh lý, triệu chứng, xét nghiệm hay hoạt chất mới.
2. ĐƯỢC PHÉP thêm: Tuổi, giới tính, sinh hiệu (mạch, HA, nhiệt độ), liều lượng thuốc, và câu văn nối cho tự nhiên.
3. BẮT BUỘC dùng chính xác các từ khóa y khoa đã cung cấp ở trên."""

    raw_text = call_llm(base_prompt)
    if not raw_text: return None

    # ==========================================
    # CƠ CHẾ TỰ ĐỘNG SỬA LỖI (LLM SELF-CORRECTION)
    # ==========================================
    found_in_raw = set()
    for kw in required_keywords:
        if re.search(re.escape(kw), raw_text, re.IGNORECASE):
            found_in_raw.add(kw)
            
    missing_kws = required_keywords - found_in_raw
    if len(missing_kws) > 1:
        retry_prompt = base_prompt + f"\n\nBản nháp trước của bạn đã bỏ sót các từ sau: {', '.join(missing_kws)}. Hãy viết lại và đảm bảo có đủ các từ này."
        raw_text = call_llm(retry_prompt)
        if not raw_text: return None

    # ==========================================
    # THUẬT TOÁN OFFSET CHỐNG CHỒNG LẤN
    # ==========================================
    matches = []
    for ent_type, ent_list in expected_entities.items():
        for ent_item in ent_list:
            if not ent_item: continue
            for m in re.finditer(re.escape(ent_item), raw_text, re.IGNORECASE):
                matches.append({
                    "start": m.start(), "end": m.end(), 
                    "orig_text": m.group(), "type": ent_type, "normalized": ent_item
                })
                
    # Ưu tiên chuỗi DÀI NHẤT
    matches = sorted(matches, key=lambda x: (-(x["end"] - x["start"])))
    
    occupied_spans = []
    filtered_matches = []
    for m in matches:
        is_overlap = any(max(m["start"], os[0]) < min(m["end"], os[1]) for os in occupied_spans)
        if not is_overlap:
            filtered_matches.append(m)
            occupied_spans.append((m["start"], m["end"]))
            
    filtered_matches = sorted(filtered_matches, key=lambda x: x["start"])
    
    # ==========================================
    # CẤY NHIỄU & GHI NHẬN OFFSET TUYỆT ĐỐI
    # ==========================================
    final_text = ""
    annotations = []
    curr_idx = 0
    
    for m in filtered_matches:
        final_text += raw_text[curr_idx:m["start"]] 
        noisy_entity = get_noisy_variant(m["orig_text"], noise_prob)
        
        start_offset = len(final_text)
        final_text += noisy_entity
        end_offset = len(final_text)
        
        # KIỂM ĐỊNH TUYỆT ĐỐI BẢO CHỨNG NHÃN
        if final_text[start_offset:end_offset] != noisy_entity:
            print("⚠️ Lỗi trượt Offset! Hủy mẫu.")
            return None
            
        annotations.append({
            "text": noisy_entity, "start": start_offset, "end": end_offset,
            "type": m["type"], "normalized": m["normalized"]
        })
        curr_idx = m["end"]
        
    final_text += raw_text[curr_idx:]
    
    return {
        "meta_data": {
            "document_type": doc_config['name'],
            "complexity_level": complexity_level,
            "comorbidities_count": num_comorb
        },
        "text": final_text, 
        "entities": annotations
    }

# ==========================================
# 4. CHẠY PIPELINE
# ==========================================
def main():
    output_path = "data/emr_dataset_master.jsonl"
    if os.path.exists(output_path): os.remove(output_path)
    
    print(f"🚀 BẮT ĐẦU CÀY DATA (Mục tiêu: {SAMPLES_PER_DISEASE} mẫu/bệnh)")
    
    # Test thử 3 bệnh đầu tiên. Chạy ổn thì đổi thành ALL_DISEASES
    test_diseases = ALL_DISEASES[:3]
    
    for disease in tqdm(test_diseases, desc="Tiến trình tổng"):
        info = KB_DATA[disease]
        valid_samples = 0
        attempts = 0
        max_attempts = SAMPLES_PER_DISEASE * 3
        
        while valid_samples < SAMPLES_PER_DISEASE and attempts < max_attempts:
            attempts += 1
            result = generate_golden_sample(disease, info)
            
            if result:
                valid_samples += 1
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    
        print(f"  -> {disease}: Thành công {valid_samples}/{SAMPLES_PER_DISEASE} (Mất {attempts} lần thử)")

if __name__ == "__main__":
    main()