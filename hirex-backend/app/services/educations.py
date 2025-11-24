import json
import re
from typing import List, Dict

ELITE_INSTITUTES = {
    "IIT": ["iit", "i.i.t", "indian institute of technology"],
    "NIT": ["nit", "n.i.t", "national institute of technology"],
    "BITS": ["bits", "b.i.t.s", "bits pilani", "birla institute of technology", "birla institute of technology and science"],
}


DEGREES = [
    "b.tech", "btech", "b.e", "be", "bsc", "b.sc", "m.tech", "mtech", "m.e", "me",
    "mca", "mba", "phd", "ms", "bca", "bba"
]

MAJORS = [
    "computer science", "cse", "ece", "electrical", "mechanical", "civil",
    "information technology", "it", "ai", "ml", "data science", "electronics"
]

def extract_institutions(text: str) -> List[str]:
    low = text.lower()
    out = set()
    for canon, variants in ELITE_INSTITUTES.items():
        for v in variants:
            if re.search(rf"\b{re.escape(v)}\b", low):
                out.add(canon); break
    return sorted(out)

def extract_degrees(text: str) -> List[str]:
    low = text.lower()
    return sorted({d for d in DEGREES if re.search(rf"\b{re.escape(d)}\b", low)})

def extract_majors(text: str) -> List[str]:
    low = text.lower()
    return sorted({m for m in MAJORS if re.search(rf"\b{re.escape(m)}\b", low)})

def to_json(lst: List[str]) -> str:
    return json.dumps(sorted(list(set(lst))), ensure_ascii=False)
