"use client";

import { useRef, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  motion,
  useMotionTemplate,
  useMotionValue,
  useScroll,
  useTransform,
} from "framer-motion";
import BackgroundStars from "@/assets/stars.png";
import BackgroundGrid from "@/assets/grid-lines.png";

/* =======================
   API HELPERS (same file)
   ======================= */

// Robust env fallback (avoids 'undefined' base)
const rawBase = process.env.NEXT_PUBLIC_API_BASE as string | undefined;
const BASE =
  rawBase && rawBase !== "undefined" && rawBase !== "null"
    ? rawBase
    : "http://127.0.0.1:8000";

// debug once on client
if (typeof window !== "undefined") {
  // eslint-disable-next-line no-console
  console.log("[HireX] AUTH API BASE =", BASE);
}

// Safe JSON reader so a non-JSON body doesn't crash with "failed to fetch"
async function safeJson(res: Response) {
  const text = await res.text();
  if (!text) return {}; // tolerate empty body
  try {
    return JSON.parse(text);
  } catch {
    throw new Error("Invalid JSON from server");
  }
}

async function registerEmailPassword(email: string, password: string) {
  const r = await fetch(`${BASE}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error(await r.text());
  const data = (await safeJson(r)) as { transaction_id?: string };
  if (!data?.transaction_id) throw new Error("Missing transaction_id in response");
  return data as { transaction_id: string };
}

async function loginStart(email: string, password: string) {
  const r = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error(await r.text());
  const data = (await safeJson(r)) as { transaction_id?: string };
  if (!data?.transaction_id) throw new Error("Missing transaction_id in response");
  return data as { transaction_id: string };
}

async function verifyOtp(transaction_id: string, code: string) {
  const r = await fetch(`${BASE}/auth/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ transaction_id, code }),
  });
  if (!r.ok) throw new Error(await r.text());
  return await safeJson(r);
}

