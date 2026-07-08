import json
from unsloth import FastLanguageModel
from metrics import evaluate_metrics

def predict(model, tokenizer, text):
    inputs = tokenizer([f"<|im_start|>system\nTrích xuất JSON<|im_end|>\n<|im_user|>\n{text}<|im_end|>\n<|im_assistant|>\n"], return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=1024)
    return json.loads(tokenizer.decode(outputs[0], skip_special_tokens=True).split("<|im_assistant|>\n")[-1])

def main():
    model, tokenizer = FastLanguageModel.from_pretrained("models/final_model", local_files_only=True)
    FastLanguageModel.for_inference(model)
    
    results = []
    with open("data/competition_ready/test_comp.jsonl", 'r') as f:
        for line in f:
            data = json.loads(line)
            pred = predict(model, tokenizer, data['input_text'])
            results.append({"ground_truth": data['output_json'], "prediction": pred})
            
    with open("data/final_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False)
        
    # Tính điểm trung bình
    text_scores, assertions_scores, candidates_scores = zip(*[evaluate_metrics(rt['output_json'], pred['prediction']) for rt, pred in results])
    print(f"Text Score: {sum(text_scores)/len(text_scores)}")
    print(f"Assertions Score: {sum(assertions_scores)/len(assertions_scores)}")
    print(f"Candidates Score: {sum(candidates_scores)/len(candidates_scores)}")

if __name__ == "__main__":
    main()