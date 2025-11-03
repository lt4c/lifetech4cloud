import { forwardRef, useMemo, type CSSProperties, type HTMLAttributes } from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

type CSSVars = CSSProperties & Record<string, string | number>;

export interface GlassSurfaceProps extends HTMLAttributes<HTMLDivElement> {
  /**
   * Blur intensity applied to the backdrop filter in pixels.
   * Defaults to 18px for a creamy glass sheen.
   */
  blur?: number;
  /**
   * Overall alpha applied to the diffused sheen layer.
   */
  opacity?: number;
  /**
   * Radius applied to the outer shell. Accepts pixel values or any CSS radius token.
   */
  borderRadius?: number | string;
  /**
   * Optional override for the gradient background.
   */
  gradientFrom?: string;
  gradientTo?: string;
  /**
   * Adds a subtle pulsing glow animation when enabled.
   */
  pulse?: boolean;
  /**
   * Elevation shadow. Disable when composition already applies external shadows.
   */
  glow?: boolean;
}

export const GlassSurface = forwardRef<HTMLDivElement, GlassSurfaceProps>(
  (
    {
      children,
      className,
      blur = 18,
      opacity = 0.18,
      borderRadius = 24,
      gradientFrom,
      gradientTo,
      pulse = false,
      glow = true,
      style,
      ...props
    },
    ref,
  ) => {
    const styles = useMemo<CSSVars>(() => {
      const borderRadiusValue = typeof borderRadius === "number" ? `${borderRadius}px` : borderRadius;
      const gradient =
        gradientFrom && gradientTo
          ? `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})`
          : undefined;
      const base: CSSVars = {
        borderRadius: borderRadiusValue,
        backdropFilter: `blur(${blur}px)`,
        WebkitBackdropFilter: `blur(${blur}px)`,
        ["--glass-opacity"]: opacity,
      };
      if (gradient) {
        base.backgroundImage = gradient;
      }
      return base;
    }, [blur, opacity, borderRadius, gradientFrom, gradientTo]);

    return (
      <motion.div
        ref={ref}
        initial={{ opacity: 0, scale: 0.98, y: 4 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          "group/glass relative isolate overflow-hidden border border-white/10 bg-[var(--glass-gradient)] text-foreground shadow-[var(--shadow-soft)] transition-all duration-500 ease-out dark:border-white/5",
          glow && "hover:shadow-[var(--shadow-glow)]",
          pulse && "animate-[pulse_6s_ease-in-out_infinite]",
          className,
        )}
        style={{ ...styles, ...style }}
        {...props}
      >
        <div className="pointer-events-none absolute inset-0 bg-white/10 mix-blend-soft-light opacity-[calc(var(--glass-opacity,0.18)+0.05)] transition-opacity duration-700 dark:bg-white/5" />
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          animate={{ backgroundPosition: ["0% 50%", "100% 50%"] }}
          transition={{ repeat: Infinity, repeatType: "reverse", duration: 18, ease: "linear" }}
          style={{
            backgroundImage:
              "radial-gradient(180px circle at 0% 0%, rgba(255,255,255,0.18), transparent 65%), radial-gradient(220px circle at 100% 0%, rgba(147,197,253,0.16), transparent 60%)",
            opacity: 0.5,
          }}
        />
        <div className="relative z-10">{children}</div>
      </motion.div>
    );
  },
);

GlassSurface.displayName = "GlassSurface";
