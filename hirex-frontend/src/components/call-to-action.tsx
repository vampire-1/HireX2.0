"use client";

import BackgroundStars from "@/assets/stars.png";
import BackgroundGrid from "@/assets/grid-lines.png";
import {
  motion,
  useMotionTemplate,
  useMotionValue,
  useScroll,
  useTransform,
  type MotionValue,
} from "framer-motion";
import { RefObject, useCallback, useEffect, useRef, useState } from "react";

/**
 * Custom Hook for Relative Mouse Position (returns motion values)
 * - updateMousePosition is wrapped in useCallback so it is stable and can be safely included
 *   in the useEffect deps array (fixes react-hooks/exhaustive-deps).
 */
const useRelativeMousePosition = (
  to: RefObject<HTMLElement>
): [MotionValue<number>, MotionValue<number>] => {
  const mouseX = useMotionValue<number>(0);
  const mouseY = useMotionValue<number>(0);

  // Stable callback so useEffect doesn't complain about missing deps
  const updateMousePosition = useCallback(
    (event: MouseEvent) => {
      if (!to.current) return;
      const { top, left } = to.current.getBoundingClientRect();
      // use clientX/Y for better cross-browser support than event.x / event.y
      mouseX.set(event.clientX - left);
      mouseY.set(event.clientY - top);
    },
    [to, mouseX, mouseY]
  );

  useEffect(() => {
    window.addEventListener("mousemove", updateMousePosition);
    return () => window.removeEventListener("mousemove", updateMousePosition);
  }, [updateMousePosition]);

  return [mouseX, mouseY];
};

export function CallToAction() {
  const sectionRef = useRef<HTMLElement>(null);
  const borderedDivRef = useRef<HTMLDivElement>(null);
  const [isChatbaseLoaded, setIsChatbaseLoaded] = useState(false);

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: [`start end`, "end start"],
  });
  const backgroundPositionY = useTransform(scrollYProgress, [0, 1], [-300, 300]);

  const [mouseX, mouseY] = useRelativeMousePosition(borderedDivRef);
  const maskImage = useMotionTemplate`radial-gradient(50% 50% at ${mouseX}px ${mouseY}px, black, transparent)`;

  return (
    <section className={"py-20 md:py-24"} ref={sectionRef} id="content">
      <div className={"container"}>
        <motion.div
          animate={{ backgroundPositionX: BackgroundStars.width }}
          transition={{ duration: 120, repeat: Infinity, ease: "linear" }}
          className={"border border-muted py-24 px-6 rounded-xl overflow-hidden relative group"}
          style={{ backgroundImage: `url(${BackgroundStars.src})`, backgroundPositionY }}
        >
          <div
            className={
              "absolute inset-0 bg-[rgb(74,32,138)] bg-blend-overlay [mask-image:radial-gradient(50%_50%_at_50%_35%,black,transparent)] group-hover:opacity-0 transition duration-700"
            }
            style={{ backgroundImage: `url(${BackgroundGrid.src})` }}
          />
          <motion.div
            className={
              "absolute inset-0 bg-[rgb(74,32,138)] bg-blend-overlay opacity-0 group-hover:opacity-100 transition duration-700"
            }
            style={{ backgroundImage: `url(${BackgroundGrid.src})`, maskImage }}
            ref={borderedDivRef}
          />
          <div className={"relative"}>
            <h2 className={"text-5xl tracking-tighter text-center font-medium"}>
              HireX, Smart Resume Screener for everyone
            </h2>
            <p className={"text-center text-lg md:text-xl text-white/70 tracking-tight px-4 mt-5"}>
              Achieve clear, impactful results without the complexity.
            </p>
            {/* Removed ActionButton component */}
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default CallToAction;
