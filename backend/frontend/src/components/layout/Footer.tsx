import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Code2 } from "lucide-react";
import { fetchPlatformVersion } from "@/lib/api-client";
import { FluidContainer, GlassSurface } from "@/components/glass";
import { cn } from "@/lib/utils";

export function Footer() {
  const { data } = useQuery({
    queryKey: ["platform-version"],
    queryFn: fetchPlatformVersion,
    staleTime: 300_000,
  });

  const versionLabel = useMemo(() => {
    if (!data) {
      return "dev v0.0.0";
    }
    return `${data.channel} ${data.version}`;
  }, [data]);

  return (
    <footer className="w-full px-4 pb-4 sm:px-6 lg:px-10">
      <GlassSurface
        className={cn(
          "flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/75 px-4 py-4 text-xs text-muted-foreground backdrop-blur-2xl dark:border-white/5 dark:bg-white/10 sm:flex-row sm:items-center sm:justify-between sm:px-6",
        )}
        glow={false}
      >
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary/85 to-accent/60 text-primary-foreground shadow-[var(--shadow-soft)]">
            <Code2 className="h-4 w-4" />
          </span>
          <div className="leading-tight">
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/80">Build</p>
            <p className="text-sm font-medium text-foreground">{versionLabel}</p>
          </div>
        </div>

        <FluidContainer className="flex w-full items-center justify-between rounded-2xl border border-white/10 px-4 py-3 text-xs text-muted-foreground sm:w-auto sm:min-w-[240px]">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-success" />
            <div className="text-left">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                Live status
              </p>
              <p className="text-sm font-medium text-foreground">All services operational</p>
            </div>
          </div>
          <a
            href="https://status.lt4c.io.vn"
            target="_blank"
            rel="noreferrer"
            className="text-[11px] font-semibold uppercase tracking-wider text-primary hover:underline"
          >
            Status page
          </a>
        </FluidContainer>
      </GlassSurface>
    </footer>
  );
}
