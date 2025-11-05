import { forwardRef, useMemo, useRef, type HTMLAttributes } from "react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

type CSSVars = React.CSSProperties & Record<string, string | number>;

export interface FluidContainerProps extends HTMLAttributes<HTMLDivElement> {
  borderRadius?: number | string;
  intensity?: number;
  blur?: number;
}

export const FluidContainer = forwardRef<HTMLDivElement, FluidContainerProps>(
  ({ className, children, borderRadius = 28, intensity = 0.24, blur = 28, style, ...props }, ref) => {
    const pointerRaf = useRef<number>();

    const styles = useMemo<CSSVars>(() => {
      const radiusValue = typeof borderRadius === "number" ? `${borderRadius}px` : borderRadius;
      return {
        borderRadius: radiusValue,
        ["--pointer-x"]: "50%",
        ["--pointer-y"]: "50%",
        ["--pointer-opacity"]: "0",
        ["--pointer-intensity"]: intensity,
        backdropFilter: `blur(${blur}px)`,
        WebkitBackdropFilter: `blur(${blur}px)`,
      };
    }, [borderRadius, intensity, blur]);

    const updatePointer = (event: React.PointerEvent<HTMLDivElement>, opacity: number) => {
      const element = event.currentTarget;
      if (pointerRaf.current) {
        cancelAnimationFrame(pointerRaf.current);
      }
      pointerRaf.current = requestAnimationFrame(() => {
        const rect = element.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        element.style.setProperty("--pointer-x", `${x}%`);
        element.style.setProperty("--pointer-y", `${y}%`);
        element.style.setProperty("--pointer-opacity", `${opacity}`);
      });
    };

    const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => updatePointer(event, 1);
    const handlePointerEnter = (event: React.PointerEvent<HTMLDivElement>) => updatePointer(event, 1);
    const handlePointerLeave = (event: React.PointerEvent<HTMLDivElement>) => {
      const { currentTarget } = event;
      currentTarget.style.setProperty("--pointer-opacity", "0");
    };

    return (
      <motion.div
        ref={ref}
        className={cn(
          "group/fluid relative isolate overflow-hidden border border-transparent bg-[var(--glass-gradient)]/70 shadow-[var(--shadow-soft)] transition-all duration-500 ease-out",
          className,
        )}
        style={{ ...styles, ...style }}
        onPointerMove={handlePointerMove}
        onPointerEnter={handlePointerEnter}
        onPointerLeave={handlePointerLeave}
        whileHover={{ scale: 1.01 }}
        transition={{ type: "spring", stiffness: 120, damping: 18, mass: 0.6 }}
        {...props}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[var(--pointer-opacity)] transition-opacity duration-500 ease-out"
          style={{
            background:
              "radial-gradient(220px circle at var(--pointer-x) var(--pointer-y), hsl(var(--primary) / calc(var(--pointer-intensity) + 0.2)), transparent 65%)",
          }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-[calc(var(--pointer-opacity)*0.65)] transition-opacity duration-500 ease-out"
          style={{
            background:
              "radial-gradient(320px circle at var(--pointer-x) var(--pointer-y), hsl(var(--accent) / calc(var(--pointer-intensity) + 0.15)), transparent 70%)",
          }}
        />
        <div className="relative z-10">{children}</div>
      </motion.div>
    );
  },
);

FluidContainer.displayName = "FluidContainer";
