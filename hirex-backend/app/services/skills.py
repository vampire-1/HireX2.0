import json
import re
from typing import List, Tuple

# add these near HARD_SKILLS / ALIASES



MERN_EXPANSION = {"mern": ["mongodb", "express", "react", "node"]}

def extract_skills(text: str) -> List[str]:
    out = set(find_terms(text, HARD_SKILLS))
    low = text.lower()
    for k, v in ALIASES.items():
        if re.search(rf"\b{re.escape(k)}\b", low):
            out.add(v)
    # expand MERN into 4 skills if 'mern' found
    if "mern" in out:
        out.remove("mern")
        out.update(MERN_EXPANSION["mern"])
    return sorted(out)

# Expandable lexicons
HARD_SKILLS = [
    "c", "c++", "java", "python", "go", "ruby", "rust", "php", "kotlin", "swift",
    "javascript", "typescript", "node", "express", "react", "next.js", "redux",
    "vue", "angular", "svelte",
    "html", "css", "tailwind", "sass",
    "mongodb", "mysql", "postgresql", "sqlite", "redis", "elasticsearch",
    "graphql", "rest", "grpc",
    "docker", "kubernetes", "aws", "gcp", "azure", "lambda", "s3", "ec2",
    "terraform", "ansible",
    "hadoop", "spark", "kafka", "airflow",
    "tensorflow", "pytorch", "sklearn", "xgboost", "opencv", "nlp", "bert",
    "huggingface",
    "jest", "cypress", "playwright",
    "git", "github", "gitlab", "ci/cd", "mern", "mongo", "mongodb", "express.js", "express", "reactjs", "react", "node.js", "node"
]

ALIASES = {
    "node.js": "node", "reactjs": "react", "express.js": "express",
    "postgres": "postgresql", "tf": "tensorflow", "scikit-learn": "sklearn",
    "azure devops": "azure", "amazon web services": "aws",
}

ALIASES.update({
    "mern stack": "mern",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node",
    "node.js": "node",
    "expressjs": "express",
    "express.js": "express",
    "mongo": "mongodb",
})


SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem solving",
    "critical thinking", "ownership", "mentoring", "collaboration",
    "presentation", "time management", "empathy", "adaptability"
]

def find_terms(text: str, vocab: List[str]) -> List[str]:
    low = text.lower()
    found = set()
    for t in vocab:
        if re.search(rf"\b{re.escape(t)}\b", low):
            found.add(t)
    return sorted(found)

def extract_skills(text: str) -> List[str]:
    out = set(find_terms(text, HARD_SKILLS))
    low = text.lower()
    for k, v in ALIASES.items():
        if re.search(rf"\b{re.escape(k)}\b", low):
            out.add(v)
    return sorted(out)

def extract_soft_skills(text: str) -> List[str]:
    return find_terms(text, SOFT_SKILLS)

def to_json(lst: List[str]) -> str:
    return json.dumps(sorted(list(set(lst))), ensure_ascii=False)
