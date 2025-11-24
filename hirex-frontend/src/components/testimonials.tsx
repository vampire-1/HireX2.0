"use client";

import Avatar1 from "@/assets/avatar-1.png";
import Avatar2 from "@/assets/avatar-2.png";
import Avatar3 from "@/assets/avatar-3.png";
import Avatar4 from "@/assets/avatar-4.png";
import Image from "next/image";
import { motion } from "framer-motion";

const testimonials = [
  {
    text: "“Smart Candidate Search: Recruiters can query in plain English and instantly get precise, ranked results.”",
    avatarImg: Avatar1,
    name: "Aarav Sharma",
    position: "HR Manager",
  },
  {
    text: "“Advanced Resume Filtering: Powerful filters for skills, education, project, CGPA, hackathon wins, roles, and more to land the right candidates.”",
    avatarImg: Avatar2,
    name: "Priya Mehta",
    position: "Recruiter",
  },
  {
    text: "“Seamless Resume Management: Upload bulk resumes in .zip, automatically parse and analyze them, then download shortlisted resumes in one click.”",
    avatarImg: Avatar3,
    name: "Rohit Verma",
    position: "Talent Acquisition Lead",
  },
  {
    text: "“Bias-Free Evaluation: Ensure fair, consistent, and transparent candidate selection.”",
    avatarImg: Avatar4,
    name: "Sneha Patel",
    position: "Hiring Specialist",
  },
];

export function Testimonials() {
  return (
    <section className="py-20 md:py-24" id="about">
      <div className="container">
        <h2 className="text-5xl md:text-6xl font-medium text-center tracking-tighter">
          Beyond Expectations.
        </h2>
        <p className="text-white/70 text-lg md:text-xl max-w-2xl mx-auto text-center tracking-tight mt-5">
          Experience faster, more accurate hiring with our innovative AI Resume
          Analyzer.
        </p>

        <div className="flex overflow-hidden mt-10 [mask-image:linear-gradient(to_right,transparent,black_20%,black_80%,transparent)]">
          <motion.div
            initial={{ translateX: "-50%" }}
            animate={{ translateX: "0" }}
            transition={{
              repeat: Infinity,
              duration: 50,
              ease: "linear",
            }}
            className="flex flex-none gap-5"
          >
            {[...testimonials, ...testimonials].map((testimonial, index) => (
              <div
                key={index}
                className="border border-muted p-6 md:p-10 rounded-xl bg-[linear-gradient(to_bottom_left,rgb(140,69,255,0.3),black)] max-w-xs md:max-w-md flex-none"
              >
                <p className="text-lg md:text-2xl tracking-tight">
                  {testimonial.text}
                </p>

                <div className="flex items-center gap-3 mt-5">
                  <div className="relative after:content-[''] after:absolute after:inset-0 after:bg-[rgb(140,69,244)] after:mix-blend-soft-light after:rounded-lg before:content-[''] before:absolute before:inset-0 before:border before:border-white/30 before:z-10 before:rounded-lg">
                    <Image
                      src={testimonial.avatarImg}
                      alt={testimonial.name || "User avatar"}
                      className="size-11 rounded-lg grayscale"
                    />
                  </div>

                  <div>
                    <p className="font-medium">{testimonial.name}</p>
                    <p className="text-white/50 text-sm">
                      {testimonial.position}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

export default Testimonials;
