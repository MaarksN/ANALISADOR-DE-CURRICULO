def score_text(text: str, keywords: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for k in keywords if k.lower() in t)

def decide(score: int) -> str:
    if score >= 5: return "apply"
    if score >= 3: return "needs_manual"
    return "skip"
