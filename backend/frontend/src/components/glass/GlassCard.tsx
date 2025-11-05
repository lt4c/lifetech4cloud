import { type ComponentProps } from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

type MotionDivProps = ComponentProps<typeof motion.div>;

interface GlassCardProps extends Omit<MotionDivProps, "children"> {
  children: MotionDivProps["children"];
  variant?: "default" | "liquid" | "surface";
  hover?: boolean;
  glow?: boolean;
}

export function GlassCard({
  children,
  className,
  variant = "default",
  hover = true,
  glow = false,
  ...props
}: GlassCardProps) {
  const variantClasses = {
    default: "glass-card",
    liquid: "liquid-glass",
    surface: "glass-surface",
  } as const;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
      whileHover={hover ? { scale: 1.02, y: -4 } : undefined}
      className={cn(
        variantClasses[variant],
        "rounded-2xl p-6",
        hover && "hover-lift",
        glow && "glow-soft",
        className,
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}

