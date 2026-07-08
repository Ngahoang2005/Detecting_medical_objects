import jiwer

def calculate_jaccard(gt_list, pred_list):
    gt_set, pred_set = set(gt_list), set(pred_list)
    if not gt_set and not pred_set: return 1.0
    if not gt_set or not pred_set: return 0.0
    return len(gt_set.intersection(pred_set)) / len(gt_set.union(pred_set))

def evaluate_metrics(ground_truth, prediction):
    wer = jiwer.wer(ground_truth.get('text', ''), prediction.get('text', ''))
    text_score = 1 - wer
    assertions_score = calculate_jaccard(ground_truth.get('assertions', []), prediction.get('assertions', []))
    candidates_score = calculate_jaccard(ground_truth.get('candidates', []), prediction.get('candidates', []))
    return text_score, assertions_score, candidates_score