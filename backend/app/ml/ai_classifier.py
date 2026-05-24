import os
import numpy as np

def predict_ai_generated(text: str, model_path: str):
    # Dummy fallback heuristic
    score = np.random.uniform(10, 90)
    if len(text) > 1000:
        score += 10
    is_ai = score > 60
    return is_ai, round(float(score), 2)
