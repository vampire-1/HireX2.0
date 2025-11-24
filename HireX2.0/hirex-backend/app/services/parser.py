import re
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from . import ocr as ocr_svc

try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    import docx2txt
except Exception:
    docx2txt = None

try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None  # optional


# ------------ File reading with OCR fallback ------------

def read_file_text(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    text = ""

    if suffix == ".pdf":
        if pdfplumber:
            try:
                parts = []
                with pdfplumber.open(p) as pdf:
                    for page in pdf.pages:
                        parts.append(page.extract_text() or "")
                text = "\n".join(parts)
            except Exception:
                text = ""
        if len((text or "").strip()) < 200:  # image-based PDF
            text = ocr_svc.ocr_pdf_path(str(p)) or text or ""
    elif suffix == ".docx" and docx2txt:
        try:
            text = docx2txt.process(str(p)) or ""
        except Exception:
            text = ""
    elif suffix in {".txt"}:
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            text = ""
    elif suffix in {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}:
        text = ocr_svc.ocr_image_path(str(p)) or ""
    else:
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            text = ""

    return text or ""


# ------------ Primitive entity extraction ------------

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+", re.I)
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9_/\-]+", re.I)
GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_\-]+", re.I)
PORTFOLIO_RE = re.compile(r"(https?://[^\s]+)", re.I)

def rough_parse(text: str) -> Dict[str, Any]:
    email = (EMAIL_RE.search(text) or [None])[0] if EMAIL_RE.search(text) else None
    phone = (PHONE_RE.search(text) or [None])[0] if PHONE_RE.search(text) else None
    linkedin = (LINKEDIN_RE.search(text) or [None])[0] if LINKEDIN_RE.search(text) else None
    github = (GITHUB_RE.search(text) or [None])[0] if GITHUB_RE.search(text) else None
    urls = PORTFOLIO_RE.findall(text) or []
    portfolio = None
    # pick a non-linkedin/github as portfolio
    for u in urls:
        if "linkedin.com" in u.lower() or "github.com" in u.lower():
            continue
        portfolio = u; break

    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "Candidate")
    name = first_line[:120]

    yrs = 0.0
    for m in re.findall(r"(\d+)\s*\+?\s*(?:years|yrs)", text, flags=re.I):
        try: yrs = max(yrs, float(m))
        except: pass

    return {"name": name, "email": email, "phone": phone, "linkedin": linkedin, "github": github,
            "portfolio": portfolio, "years_experience": yrs}


# ------------ Section heuristics ------------

SEC_EDU = re.compile(r"^\s*(education|academics)\b", re.I)
SEC_EXP = re.compile(r"^\s*(experience|work experience|employment)\b", re.I)
SEC_PROJ = re.compile(r"^\s*(projects?|academic projects?|personal projects?)\b", re.I)
SEC_CERT = re.compile(r"^\s*(certifications?|licenses?)\b", re.I)
SEC_ACHV = re.compile(r"^\s*(achievements?|awards?)\b", re.I)
SEC_PUBS = re.compile(r"^\s*(publications?|research)\b", re.I)
SEC_MISC = re.compile(r"^\s*(skills|tech skills|technical skills)\b", re.I)

BULLET = re.compile(r"^\s*[\u2022\-\*\•]\s+")

def _split_lines(text: str) -> List[str]:
    return [ln.rstrip() for ln in text.splitlines()]

def _collect_section(lines: List[str], start_idx: int) -> List[str]:
    buf = []
    for ln in lines[start_idx + 1 :]:
        if any(rx.search(ln) for rx in [SEC_EDU, SEC_EXP, SEC_PROJ, SEC_CERT, SEC_ACHV, SEC_PUBS, SEC_MISC]):
            break
        buf.append(ln)
    return buf


def extract_projects(text: str) -> List[dict]:
    lines = _split_lines(text)
    out: List[dict] = []
    for i, ln in enumerate(lines):
        if SEC_PROJ.search(ln):
            section = _collect_section(lines, i)
            # simple grouping by bullets / blank lines
            chunk = []
            for s in section + [""]:
                if s.strip() == "" and chunk:
                    title = chunk[0].strip().strip("-–•*")
                    desc = " ".join(x.strip() for x in chunk[:6])
                    out.append({"title": title[:120], "tech": [], "desc": desc[:600], "snippet": desc[:400]})
                    chunk = []
                else:
                    chunk.append(BULLET.sub("", s))
    return out


