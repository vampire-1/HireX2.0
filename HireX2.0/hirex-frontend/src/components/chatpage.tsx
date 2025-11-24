"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useMotionTemplate,
  useMotionValue,
} from "framer-motion";
import BackgroundStars from "@/assets/stars.png";
import BackgroundGrid from "@/assets/grid-lines.png";



import {
  recruiterQuery,
  uploadZip,
  resumeDownloadUrl,
} from "@/components/hirex";

type Candidate = {
  id: number;
  name: string;
  email?: string | null;
  years_experience?: number | null;
  skills: string[];
  institutions: string[];
  score: number;
  reasons: string[];
  resume_path: string;
  snippet?: string | null;
};

type SearchResponse = {
  query: string;
  total_returned: number;
  items: Candidate[];
  filters: any;
};

const useRelativeMousePosition = (to: React.RefObject<HTMLElement>) => {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  useEffect(() => {
    const updateMousePosition = (event: MouseEvent) => {
      if (!to.current) return;
      const { top, left } = to.current.getBoundingClientRect();
      mouseX.set(event.clientX - left);
      mouseY.set(event.clientY - top);
    };
    window.addEventListener("mousemove", updateMousePosition);
    return () => window.removeEventListener("mousemove", updateMousePosition);
  }, [mouseX, mouseY, to]);
  return [mouseX, mouseY] as const;
};

function Starfield({ count = 120 }: { count?: number }) {
  const stars = useMemo(
    () =>
      Array.from({ length: count }).map((_, i) => ({
        id: i,
        top: Math.random() * 100,
        left: Math.random() * 100,
        size: Math.random() * 2 + 1,
        delay: Math.random() * 6,
        drift: (Math.random() * 2 - 1) * 20,
      })),
    [count]
  );
  return (
    <div className="pointer-events-none fixed inset-0 -z-10">
      {stars.map((s) => (
        <motion.span
          key={s.id}
          initial={{ opacity: 0.4, y: 0 }}
          animate={{ opacity: [0.4, 1, 0.6, 1], y: [0, s.drift, 0] }}
          transition={{
            duration: 8 + s.delay,
            repeat: Infinity,
            ease: "easeInOut",
            delay: s.delay,
          }}
          style={{
            top: `${s.top}%`,
            left: `${s.left}%`,
            width: s.size,
            height: s.size,
          }}
          className="absolute rounded-full bg-white/90 shadow-[0_0_6px_rgba(255,255,255,0.7)]"
        />
      ))}
    </div>
  );
}

