import { forwardRef, useCallback, type ButtonHTMLAttributes } from "react";
import { motion, useMotionValue, useSpring } from "motion/react";
import { cn } from "@/lib/utils";

export interface MagneticButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /**
   * Strength multiplier for the magnetic pull. Values between 0 and 1 recommended.
   */
  strength?: number;
}

export const MagneticButton = forwardRef<HTMLButtonElement, MagneticButtonProps>(
  ({ children, className, strength = 0.35, ...props }, ref) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const springX = useSpring(x, { stiffness: 220, damping: 18, mass: 0.32 });
    const springY = useSpring(y, { stiffness: 220, damping: 18, mass: 0.32 });

    const reset = useCallback(() => {
      x.stop();
      y.stop();
      x.set(0);
      y.set(0);
    }, [x, y]);

    const handlePointerMove = useCallback(
      (event: React.PointerEvent<HTMLButtonElement>) => {
        const { currentTarget } = event;
        const rect = currentTarget.getBoundingClientRect();
        const relativeX = event.clientX - rect.left;
        const relativeY = event.clientY - rect.top;
        const offsetX = (relativeX / rect.width - 0.5) * rect.width * strength;
        const offsetY = (relativeY / rect.height - 0.5) * rect.height * strength;
        x.set(offsetX);
        y.set(offsetY);
      },
      [strength, x, y],
    );

    return (
      <motion.button
        ref={ref}
        type={props.type ?? "button"}
        style={{ x: springX, y: springY, willChange: "transform" }}
        onPointerMove={handlePointerMove}
        onPointerLeave={reset}
        onPointerCancel={reset}
        className={cn(
          "group/magnetic relative inline-flex items-center justify-center overflow-hidden rounded-full px-6 py-3 text-sm font-semibold tracking-wide transition-all duration-300 ease-out",
          "bg-[var(--glass-gradient)] text-primary-foreground shadow-[var(--shadow-soft)] backdrop-blur-xl",
          "hover:-translate-y-0.5 hover:shadow-[0_0_40px_rgba(108,99,255,0.35)] focus-visible:ring-2 focus-visible:ring-primary/40",
          "before:pointer-events-none before:absolute before:inset-0 before:rounded-full before:border before:border-white/20 before:bg-gradient-to-r before:from-white/20 before:to-white/5 before:opacity-50 before:transition-opacity before:duration-500",
          "after:pointer-events-none after:absolute after:inset-[-40%] after:bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.45),transparent_70%)] after:opacity-0 after:transition-all after:duration-500 after:blur-3xl group-hover/magnetic:after:opacity-100",
          className,
        )}
        {...props}
      >
        <span className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 ease-out group-hover/magnetic:opacity-40">
          <span className="absolute inset-0 bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.45),transparent_60%)] blur-3xl" />
        </span>
        <span className="relative z-10">{children}</span>
      </motion.button>
    );
  },
);

MagneticButton.displayName = "MagneticButton";
