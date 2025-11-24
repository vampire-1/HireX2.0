// components/hirex.ts
const rawBase = process.env.NEXT_PUBLIC_API_BASE;

// guard against undefined, "undefined", "", "null"
export const API_BASE =
  rawBase && rawBase !== "undefined" && rawBase !== "null"
    ? rawBase
    : "http://127.0.0.1:8000";

// Optional: log the resolved base on the client once
if (typeof window !== "undefined") {
  // eslint-disable-next-line no-console
  console.log("[HireX] API_BASE =", API_BASE);
}

export type RecruiterQueryBody = {
  prompt: string;
  top_k?: number;
  profile?: string | null;
  candidate_ids?: number[];
};

export async function recruiterQuery(body: RecruiterQueryBody) {
  const res = await fetch(`${API_BASE}/recruiters/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // credentials: "include", // only if your backend sets cookies and CORS allows credentials
    body: JSON.stringify({ top_k: 50, profile: "balanced", ...body }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function uploadZip(file: File) {
  const form = new FormData();
  form.append("zipfile_upload", file); // must match FastAPI param name

  const res = await fetch(`${API_BASE}/recruiters/resumes/upload-zip`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export function resumeDownloadUrl(id: number) {
  return `${API_BASE}/resumes/${id}/download`;
}
