import os
import json
import openai
import zipfile

# Kết nối với Local LLM (Ollama/vLLM đang chạy trên RTX 4090)
client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="local-llm"
)

SYSTEM_PROMPT = """Bạn là chuyên gia xử lý dữ liệu Y tế. Đọc văn bản và trả về định dạng JSON thuần túy gồm 2 mảng:
{
  "typos": ["từ lỗi 1", "từ lỗi 2"],
  "garbage_sentences": ["câu kể lể rác 1", "câu kể lể rác 2"]
}"""

def analyze_noise_with_llm(text_content):
    try:
        response = client.chat.completions.create(
            # ĐÃ ĐỔI TÊN MODEL Ở ĐÂY CHO KHỚP VỚI OLLAMA TRÊN MÁY BẠN
            model="qwen2.5:7b", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Phân tích đoạn bệnh án sau:\n\n{text_content}"}
            ],
            temperature=0.3, # Để nhiệt độ thấp để LLM phân tích logic, tránh ảo giác
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Lỗi khi gọi LLM: {e}")
        return {"typos": [], "garbage_sentences": []}

def main():
    # ĐÃ ĐỔI ĐẦU VÀO THÀNH FILE ZIP CỦA BẠN
    zip_path = "data/input_turn2_vong1.zip" 
    output_report = "noise_report.json"
    
    total_report = []
    
    # Kiểm tra xem file zip có nằm đúng cùng thư mục với script này không
    if not os.path.exists(zip_path):
        print(f"❌ Không tìm thấy file {zip_path}. Vui lòng để file zip cùng thư mục với đoạn code này!")
        return
        
    print(f"🚀 Bắt đầu dùng LLM quét nhiễu trực tiếp từ file nén: {zip_path}...")
    
    # Mở và đọc trực tiếp từ file zip
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Lọc ra danh sách các file .txt bên trong (bỏ qua các thư mục hoặc file ẩn của hđh)
        txt_files = [f for f in zip_ref.namelist() if f.endswith('.txt') and not f.startswith('__MACOSX')]
        
        print(f"📂 Tìm thấy {len(txt_files)} file .txt trong zip. Bắt đầu quét...")
        
        for i, filename in enumerate(txt_files):
            print(f"Đang phân tích [{i+1}/{len(txt_files)}]: {os.path.basename(filename)}")
            
            # Đọc nội dung text bên trong từng file
            with zip_ref.open(filename) as f:
                content = f.read().decode('utf-8')
                
            analysis = analyze_noise_with_llm(content)
            
            total_report.append({
                "file_name": os.path.basename(filename),
                "typos": analysis.get("typos", []),
                "garbage_sentences": analysis.get("garbage_sentences", [])
            })
            
    # Lưu báo cáo tổng hợp
    with open(output_report, 'w', encoding='utf-8') as f:
        json.dump(total_report, f, ensure_ascii=False, indent=4)
        
    print(f"✅ Đã quét xong! Kết quả lưu tại: {output_report}")
    print("💡 Giờ bạn có thể mang file noise_report.json này lên Google Colab để vẽ biểu đồ phân phối lỗi.")

if __name__ == "__main__":
    main()