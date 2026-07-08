import json
from unsloth import FastLanguageModel
from metrics import evaluate_metrics

def predict(model, tokenizer, text):
    inputs = tokenizer([f"<|im_start|>system\nTrích xuất JSON<|im_end|>\n<|im_user|>\n{text}<|im_end|>\n<|im_assistant|>\n"], return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=1024)
    return json.loads(tokenizer.decode(outputs[0], skip_special_tokens=True).split("<|im_assistant|>\n")[-1])

def main():
    model, tokenizer = FastLanguageModel.from_pretrained("models/final_model", local_files_only=True)
    with open("data/competition_ready/test_comp.jsonl", 'r') as f:
        for line in f:
            data = json.loads(line)
            pred = predict(model, tokenizer, data['input_text'])
            # Tính điểm tại đây
            print(evaluate_metrics(data['output_json'], pred))

if __name__ == "__main__":
    main()