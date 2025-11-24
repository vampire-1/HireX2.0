from .ranking_profiles import PROFILES, DEFAULT_PROFILE, COLLEGE_TIERS

def _norm(val, hi):
    try:
        return min(max(float(val)/float(hi), 0.0), 1.0)
    except Exception:
        return 0.0

def _college_norm(institutions):
    best = 0.0
    for inst in institutions or []:
        best = max(best, COLLEGE_TIERS.get(inst, 0.0))
    return best

def compute_score(item, weights, semantic_score):
    exp_norm = _norm(item.get("years_experience",0), 10)   # cap at 10y
    cgpa_norm = _norm(item.get("cgpa",0), 10)              # /10 scale
    college_norm = _college_norm(item.get("institutions",[]))
    extra_norm = _norm(item.get("extracurricular_score",0), 5)

    score = (weights["semantic"] * semantic_score +
             weights["exp"] * exp_norm +
             weights["cgpa"] * cgpa_norm +
             weights["college"] * college_norm +
             weights["extra"] * extra_norm)

    parts = {
        "semantic": round(semantic_score,3),
        "exp_norm": round(exp_norm,3),
        "cgpa_norm": round(cgpa_norm,3),
        "college_norm": round(college_norm,3),
        "extra_norm": round(extra_norm,3),
    }
    return score, parts
