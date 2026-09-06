"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { Play, Smartphone, Watch } from "lucide-react";

const phoneScreens = [
  {
    src: "/prototype/phone-intro.png",
    title: "Phone launch screen",
    caption: "Entry point for the controlled Aura Watch demonstration.",
  },
  {
    src: "/prototype/phone-dashboard.png",
    title: "Monitoring dashboard",
    caption: "Controlled sensor values, risk state and signal preview.",
  },
  {
    src: "/prototype/phone-test-alert.png",
    title: "Test-alert state",
    caption: "Safe demonstration of the warning and cancellation workflow.",
  },
];

const watchScreens = [
  {
    src: "/prototype/watch-monitoring.png",
    title: "Watch monitoring",
    caption: "On-wrist monitoring state using simulated input.",
  },
  {
    src: "/prototype/watch-countdown.png",
    title: "Watch countdown",
    caption: "The 15-second user-confirmation window.",
  },
];

export function PrototypeGallery() {
  return (
    <div className="space-y-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        className="grid items-center gap-8 lg:grid-cols-[1.5fr_0.5fr]"
      >
        <div className="overflow-hidden rounded-md border border-slate-700 bg-slate-950 shadow-2xl shadow-neon-cyan/5">
          <video
            className="aspect-video w-full bg-slate-950 object-contain"
            controls
            muted
            loop
            playsInline
            preload="metadata"
            poster="/prototype/phone-dashboard.png"
          >
            <source src="/prototype/aura-watch-demo.mp4" type="video/mp4" />
            Your browser does not support embedded video.
          </video>
        </div>
        <div>
          <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-md border border-neon-cyan/30 bg-neon-cyan/10 text-neon-cyan">
            <Play size={18} fill="currentColor" />
          </div>
          <h3 className="text-2xl font-semibold text-white">Prototype walkthrough</h3>
          <p className="mt-3 text-sm leading-relaxed text-slate-400">
            A short sequence recorded from the project emulator captures: phone launch, monitoring dashboard, watch state, test alert and user-confirmation countdown.
          </p>
          <p className="mt-4 border-l-2 border-neon-amber pl-3 text-xs leading-relaxed text-slate-500">
            These screens demonstrate application behavior with controlled inputs. They do not show clinical seizure prediction.
          </p>
        </div>
      </motion.div>

      <div>
        <div className="mb-5 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-neon-cyan">
          <Smartphone size={16} /> Android application
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {phoneScreens.map((screen, index) => (
            <motion.figure
              key={screen.src}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.08 }}
              className="overflow-hidden rounded-md border border-slate-800 bg-slate-950/70"
            >
              <div className="relative mx-auto aspect-[9/16] max-h-[620px] bg-black">
                <Image src={screen.src} alt={screen.title} fill sizes="(max-width: 768px) 90vw, 30vw" className="object-contain" />
              </div>
              <figcaption className="border-t border-slate-800 p-4">
                <div className="font-medium text-white">{screen.title}</div>
                <div className="mt-1 text-xs leading-relaxed text-slate-500">{screen.caption}</div>
              </figcaption>
            </motion.figure>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-5 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-neon-cyan">
          <Watch size={16} /> Wear OS application
        </div>
        <div className="grid max-w-3xl gap-6 sm:grid-cols-2">
          {watchScreens.map((screen, index) => (
            <motion.figure
              key={screen.src}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.08 }}
              className="overflow-hidden rounded-md border border-slate-800 bg-slate-950/70"
            >
              <div className="relative aspect-square bg-black">
                <Image src={screen.src} alt={screen.title} fill sizes="(max-width: 768px) 90vw, 360px" className="object-contain" />
              </div>
              <figcaption className="border-t border-slate-800 p-4">
                <div className="font-medium text-white">{screen.title}</div>
                <div className="mt-1 text-xs leading-relaxed text-slate-500">{screen.caption}</div>
              </figcaption>
            </motion.figure>
          ))}
        </div>
      </div>
    </div>
  );
}
