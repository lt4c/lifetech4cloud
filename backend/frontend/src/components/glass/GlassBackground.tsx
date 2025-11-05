import { cn } from "@/lib/utils";

interface GlassBackgroundProps {
  className?: string;
}

export function GlassBackground({ className }: GlassBackgroundProps) {
  return (
    <div className={cn("glass-background", className)}>
      <div className="glass-background__orb glass-background__orb--primary" />
      <div className="glass-background__orb glass-background__orb--secondary" />
      <div className="glass-background__orb glass-background__orb--accent" />
      <div className="glass-background__grid" />
    </div>
  );
}
