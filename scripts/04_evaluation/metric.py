import jiwer

def calculate_jaccard(gt_list, pred_list):
    gt_set, pred_set = set(gt_list), set(pred_list)
    if not gt_set and not pred_set: return 1.0
    if not gt_set or not pred_set: return 0.0
    return len(gt_set.intersection(pred_set)) / len(gt_set.union(pred_set))

def evaluate_metrics(ground_truth_list, prediction_list):
    # ground_truth_list và prediction_list là list các dict thực thể
    total_text_score = 0
    total_assertions_score = 0
    total_candidates_score = 0
    
    # Ở đây giả định bạn so sánh theo thứ tự hoặc bằng cách tìm kiếm (matching)
    # Cách đơn giản nhất là duyệt qua và so sánh:
    for gt, pred in zip(ground_truth_list, prediction_list):
        # Tính WER trên text
        wer = jiwer.wer(gt.get('text', ''), pred.get('text', ''))
        total_text_score += (1 - wer)
        
        # Tính Jaccard cho assertions
        total_assertions_score += calculate_jaccard(gt.get('assertions', []), pred.get('assertions', []))
        
        # Tính Jaccard cho candidates
        total_candidates_score += calculate_jaccard(gt.get('candidates', []), pred.get('candidates', []))
        
    n = len(ground_truth_list)
    return total_text_score/n, total_assertions_score/n, total_candidates_score/n