async function resendOtp(transaction_id: string) {
  const r = await fetch(`${BASE}/auth/resend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ transaction_id }),
  });
  if (!r.ok) throw new Error(await r.text());
  return await safeJson(r);
}

/** Track mouse position relative to an element */
const useRelativeMousePosition = (to: React.RefObject<HTMLElement>) => {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!to.current) return;
      const rect = to.current.getBoundingClientRect();
      mouseX.set(e.clientX - rect.left);
      mouseY.set(e.clientY - rect.top);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [mouseX, mouseY, to]);
  return [mouseX, mouseY] as const;
};

/** Twinkling star particles on top of the drifting stars texture */
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

export default function AuthPage() {
  const router = useRouter(); // for redirect after OTP
  const sectionRef = useRef<HTMLElement>(null);
  const gridMaskRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"],
  });
  const backgroundPositionY = useTransform(scrollYProgress, [0, 1], [-300, 300]);

  const [mouseX, mouseY] = useRelativeMousePosition(gridMaskRef);
  const maskImage = useMotionTemplate`radial-gradient(50% 50% at ${mouseX}px ${mouseY}px, black, transparent)`;

  /* ===== Auth state & handlers ===== */
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [transactionId, setTransactionId] = useState<string | null>(null);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setInfo(null);
    setLoading(true);
    try {
      const start =
        mode === "signup"
          ? await registerEmailPassword(email, password)
          : await loginStart(email, password);
      setTransactionId(start.transaction_id);
      setInfo("We sent a 6-digit code to your email.");
    } catch (e: any) {
      setErr(e?.message ?? "Failed");
    } finally {
      setLoading(false);
    }
  }

  async function onVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!transactionId) return;
    setLoading(true);
    setErr(null);
    try {
      await verifyOtp(transactionId, otp);
      setInfo("You're in! Redirecting…");
      // redirect to your chat page; remove if you prefer to keep them here
      setTimeout(() => router.push("/chatbase"), 800);
    } catch (e: any) {
      setErr(e?.message ?? "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      {/* Subtle twinkling particles */}
      <Starfield count={120} />

      {/* Drifting star texture header (like ChatPage) */}
      <motion.section
        ref={sectionRef}
        animate={{ backgroundPositionX: BackgroundStars.width }}
        transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
        className="relative h-[220px] md:h-[280px] overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,black_6%,black_94%,transparent)]"
        style={{
          backgroundImage: `url(${BackgroundStars.src})`,
          backgroundPositionY,
        }}
      >
        {/* Grid with radial reveal-on-hover */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[rgb(14,0,36)]/40" />
          <div
            className="absolute inset-0 bg-[rgb(74,32,138)]/60 bg-blend-overlay [mask-image:radial-gradient(50%_50%_at_50%_35%,black,transparent)]"
            style={{ backgroundImage: `url(${BackgroundGrid.src})` }}
          />
          <motion.div
            ref={gridMaskRef}
            className="absolute inset-0 bg-[rgb(74,32,138)]/60 bg-blend-overlay opacity-0"
            style={{ backgroundImage: `url(${BackgroundGrid.src})`, maskImage }}
            whileHover={{ opacity: 1 }}
          />
        </div>

        <div className="relative h-full flex flex-col justify-center items-center text-center gap-2">
          <h1 className="text-5xl md:text-7xl font-bold text-white tracking-tight">
            HireX
          </h1>
          <p className="text-white/70 text-sm md:text-lg max-w-xl">
            {mode === "signup"
              ? "Sign up and surf the stars to your next hire."
              : "Welcome back. Continue with your credentials."}
          </p>
        </div>
      </motion.section>

      {/* Auth card */}
      <main className="container px-4 md:px-6 pb-28">
        <div className="mx-auto max-w-md -mt-16 relative z-10">
          <motion.div
            className="border border-white/10 bg-white/5 rounded-2xl p-6 md:p-8 text-white backdrop-blur-sm shadow-xl"
            style={{
              backgroundImage: `url(${BackgroundStars.src})`,
              backgroundPositionY,
            }}
          >
            <div className="flex items-center justify-center gap-3 text-xs text-white/70 -mt-1 mb-4">
              <button
                type="button"
                onClick={() => {
                  setMode("signup");
                  setTransactionId(null);
                  setErr(null);
                  setInfo(null);
                }}
                className={mode === "signup" ? "underline" : ""}
              >
                Sign up
              </button>
              <span>•</span>
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setTransactionId(null);
                  setErr(null);
                  setInfo(null);
                }}
                className={mode === "login" ? "underline" : ""}
              >
                Log in
              </button>
            </div>

            <h2 className="text-2xl font-semibold text-center">
              {mode === "signup" ? "Create your account" : "Welcome back"}
            </h2>
            <p className="text-center mb-6 mt-1 text-white/70 text-sm">
              {transactionId
                ? "Enter the 6-digit code we emailed you"
                : mode === "signup"
                ? "Use your work email and a password"
                : "Enter your credentials to continue"}
            </p>

            {!transactionId ? (
              <form onSubmit={onSubmit} className="space-y-3">
                <label className="block text-xs text-white/70 mb-1">Email</label>
                <input
                  type="email"
                  placeholder="you@company.com"
                  className="px-4 py-3 rounded-lg bg-black/40 border border-white/20 text-white w-full placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-400/60"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />

                <label className="block text-xs text-white/70 mb-1">Password</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  className="px-4 py-3 rounded-lg bg-black/40 border border-white/20 text-white w-full placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-purple-400/60"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />

                <button
                  disabled={loading}
                  className="w-full bg-white text-[#0E0024] py-3 rounded-lg font-medium hover:bg-white/90 transition disabled:opacity-60"
                >
                  {loading
                    ? "Please wait…"
                    : mode === "signup"
                    ? "Create account"
                    : "Continue"}
                </button>

                {err && <div className="text-red-300 text-xs mt-2">{err}</div>}
                {info && <div className="text-green-300 text-xs mt-2">{info}</div>}

                <div className="flex items-center my-4">
                  <div className="flex-grow h-px bg-white/20" />
                  <span className="px-3 text-sm text-gray-300">HireX</span>
                  <div className="flex-grow h-px bg-white/20" />
                </div>

                <p className="text-center text-xs text-white/60">
                  By continuing you agree to our Terms & Privacy Policy.
                </p>
              </form>
            ) : (
              <form onSubmit={onVerify} className="space-y-3">
                <label className="block text-xs text-white/70">Enter 6-digit code</label>
                <input
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  inputMode="numeric"
                  maxLength={6}
                  className="px-4 py-3 rounded-lg bg-black/40 border border-white/20 text-white w-full"
                  placeholder="------"
                />

                <button
                  disabled={loading}
                  className="w-full bg-white text-[#0E0024] py-3 rounded-lg font-medium hover:bg-white/90 transition disabled:opacity-60"
                >
                  {loading ? "Verifying…" : "Verify & Sign in"}
                </button>

                <button
                  type="button"
                  onClick={() => transactionId && resendOtp(transactionId)}
                  className="text-xs underline text-white/70"
                >
                  Resend code
                </button>

                {err && <div className="text-red-300 text-xs mt-2">{err}</div>}
                {info && <div className="text-green-300 text-xs mt-2">{info}</div>}
              </form>
            )}
          </motion.div>
        </div>
      </main>

      {/* Global night gradient (behind everything) */}
      <div className="fixed inset-0 -z-20 bg-gradient-to-b from-[#0E0024] via-[#0E0024] to-[#0B001C]" />

      {/* Slow panning star texture across the entire viewport */}
      <motion.div
        aria-hidden
        animate={{ backgroundPositionX: BackgroundStars.width }}
        transition={{ duration: 160, repeat: Infinity, ease: "linear" }}
        className="fixed inset-0 -z-30 opacity-[0.07]"
        style={{ backgroundImage: `url(${BackgroundStars.src})` }}
      />
    </>
  );
}
