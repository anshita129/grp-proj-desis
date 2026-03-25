# ai_engine/utils.py

def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default