def _parse_date(s: str):
    if not dateparser: return None
    try:
        return dateparser.parse(s, fuzzy=True, default=None)
    except Exception:
        return None


def extract_experience(text: str) -> Tuple[List[dict], float]:
    lines = _split_lines(text)
    entries: List[dict] = []
    total_months = 0.0

    DATE_RANGE = re.compile(r"([A-Za-z]{3,9}\.? \d{4}|[0-9]{1,2}/\d{4}|[0-9]{4})\s*[-–]\s*(Present|[A-Za-z]{3,9}\.? \d{4}|[0-9]{1,2}/\d{4}|[0-9]{4})", re.I)

    for i, ln in enumerate(lines):
        if SEC_EXP.search(ln):
            sec = _collect_section(lines, i)
            buffer = []
            for s in sec + [""]:
                if s.strip() == "" and buffer:
                    block = " ".join(buffer)
                    # crude role/company split
                    role = buffer[0][:120].strip()
                    m = DATE_RANGE.search(block)
                    dur_m = None
                    if m:
                        a, b = m.group(1), m.group(2)
                        d1 = _parse_date(a)
                        d2 = None if b.lower() == "present" else _parse_date(b)
                        if d1:
                            from datetime import datetime as dt
                            end = d2 or dt.utcnow()
                            months = (end.year - d1.year) * 12 + (end.month - d1.month)
                            dur_m = max(0, months)
                            total_months += dur_m
                    entries.append({"company": "", "role": role, "start_end": m.group(0) if m else "",
                                    "duration_months": dur_m, "desc": block[:600]})
                    buffer = []
                else:
                    buffer.append(BULLET.sub("", s))
    years = round(total_months / 12.0, 2)
    return entries, years


def extract_cgpa(text: str) -> float | None:
    m = re.search(r"(?:cgpa|gpa)\s*[:=]?\s*([0-9](?:\.[0-9])?)\s*(?:/10)?", text, re.I)
    if not m: return None
    try:
        val = float(m.group(1))
        if 0 <= val <= 10: return round(val, 2)
    except Exception:
        pass
    return None


def extract_hackathons(text: str) -> int:
    low = text.lower()
    wins = 0
    for m in re.findall(r"(won|winner|winners?)\s+(?:at\s+)?([a-z0-9 \-]+?)\s*(?:hackathon|hackathons)", low):
        wins += 1
    # also count explicit "x hackathons won"
    m2 = re.search(r"(\d+)\s*(?:\+)?\s*(?:hackathon|hackathons)\s*(?:won|wins)", low)
    if m2:
        try: wins = max(wins, int(m2.group(1)))
        except: pass
    return wins


def extracurricular_score(text: str) -> int:
    words = ["hackathon", "open source", "volunteer", "ngo", "community", "olympiad",
             "sports", "captain", "event organizer", "fest", "core team", "club"]
    low = text.lower()
    return sum(1 for w in words if w in low)


def por_score(text: str) -> int:
    words = ["president", "secretary", "lead", "team lead", "founder", "co-founder",
             "chair", "head", "captain", "coordinator", "core team"]
    low = text.lower()
    return sum(1 for w in words if w in low)


def leadership_score(text: str) -> int:
    words = ["leadership", "led a team", "managed", "mentored", "spearheaded", "ownership"]
    low = text.lower()
    return sum(1 for w in words if w in low)


def extract_certifications(text: str) -> List[str]:
    lines = _split_lines(text)
    out = []
    for i, ln in enumerate(lines):
        if SEC_CERT.search(ln):
            sec = _collect_section(lines, i)
            for s in sec:
                s = BULLET.sub("", s).strip()
                if s:
                    out.append(s[:160])
    return out


def extract_achievements(text: str) -> List[str]:
    lines = _split_lines(text)
    out = []
    for i, ln in enumerate(lines):
        if SEC_ACHV.search(ln):
            sec = _collect_section(lines, i)
            for s in sec:
                s = BULLET.sub("", s).strip()
                if s:
                    out.append(s[:200])
    return out


def extract_publications(text: str) -> List[str]:
    lines = _split_lines(text)
    out = []
    for i, ln in enumerate(lines):
        if SEC_PUBS.search(ln):
            sec = _collect_section(lines, i)
            for s in sec:
                s = BULLET.sub("", s).strip()
                if s:
                    out.append(s[:200])
    return out
