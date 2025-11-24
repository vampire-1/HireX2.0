import json
import logging
import zipfile
from pathlib import Path
from typing import List, Optional

# app/main.py
from dotenv import load_dotenv
load_dotenv()  # loads .env from project root


from .config import settings
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from .config import settings
from .db import init_db, engine, Candidate
from .utils.files import save_upload
from .services import parser
from .services.skills import (
    extract_skills as sk_extract,
    extract_soft_skills as sk_soft,
    to_json as to_json_list,
)
from .services.educations import (
    extract_institutions as edu_extract,
    extract_degrees,
    extract_majors,
    to_json as to_json_edu,
)
from .services.embeddings import Embedder
from .services.indexer import FaissIndex
from .services.prompt_parser import parse_prompt
from .services.search import apply_filters, best_snippet
from .services.ranking_profiles import PROFILES, DEFAULT_PROFILE
from .services.ranking import compute_score
from .services.roles import extract_roles_from_resume

# ⬇️ NEW: auth tables + router
from .models_auth import User, AuthTxn  # ensure tables are registered for create_all
from .routes.auth import router as auth_router

from .schemas import (
    UploadResponse,
    RecruiterQueryRequest,
    CandidateOut,
    RecruiterSearchResponse,
    StructuredFilters,
)

# -----------------------------------------------------------------------------
# App / Init
# -----------------------------------------------------------------------------
app = FastAPI(title="HireX Backend", version="0.8.0")

