import re
from typing import List, Dict, Set

# Canonical role tags (keep simple, readable)
ROLES: Set[str] = {
    "frontend", "backend", "fullstack", "web", "mobile",
    "ios", "android",
    "devops", "sre", "mlops",
    "ml", "ai", "data-engineer", "analytics-engineer", "bi-engineer",
    "research-scientist",
    "security", "appsec", "cloud-security",
    "cloud", "distributed-systems", "systems",
    "embedded", "networking",
    "vr", "gaming", "crypto",
    "qa", "developer-advocate",
    "salesforce", "workday", "forward-deployed",
    "production-engineer", "quant", "linguistics",
    "bioinformatics",
    "engineering-manager",  # manager track
}

# Aliases / titles -> canonical role tags
ROLE_ALIASES: Dict[str, str] = {
    # Web / Frontend
    "frontend engineer": "frontend",
    "frontend developer": "frontend",
    "react developer": "frontend",
    "reactjs developer": "frontend",
    "next.js developer": "frontend",
    "web developer": "web",
    "ux engineer": "frontend",
    "ui engineer": "frontend",

    # Backend / Fullstack
    "backend engineer": "backend",
    "backend developer": "backend",
    "server-side engineer": "backend",
    "full-stack engineer": "fullstack",
    "full stack engineer": "fullstack",
    "full-stack developer": "fullstack",

    # Mobile
    "ios engineer": "ios",
    "ios developer": "ios",
    "android engineer": "android",
    "android developer": "android",
    "mobile engineer": "mobile",
    "mobile developer": "mobile",

    # DevOps / SRE
    "devops engineer": "devops",
    "site reliability engineer": "sre",
    "sre": "sre",
    "ml ops engineer": "mlops",
    "mlops engineer": "mlops",

    # ML / AI / Data / Research
    "machine learning engineer": "ml",
    "ml engineer": "ml",
    "ai engineer": "ai",
    "ai researcher": "ai",
    "research scientist": "research-scientist",
    "data engineer": "data-engineer",
    "analytics engineer": "analytics-engineer",
    "business intelligence engineer": "bi-engineer",
    "bioinformatics engineer": "bioinformatics",

    # Security
    "security software engineer": "security",
    "application security engineer": "appsec",
    "appsec engineer": "appsec",
    "cloud security engineer": "cloud-security",

    # Cloud / Systems
    "cloud engineer": "cloud",
    "distributed systems engineer": "distributed-systems",
    "systems engineer": "systems",
    "networking engineer": "networking",
    "embedded systems engineer": "embedded",
    "embedded software engineer": "embedded",

    # Platforms / Apps
    "salesforce developer": "salesforce",
    "workday engineer": "workday",
    "forward deployed software engineer": "forward-deployed",
    "production software engineer": "production-engineer",
    "developer advocate": "developer-advocate",

    # Niche
    "video game software engineer": "gaming",
    "game developer": "gaming",
    "vr engineer": "vr",
    "crypto engineer": "crypto",
    "quantitative developer": "quant",
    "linguistic engineer": "linguistics",

    # QA
    "qa engineer": "qa",
    "quality assurance engineer": "qa",

    # Management
    "software engineering manager": "engineering-manager",
}

