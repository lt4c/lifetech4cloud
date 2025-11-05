import { memo, useMemo } from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

interface BlurTextProps {
  text: string;
  className?: string;
  delay?: number;
  animateBy?: "words" | "characters";
}

export const BlurText = memo(function BlurTextComponent({
  text,
  className,
  delay = 0,
  animateBy = "words",
}: BlurTextProps) {
  const items = useMemo(() => (animateBy === "words" ? text.split(" ") : text.split("")), [text, animateBy]);
  const delayIncrement = animateBy === "words" ? 0.08 : 0.03;

  return (
    <span className={cn("inline-block", className)}>
      {items.map((item, index) => (
        <motion.span
          key={`${item}-${index}`}
          initial={{ filter: "blur(10px)", opacity: 0 }}
          whileInView={{ filter: "blur(0px)", opacity: 1 }}
          viewport={{ once: true }}
          transition={{
            duration: 0.6,
            delay: delay / 1000 + index * delayIncrement,
            ease: [0.4, 0, 0.2, 1],
          }}
          className="inline-block"
          style={{ marginRight: animateBy === "words" ? "0.25em" : "0" }}
        >
          {item}
        </motion.span>
      ))}
    </span>
  );
});

BlurText.displayName = "BlurText";
