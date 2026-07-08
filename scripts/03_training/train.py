import torch
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import json

def main():
    # 1. Load model 4090 friendly
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-7B-Instruct", 
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained("unsloth/qwen2.5-7b-instruct-unsloth-bnb-4bit")

    model = FastLanguageModel.get_peft_model(
        model, r=16, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=16, lora_dropout=0, bias="none",
    )

    # 2. Load data
    dataset = load_dataset("json", data_files={
        "train": "data/competition_ready/train_comp.jsonl"
    })

    # 3. Formatting
    def formatting_prompts_func(examples):
        instructions = "Bạn là chuyên gia y tế. Trích xuất thực thể theo JSON."
        inputs = examples["input_text"]
        outputs = [json.dumps(o, ensure_ascii=False) for o in examples["output_json"]]
        return {"text": [f"<|im_start|>system\n{instructions}<|im_end|>\n<|im_user|>\n{i}<|im_end|>\n<|im_assistant|>\n{o}<|im_end|>" for i, o in zip(inputs, outputs)]}

    dataset = dataset.map(formatting_prompts_func, batched=True)

    
    # 4. Train
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"], 
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            per_device_train_batch_size=4, 
            gradient_accumulation_steps=4,
            max_steps=500, 
            learning_rate=2e-4,
            
            # SỬA TẠI ĐÂY:
            fp16=False,   # Chuyển thành False
            bf16=True,    # Chuyển thành True (Vì 4090 hỗ trợ bfloat16 cực tốt)
            
            logging_steps=1, 
            output_dir="models/outputs",
        ),
    )
    trainer.train()
    model.save_pretrained("models/final_model")
    tokenizer.save_pretrained("models/final_model")

if __name__ == "__main__":
    main()