origins = [o.strip() for o in settings.FRONTEND_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # e.g. http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routers
app.include_router(auth_router)  # ⬅️ exposes /auth/register, /auth/login, /auth/verify, /auth/resend

# Logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("hirex.mail").setLevel(logging.INFO)
logger = logging.getLogger("hirex")
logger.setLevel(logging.INFO)

init_db()
_embedder = Embedder(settings.EMBEDDING_MODEL)
_DIM = _embedder.encode(["test"]).shape[1]
_index = FaissIndex.load(_DIM)

ALLOWED_EXTS = {
    ".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff",
}


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _build_candidate_record(text: str, path: str) -> dict:
    meta = parser.rough_parse(text or Path(path).name)
    skills = sk_extract(text or "")
    soft_sk = sk_soft(text or "")
    insts = edu_extract(text or "")
    degrees = extract_degrees(text or "")
    majors = extract_majors(text or "")

    projects = parser.extract_projects(text or "")
    exp_entries, computed_years = parser.extract_experience(text or "")
    cgpa = parser.extract_cgpa(text or "")
    hackwins = parser.extract_hackathons(text or "")
    extra = parser.extracurricular_score(text or "")
    por = parser.por_score(text or "")
    lead = parser.leadership_score(text or "")
    certs = parser.extract_certifications(text or "")
    achv = parser.extract_achievements(text or "")
    pubs = parser.extract_publications(text or "")

    years = meta.get("years_experience") or computed_years or 0.0

    # derive roles (from titles + skills)
    roles = extract_roles_from_resume(text or "", skills)

    rec = dict(
        name=meta.get("name") or Path(path).stem,
        email=meta.get("email"),
        phone=meta.get("phone"),
        location=None,
        linkedin=meta.get("linkedin"),
        github=meta.get("github"),
        portfolio=meta.get("portfolio"),
        years_experience=years,
        cgpa=cgpa,
        project_count=len(projects),
        hackathon_wins=hackwins,
        extracurricular_score=extra,
        leadership_score=lead,
        por_score=por,
        notice_period_months=None,
        skills=to_json_list(skills),
        soft_skills=to_json_list(soft_sk),
        institutions=to_json_edu(insts),
        degrees=to_json_edu(degrees),
        majors=to_json_edu(majors),
        languages="[]",
        certifications=json.dumps(certs, ensure_ascii=False),
        achievements=json.dumps(achv, ensure_ascii=False),
        publications=json.dumps(pubs, ensure_ascii=False),
        education_entries=json.dumps([], ensure_ascii=False),  # simple for MVP
        experience_entries=json.dumps(exp_entries, ensure_ascii=False),
        projects=json.dumps(projects, ensure_ascii=False),
        keywords="[]",
        education_text=None,
        resume_path=path,
        parsed_text=text or "",
        roles=json.dumps(roles, ensure_ascii=False),  # store roles
    )
    return rec


# -----------------------------------------------------------------------------
# Upload endpoints
# -----------------------------------------------------------------------------
@app.post("/resumes/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    path = save_upload(file)
    text = parser.read_file_text(path)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from resume")

    rec = _build_candidate_record(text, path)
    with Session(engine) as session:
        cand = Candidate(**rec)
        session.add(cand)
        session.commit()
        session.refresh(cand)

    vec = _embedder.encode([rec["parsed_text"]])
    _index.add(vec, [{"id": cand.id, "name": cand.name}])
    _index.save()

    return UploadResponse(
        id=cand.id,
        name=cand.name,
        email=cand.email,
        skills=json.loads(rec["skills"]),
        institutions=json.loads(rec["institutions"]),
    )


@app.post("/recruiters/resumes/upload-zip")
async def upload_zip(zipfile_upload: UploadFile = File(...)):
    tmp_zip = Path(settings.DATA_DIR) / ("tmp_" + zipfile_upload.filename)
    tmp_zip.parent.mkdir(parents=True, exist_ok=True)
    with tmp_zip.open("wb") as f:
        f.write(await zipfile_upload.read())

    accepted_records, accepted_texts, accepted_names = [], [], []
    failed = 0
    extract_dir = Path(settings.RESUME_DIR) / ("batch_" + Path(zipfile_upload.filename).stem)
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                suffix = Path(member.filename).suffix.lower()
                if suffix not in ALLOWED_EXTS:
                    continue
                target_path = extract_dir / Path(member.filename).name
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, target_path.open("wb") as dst:
                    dst.write(src.read())
                try:
                    text = parser.read_file_text(str(target_path))
                    rec = _build_candidate_record(text, str(target_path))
                    accepted_records.append(rec)
                    if text and text.strip():
                        accepted_texts.append(text)
                        accepted_names.append(rec["name"])
                except Exception:
                    failed += 1
    finally:
        try:
            tmp_zip.unlink()
        except Exception:
            pass

    ids: List[int] = []
    with Session(engine) as session:
        for rec in accepted_records:
            cand = Candidate(**rec)
            session.add(cand)
        session.commit()
        for rec in accepted_records:
            obj = session.exec(
                select(Candidate).where(Candidate.resume_path == rec["resume_path"])
            ).first()
            if obj:
                ids.append(obj.id)

    if accepted_texts:
        vecs = _embedder.encode(accepted_texts)
        metas = [{"id": ids[i], "name": accepted_names[i]} for i in range(len(accepted_texts))]
        _index.add(vecs, metas)
        _index.save()

    return {
        "accepted": len(accepted_records),
        "failed": failed,
        "total_in_zip": len(accepted_records) + failed,
        "inserted_ids": ids,
        "embedded_count": len(accepted_texts),
        "message": "ZIP upload processed",
    }


@app.get("/resumes/{cand_id}/download")
async def download_resume(cand_id: int):
    with Session(engine) as session:
        cand = session.get(Candidate, cand_id)
        if not cand:
            raise HTTPException(status_code=404, detail="Not found")
        p = Path(cand.resume_path)
        if not p.exists():
            raise HTTPException(status_code=404, detail="File missing")
        return FileResponse(str(p), filename=p.name)


# -----------------------------------------------------------------------------
# Recruiter query (POST) + optional GET wrapper
# -----------------------------------------------------------------------------
@app.post("/recruiters/query", response_model=RecruiterSearchResponse)
async def recruiter_query(req: RecruiterQueryRequest):
    """
    Chat-style endpoint. Example body:
    {
      "prompt": "mern developers from iit with minimum 4 years experience",
      "top_k": 10,
      "profile": "balanced",
      "candidate_ids": [optional subset restriction]
    }
    """

    # 1) Parse prompt -> structured filters
    fdict = parse_prompt(req.prompt)
    filters = StructuredFilters(**fdict)
    logger.info("Parsed filters: %s", filters.model_dump())

    # 2) Semantic retrieval first
    q_vec = _embedder.encode([req.prompt])
    D, metas = _index.search(q_vec, top_k=max(req.top_k, 200))
    id2sem = {}
    ids: List[int] = []
    if metas and len(metas) > 0 and len(metas[0]) > 0:
        for score, m in zip(D[0].tolist(), metas[0]):
            id2sem[m["id"]] = float(score)
        ids = [m["id"] for m in metas[0]]

    # 3) Load candidates; if FAISS empty, fallback to scanning all
    with Session(engine) as session:
        if ids:
            rows = session.exec(select(Candidate).where(Candidate.id.in_(ids))).all()
        else:
            rows = session.exec(select(Candidate)).all()

    # 4) Optional subset restriction (rank only from these resumes)
    if req.candidate_ids:
        allow = set(req.candidate_ids)
        rows = [r for r in rows if r.id in allow]

    # 5) Apply structured filters on the pool (incl. roles_any_of)
    rows = apply_filters(
        rows,
        min_experience=filters.min_experience,
        must_have=filters.must_have_skills,
        education_any_of=filters.education_any_of,
        location=filters.location,
        min_projects=filters.min_projects,
        min_cgpa=filters.min_cgpa,
        min_hackathon_wins=filters.min_hackathon_wins,
        contains_phrase=filters.contains_phrase,
        require_extracurricular=filters.require_extracurricular,
        require_por=filters.require_por,
        roles_any_of=getattr(filters, "roles_any_of", []),  # pass roles
    )

    # 6) If no semantic scores (FAISS empty), create a tiny proxy from skill overlap
    if not id2sem:
        q_skills = set(sk_extract(req.prompt))
        for r in rows:
            r_skills = set(json.loads(r.skills or "[]"))
            id2sem[r.id] = (
                len(q_skills & r_skills) / max(1, len(q_skills)) if q_skills else 0.0
            )

    # 7) Choose scoring profile (weights)
    weights = PROFILES.get((req.profile or DEFAULT_PROFILE), PROFILES[DEFAULT_PROFILE])

    # 8) Score & build response items (with small role bonus)
    items: List[CandidateOut] = []
    q_skills = set(sk_extract(req.prompt))
    req_roles = set(getattr(filters, "roles_any_of", []) or [])

    for r in rows:
        r_skills = set(json.loads(r.skills or "[]"))
        r_insts = list(json.loads(r.institutions or "[]"))
        r_roles = set(json.loads(getattr(r, "roles", "[]") or "[]"))
        sem = id2sem.get(r.id, 0.0)

        score, parts = compute_score(
            {
                "years_experience": r.years_experience,
                "cgpa": r.cgpa,
                "institutions": r_insts,
                "extracurricular_score": r.extracurricular_score,
            },
            weights,
            sem,
        )

        # small score bonus if role matches prompt roles
        role_match = 1.0 if (req_roles and (r_roles & req_roles)) else 0.0
        if role_match:
            score = score + 0.05  # 5% bump
        parts["role_bonus"] = role_match

        reasons = [
            f"score_parts={parts}",
            f"skills_match={', '.join(sorted(list(q_skills & r_skills))) or '—'}",
        ]
        if req_roles:
            reasons.append(f"Role match: {', '.join(sorted(list(r_roles & req_roles))) or '—'}")
        if filters.min_cgpa is not None:
            reasons.append(f"CGPA needed ≥{filters.min_cgpa}, found {r.cgpa or 'N/A'}")
        if filters.min_projects:
            reasons.append(f"Projects needed ≥{filters.min_projects}, found {r.project_count}")
        if filters.min_hackathon_wins:
            reasons.append(
                f"Hackathon wins needed ≥{filters.min_hackathon_wins}, found {r.hackathon_wins}"
            )

        items.append(
            CandidateOut(
                id=r.id,
                name=r.name,
                email=r.email,
                years_experience=r.years_experience,
                skills=sorted(list(r_skills)),
                institutions=r_insts,
                score=round(float(score), 4),
                reasons=reasons,
                resume_path=f"/resumes/{r.id}/download",
                snippet=best_snippet(r.parsed_text, filters.contains_phrase or req.prompt),
            )
        )

    # 9) Sort & truncate
    items.sort(key=lambda x: x.score, reverse=True)
    items = items[: req.top_k]

    return RecruiterSearchResponse(
        query=req.prompt, filters=filters, total_returned=len(items), items=items
    )


# Optional: GET wrapper for quick manual testing from the browser bar
@app.get("/recruiters/query")
async def recruiter_query_get(prompt: str, top_k: int = 50, profile: Optional[str] = None):
    """
    Convenience GET so you can test in the browser:
    /recruiters/query?prompt=mern%20developers%20from%20iit%20with%204%20years&top_k=10
    """
    body = RecruiterQueryRequest(prompt=prompt, top_k=top_k, profile=profile)
    return await recruiter_query(body)
