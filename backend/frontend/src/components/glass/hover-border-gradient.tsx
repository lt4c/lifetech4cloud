import { forwardRef, useMemo, type HTMLAttributes } from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

type CSSVars = React.CSSProperties & Record<string, string | number>;

export interface HoverBorderGradientProps extends HTMLAttributes<HTMLDivElement> {
  borderRadius?: number | string;
  thickness?: number;
  glow?: boolean;
}

export const HoverBorderGradient = forwardRef<HTMLDivElement, HoverBorderGradientProps>(
  ({ children, className, borderRadius = 24, thickness = 2, glow = true, style, ...props }, ref) => {
    const styles = useMemo<CSSVars>(() => {
      const radiusValue = typeof borderRadius === "number" ? `${borderRadius}px` : borderRadius;
      return {
        borderRadius: radiusValue,
        ["--border-gradient-width"]: `${thickness}px`,
      };
    }, [borderRadius, thickness]);

    return (
      <motion.div
        ref={ref}
        className={cn(
          "group/gradient relative isolate overflow-hidden border border-border/20 bg-[var(--glass-gradient)] transition-all duration-500 ease-out",
          glow && "hover:shadow-[var(--shadow-glow)]",
          className,
        )}
        style={{ ...styles, ...style }}
        whileHover={{ scale: 1.01 }}
        transition={{ type: "spring", stiffness: 160, damping: 18, mass: 0.7 }}
        {...props}
      >
        <div className="pointer-events-none absolute inset-0 rounded-[inherit] border border-white/10 mix-blend-luminosity opacity-70 dark:border-white/5" />
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-[-1px] rounded-[inherit] opacity-0 blur-sm transition-opacity duration-500 ease-out group-hover/gradient:opacity-100"
          animate={{ rotate: [0, 360] }}
          transition={{ repeat: Infinity, duration: 24, ease: "linear" }}
          style={{
            background:
              "conic-gradient(from 120deg at 50% 50%, hsl(var(--primary) / 0.65), hsl(var(--accent) / 0.5), hsl(var(--secondary) / 0.65), hsl(var(--primary) / 0.65))",
          }}
        />
        <div className="pointer-events-none absolute inset-[var(--border-gradient-width)] rounded-[inherit] bg-[var(--glass-gradient)] opacity-90 backdrop-blur-[var(--blur-base)] dark:opacity-80" />
        <div className="relative z-10">{children}</div>
      </motion.div>
    );
  },
);

HoverBorderGradient.displayName = "HoverBorderGradient";
