PROFILES = {
    "balanced":         {"semantic":0.45,"exp":0.20,"cgpa":0.15,"college":0.10,"extra":0.10},
    "cgpa-heavy":       {"semantic":0.30,"exp":0.15,"cgpa":0.40,"college":0.10,"extra":0.05},
    "experience-heavy": {"semantic":0.35,"exp":0.40,"cgpa":0.10,"college":0.10,"extra":0.05},
    "college-heavy":    {"semantic":0.35,"exp":0.15,"cgpa":0.15,"college":0.30,"extra":0.05},
    "leadership-heavy": {"semantic":0.35,"exp":0.20,"cgpa":0.10,"college":0.10,"extra":0.25},
}
DEFAULT_PROFILE = "balanced"

COLLEGE_TIERS = {"IIT":1.0,"BITS":0.9,"NIT":0.8}