# Skill -> role signals (not exclusive; a resume can get multiple tags)
SKILL_TO_ROLES: Dict[str, List[str]] = {
    # Frontend
    "react": ["frontend"], "next.js": ["frontend"], "redux": ["frontend"],
    "vue": ["frontend"], "angular": ["frontend"], "svelte": ["frontend"],
    "tailwind": ["frontend"], "css": ["frontend"], "html": ["frontend"],

    # Backend
    "node": ["backend"], "express": ["backend"], "django": ["backend"],
    "flask": ["backend"], "spring": ["backend"], "go": ["backend"], "rust": ["backend"],

    # Fullstack hint
    "graphql": ["fullstack"], "rest": ["fullstack"],

    # Mobile
    "swift": ["ios"], "objective-c": ["ios"],
    "kotlin": ["android"], "java": ["android"],
    "react native": ["mobile"], "flutter": ["mobile"],

    # DevOps / SRE
    "docker": ["devops", "sre"], "kubernetes": ["devops", "sre"],
    "terraform": ["devops"], "ansible": ["devops"],
    "aws": ["devops", "cloud"], "gcp": ["devops", "cloud"], "azure": ["devops", "cloud"],
    "prometheus": ["sre"], "grafana": ["sre"], "nginx": ["sre"],
    "ci/cd": ["devops"],

    # Data / ML
    "spark": ["data-engineer"], "kafka": ["data-engineer"],
    "airflow": ["data-engineer"],
    "pytorch": ["ml"], "tensorflow": ["ml"], "sklearn": ["ml"],
    "xgboost": ["ml"], "opencv": ["ml"],
    "mlflow": ["mlops"], "kubeflow": ["mlops"], "sagemaker": ["mlops"],

    # Security
    "burp": ["appsec"], "zap": ["appsec"], "threat modeling": ["security"],
    "iam": ["cloud-security"], "cspm": ["cloud-security"],

    # Systems / Distributed
    "grpc": ["distributed-systems"], "distributed": ["distributed-systems"],
    "os": ["systems"], "kernel": ["systems"],

    # Networking / Embedded
    "tcp/ip": ["networking"], "fpga": ["embedded"], "rtos": ["embedded"],

    # BI / Analytics
    "tableau": ["bi-engineer"], "power bi": ["bi-engineer"],

    # Research
    "paper": ["research-scientist"], "arxiv": ["research-scientist"],
}

# Role -> common core skills (used to expand recruiter prompt)
ROLE_TO_CORE_SKILLS: Dict[str, List[str]] = {
    "frontend": ["react", "next.js", "javascript", "typescript", "html", "css", "tailwind"],
    "backend": ["node", "express", "python", "django", "flask", "go", "java", "spring"],
    "fullstack": ["react", "node"],
    "ios": ["swift", "objective-c"],
    "android": ["kotlin", "java"],
    "mobile": ["flutter", "react native"],
    "devops": ["docker", "kubernetes", "terraform", "aws", "ci/cd"],
    "sre": ["kubernetes", "prometheus", "grafana", "nginx"],
    "mlops": ["mlflow", "kubeflow", "sagemaker", "docker", "kubernetes"],
    "ml": ["pytorch", "tensorflow", "sklearn", "xgboost"],
    "ai": ["pytorch", "transformers"],
    "data-engineer": ["spark", "kafka", "airflow", "sql"],
    "analytics-engineer": ["dbt", "sql"],
    "bi-engineer": ["tableau", "power bi", "sql"],
    "security": ["threat modeling"], "appsec": ["zap", "burp"], "cloud-security": ["iam"],
    "cloud": ["aws", "gcp", "azure"],
    "distributed-systems": ["grpc"],
    "systems": ["c", "c++", "os"],
    "embedded": ["c", "fpga", "rtos"],
    "networking": ["tcp/ip"],
    "gaming": ["unity", "unreal"],
    "vr": ["unity"],
    "crypto": ["solidity"],
    "qa": ["jest", "cypress", "playwright"],
    "developer-advocate": ["documentation", "talks"],
    "salesforce": ["apex"],
    "workday": ["workday"],
    "forward-deployed": ["python", "react"],
    "production-engineer": ["linux", "nginx"],
    "quant": ["python", "numpy", "pandas"],
    "linguistics": ["nlp"],
    "bioinformatics": ["python", "rna", "genomics"],
    "engineering-manager": ["leadership", "management"],
}

def normalize_role_text(txt: str) -> List[str]:
    low = txt.lower()
    found = set()
    # alias pass
    for k, v in ROLE_ALIASES.items():
        if re.search(rf"\b{re.escape(k)}\b", low):
            found.add(v)
    # direct canonical tokens
    for r in ROLES:
        if re.search(rf"\b{re.escape(r)}\b", low):
            found.add(r)
    return sorted(found)

def roles_from_skills(skills: List[str]) -> List[str]:
    out = set()
    for s in skills:
        out.update(SKILL_TO_ROLES.get(s, []))
    return sorted(out)

def expand_skills_for_roles(roles: List[str]) -> List[str]:
    out = set()
    for r in roles:
        out.update(ROLE_TO_CORE_SKILLS.get(r, []))
    return sorted(out)

def extract_roles_from_resume(text: str, skills: List[str]) -> List[str]:
    # combine signals from titles + skills
    from_titles = normalize_role_text(text)
    from_sk = roles_from_skills(skills)
    return sorted(set(from_titles) | set(from_sk))
