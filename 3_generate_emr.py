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
MODEL_NAME = "qwen2.5:7b"  # Nên dùng bản 14B nếu máy bạn đủ mạnh (12-16GB VRAM)
SAMPLES_PER_DISEASE = 10

# Phân bổ Cấu trúc và Độ nhiễu (Noise) sát thực tế
DOCUMENT_TYPES = [
    {
        "name": "Giấy ra viện (Discharge Summary)",
        "style": "Hành chính, trang trọng, viết thành các đoạn văn xuôi dài.",
        "base_length": "DÀI (2-3 đoạn văn).",
        "noise_level": 0.15 # Rất chuẩn, ít viết tắt
    },
    {
        "name": "Bệnh án khám vào viện",
        "style": "Chia rõ: [Lý do vào viện], [Bệnh sử], [Khám lâm sàng], [Cận lâm sàng].",
        "base_length": "CHI TIẾT.",
        "noise_level": 0.35 # Có viết tắt thông dụng
    },
    {
        "name": "Ghi chú tiến triển hàng ngày (SOAP)",
        "style": "TUYỆT ĐỐI tuân thủ 4 gạch đầu dòng: S (Triệu chứng bệnh nhân kể), O (Khám & Sinh hiệu), A (Chẩn đoán), P (Điều trị).",
        "base_length": "TRUNG BÌNH, liệt kê gạch đầu dòng ngắn gọn.",
        "noise_level": 0.55 # Bác sĩ viết nhanh cho nhau
    },
    {
        "name": "Phiếu khám Cấp cứu",
        "style": "Khẩn trương, dồn dập. Ghi nhận nhanh sinh hiệu, tình trạng và xử trí.",
        "base_length": "NGẮN (1 đoạn).",
        "noise_level": 0.65 
    },
    {
        "name": "Sổ tay ghi chú Điều dưỡng",
        "style": "Siêu vắn tắt, thực dụng. Ghi ngày giờ, sinh hiệu, tình trạng, y lệnh đã làm.",
        "base_length": "CỰC NGẮN (2-3 dòng, không phân tích, không viết thành câu hoàn chỉnh).",
        "noise_level": 0.85 # Viết tắt vô tội vạ, có lóng
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
    """Bơm nhiễu đồng nghĩa/viết tắt theo tỷ lệ của loại văn bản"""
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

def generate_patient_vitals():
    """Python tự sinh thông số y khoa (chống overfit)"""
    age = random.randint(18, 90)
    hr = random.randint(55, 130)
    bp = f"{random.randint(90, 170)}/{random.randint(60, 100)}"
    temp = round(random.uniform(36.0, 39.5), 1)
    return f"Tuổi: {age}, Mạch: {hr} l/p, HA: {bp} mmHg, Nhiệt độ: {temp}°C"

def generate_golden_sample(primary_disease, kb_info):
    # Lấy ngẫu nhiên Document Type & Mức độ Nhiễu tương ứng
    doc_config = random.choice(DOCUMENT_TYPES)
    noise_prob = doc_config["noise_level"]
    
    # ---------------------------------------------------------
    # COMPLEXITY ENGINE (Bệnh nền ngẫu nhiên)
    # ---------------------------------------------------------
    num_comorb = random.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
    comorbidities = []
    if num_comorb > 0:
        available = [d for d in ALL_DISEASES if d != primary_disease]
        comorbidities = random.sample(available, min(num_comorb, len(available)))
    
    # ---------------------------------------------------------
    # SUBSET SAMPLING (Thực thể ngẫu nhiên)
    # ---------------------------------------------------------
    sym_raw = kb_info.get('symptoms', [])
    symptoms = random.sample(sym_raw, max(1, int(len(sym_raw) * random.uniform(0.5, 0.8))))
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

    vitals_str = generate_patient_vitals()

    # ---------------------------------------------------------
    # PROMPT THÉP (NEGATIVE CONSTRAINTS)
    # ---------------------------------------------------------
    input_str = f"- HÀNH CHÍNH & SINH HIỆU BẮT BUỘC: {vitals_str}\n"
    input_str += f"- CHẨN ĐOÁN CHÍNH: {primary_disease}\n"
    if comorbidities: input_str += f"- BỆNH NỀN KÈM THEO: {', '.join(comorbidities)}\n"
    if present_sym: input_str += f"- TRIỆU CHỨNG HIỆN CÓ: {', '.join(present_sym)}\n"
    if negated_sym: input_str += f"- TRIỆU CHỨNG HOÀN TOÀN KHÔNG CÓ: {', '.join(negated_sym)}\n"
    if tests: input_str += f"- XÉT NGHIỆM ĐÃ LÀM: {', '.join(tests)}\n"
    if drugs: input_str += f"- THUỐC KÊ ĐƠN: {', '.join(drugs)}\n"

    base_prompt = f"""Bạn là một BÁC SĨ LÂM SÀNG đang bận rộn. Viết 1 bệnh án loại: {doc_config['name']}.

THÔNG TIN BẮT BUỘC PHẢI DÙNG CHÍNH XÁC:
{input_str}

LUẬT THÉP (CẤM LÀM SAI):
1. VĂN PHONG VÀ ĐỘ DÀI: {doc_config['style']} {doc_config['base_length']}
2. KHÔNG tự sáng tạo thêm bệnh lý, triệu chứng, xét nghiệm hay thuốc ngoài danh sách trên.
3. PHẢI BÊ NGUYÊN các con số (Tuổi, Mạch, HA, Nhiệt độ) vào văn bản. Không tự bịa số khác.
4. TUYỆT ĐỐI KHÔNG DÙNG CÁC TỪ AI LẢM NHẢM: Cấm viết "Lưu ý:", "Ghi chú:", "Phân tích sự tương tác", "Bệnh án này được viết dựa trên", "Đánh giá toàn diện". Hãy trực tiếp ghi thông tin y khoa.
5. Chỉ trả về nội dung bệnh án, không giải thích gì thêm."""

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
    if len(missing_kws) > 0: # Ép gắt: Thiếu 1 từ cũng bắt viết lại
        retry_prompt = base_prompt + f"\n\nBản nháp trước của bạn ĐÃ BỎ SÓT các từ khóa y khoa này: {', '.join(missing_kws)}. Hãy viết lại và bắt buộc phải nhét các từ này vào."
        raw_text = call_llm(retry_prompt)
        if not raw_text: return None

    # Lọc bỏ các câu AI lảm nhảm (Safety Fallback) nếu LLM vẫn cố tình sinh ra
    raw_lines = raw_text.split('\n')
    clean_lines = [line for line in raw_lines if not any(bad in line.lower() for bad in ["lưu ý:", "ghi chú:", "bệnh án này", "dựa trên thông tin", "theo yêu cầu"])]
    raw_text = '\n'.join(clean_lines).strip()

    # ==========================================
    # THUẬT TOÁN OFFSET (LONGEST-MATCH CHỐNG CHỒNG LẤN)
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
                
    # Ưu tiên chuỗi DÀI NHẤT ("đau bụng dưới" thắng "đau bụng")
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
    # CẤY NHIỄU THEO DOCUMENT TYPE & GHI NHẬN OFFSET TUYỆT ĐỐI
    # ==========================================
    final_text = ""
    annotations = []
    curr_idx = 0
    
    for m in filtered_matches:
        final_text += raw_text[curr_idx:m["start"]] 
        noisy_entity = get_noisy_variant(m["orig_text"], noise_prob) # Noise theo type
        
        start_offset = len(final_text)
        final_text += noisy_entity
        end_offset = len(final_text)
        
        # KIỂM ĐỊNH TUYỆT ĐỐI BẢO CHỨNG NHÃN (ASSERTION)
        if final_text[start_offset:end_offset] != noisy_entity:
            # Nếu logic nối chuỗi bị sai, bỏ qua mẫu này để tránh hỏng dữ liệu train
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
            "noise_level": noise_prob,
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
    test_diseases = ALL_DISEASES
    
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