export default function ChatPage() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resp, setResp] = useState<SearchResponse | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sectionRef = useRef<HTMLElement>(null);
  const gridMaskRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"],
  });
  const backgroundPositionY = useTransform(scrollYProgress, [0, 1], [-300, 300]);

  const headerTiltX = useMotionValue(0);
  const headerTiltY = useMotionValue(0);
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      const { innerWidth: w, innerHeight: h } = window;
      const dx = (e.clientX / w - 0.5) * 10;
      const dy = (e.clientY / h - 0.5) * -10;
      headerTiltX.set(dy);
      headerTiltY.set(dx);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [headerTiltX, headerTiltY]);

  const [mouseX, mouseY] = useRelativeMousePosition(gridMaskRef);
  const maskImage = useMotionTemplate`radial-gradient(50% 50% at ${mouseX}px ${mouseY}px, black, transparent)`;

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setToast(null);
    setResp(null);
    try {
      const data = await recruiterQuery({
        prompt,
        top_k: 50,
        profile: "balanced",
      });
      setResp(data);
      if (!data?.items?.length) {
        setToast("No matching candidates. Try broader criteria or fewer constraints.");
      }
    } catch (err: any) {
      setError(err?.message ?? "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function onZipSelected(file: File | null) {
    if (!file) return;
    setUploading(true);
    setToast(null);
    setError(null);
    try {
      const res = await uploadZip(file);
      setToast(
        `Uploaded: ${res.accepted ?? 0} • Embedded: ${res.embedded_count ?? 0} • Failed: ${res.failed ?? 0}`
      );
    } catch (err: any) {
      setError(err?.message ?? "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <Starfield count={120} />

      <motion.section
        ref={sectionRef}
        animate={{ backgroundPositionX: BackgroundStars.width }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
        className="relative h-[220px] md:h-[280px] overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_6%,black_94%,transparent)]"
        style={{
          backgroundImage: `url(${BackgroundStars.src})`,
          backgroundPositionY,
          perspective: 1000,
        }}
      >
        <motion.div
          style={{
            rotateX: headerTiltX,
            rotateY: headerTiltY,
            transformStyle: "preserve-3d",
          }}
          className="absolute inset-0"
        >
          <div className="absolute inset-0 bg-[rgb(14,0,36)]/40" />
          <div
            className="absolute inset-0 bg-[rgb(74,32,138)]/60 bg-blend-overlay [mask-image:radial-gradient(50%_50%_at_50%_35%,black,transparent)]"
            style={{ backgroundImage: `url(${BackgroundGrid.src})` }}
          />
          <motion.div
            className="absolute inset-0 bg-[rgb(74,32,138)]/60 bg-blend-overlay opacity-0"
            style={{ backgroundImage: `url(${BackgroundGrid.src})`, maskImage }}
            whileHover={{ opacity: 1 }}
            ref={gridMaskRef}
          />
        </motion.div>

        <div className="relative h-full flex flex-col justify-center items-center text-center gap-2">
          <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight">
            HireX
          </h1>
          <p className="text-white/70 text-sm md:text-lg max-w-xl">
            Surf the stars to your next hire. Intelligent resume screening made effortless.
          </p>
        </div>
      </motion.section>

      <main className="container px-4 md:px-6 pb-28">
        <div className="mx-auto max-w-3xl">
          {toast && (
            <div className="mb-4 rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/80">
              {toast}
            </div>
          )}
          {error && (
            <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          )}

          {resp ? (
            <section className="space-y-4">
              <div className="text-[13px] text-white/60">
                <b className="text-white/80">{resp.total_returned ?? 0}</b> matches for{" "}
                <i>{resp.query}</i>
              </div>

              {!resp.items?.length ? (
                <div className="rounded-xl border border-white/10 bg-white/5 p-6 text-center text-white/80">
                  <div className="text-base font-medium">No matching candidates</div>
                  <div className="text-xs text-white/60 mt-1">
                    Try broader filters or fewer constraints.
                  </div>
                </div>
              ) : (
                <ul className="space-y-3">
                  {resp.items.map((c) => {
                    const skills = Array.isArray(c.skills) ? c.skills : [];
                    const institutions = Array.isArray(c.institutions) ? c.institutions : [];
                    const years =
                      typeof c.years_experience === "number" ? c.years_experience : 0;
                    const score = typeof c.score === "number" ? c.score : 0;

                    return (
                      <li
                        key={c.id}
                        className="border border-white/10 rounded-xl p-4 bg-white/5"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="font-medium text-white">{c.name}</div>
                            <div className="text-xs text-white/60 mt-0.5">
                              {c.email || "—"} • {years} yrs
                            </div>
                            <div className="text-xs mt-2 text-white/80">
                              <span className="text-white/90">Skills:</span>{" "}
                              {skills.slice(0, 12).join(", ") || "—"}
                            </div>
                            <div className="text-xs text-white/80">
                              <span className="text-white/90">Institutions:</span>{" "}
                              {institutions.join(", ") || "—"}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-[10px] uppercase tracking-wider text-white/50">
                              Score
                            </div>
                            <div className="text-xl font-semibold text-white">
                              {Number(score).toFixed(3)}
                            </div>
                          </div>
                        </div>

                        {c.snippet ? (
                          <div className="text-xs mt-3 text-white/80 line-clamp-3">
                            {c.snippet}
                          </div>
                        ) : null}

                        <div className="mt-3 flex flex-wrap items-center gap-3">
                          <a
                            className="text-xs underline underline-offset-2 text-white/80 hover:text-white"
                            href={resumeDownloadUrl(c.id)}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download resume
                          </a>
                          {Array.isArray(c.reasons) && c.reasons.length > 0 ? (
                            <div className="text-[11px] text-white/60">
                              {c.reasons.slice(0, 2).join(" · ")}
                            </div>
                          ) : null}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}

              {/* DEV DEBUG (remove later) */}
              {/* <pre className="mt-4 text-[10px] text-white/40 whitespace-pre-wrap break-all">
                {JSON.stringify({ total: resp.total_returned, first: resp.items?.[0] }, null, 2)}
              </pre> */}
            </section>
          ) : null}
        </div>
      </main>

      <form
        onSubmit={onAsk}
        className="fixed bottom-0 left-0 right-0 border-t border-white/10 bg-gradient-to-b from-transparent to-[#0B001C]/80 backdrop-blur-md"
      >
        <div className="container mx-auto px-4 md:px-6">
          <div className="mx-auto max-w-3xl py-4">
            <div className="relative flex items-center gap-2">
              <button
                type="button"
                aria-label="Attach"
                className="h-12 w-12 flex items-center justify-center rounded-lg border border-white/10 bg-white/5 text-white/80 hover:bg-white/10"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                title={uploading ? "Uploading…" : "Attach"}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="size-5"
                >
                  <path d="M12 5a1 1 0 0 1 1 1v5h5a1 1 0 1 1 0 2h-5v5a1 1 0 1 1-2 0v-5H6a1 1 0 1 1 0-2h5V6a1 1 0 0 1 1-1Z" />
                </svg>
              </button>
              <input
                className="flex-1 h-12 px-4 rounded-xl border border-white/10 bg-white/5 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-400/60"
                placeholder="Ask anything about your candidate pool…"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
              <button
                className="h-12 px-6 rounded-lg bg-white text-[#0E0024] font-medium hover:bg-white/90 transition disabled:opacity-60 disabled:cursor-not-allowed"
                disabled={loading || !prompt.trim()}
                type="submit"
              >
                {loading ? "Searching…" : "Send"}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                className="hidden"
                onChange={(e) => onZipSelected(e.target.files?.[0] ?? null)}
              />
            </div>
            <div className="mt-2 text-[10px] text-white/40 text-center">
              HireX may show downloadable resumes when available.
            </div>
          </div>
        </div>
      </form>

      <div className="fixed inset-0 -z-20 bg-gradient-to-b from-[#0E0024] via-[#0E0024] to-[#0B001C]" />
    </>
  );
}
