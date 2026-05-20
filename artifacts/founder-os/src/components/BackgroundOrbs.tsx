import { motion } from "framer-motion";

export function BackgroundOrbs() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-[-1]">
      <div className="absolute inset-0 bg-background" />
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.15, 0.2, 0.15],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] rounded-full bg-primary/20 blur-[120px]"
      />
      <motion.div
        animate={{
          scale: [1, 1.3, 1],
          opacity: [0.1, 0.15, 0.1],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1,
        }}
        className="absolute bottom-[-10%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-secondary/15 blur-[120px]"
      />
      <motion.div
        animate={{
          y: [0, 50, 0],
          opacity: [0.05, 0.1, 0.05],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 2,
        }}
        className="absolute top-[30%] left-[40%] w-[30vw] h-[30vw] rounded-full bg-violet-600/10 blur-[100px]"
      />
    </div>
  );
}