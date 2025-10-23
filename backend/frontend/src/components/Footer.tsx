import { Activity, Code2 } from "lucide-react";

import { cn } from "@/lib/utils";

export function Footer() {
  const version = "devStable v1.2.68";

  return (
    <footer
      className={cn(
        "border-t glass-panel text-xs text-muted-foreground",
        "w-full px-4 sm:px-6 py-2",
      )}
    >
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-1.5">
          <Code2 className="h-3.5 w-3.5 text-primary" />
          <span>Phiên bản: {version}</span>
        </div>

        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Activity className="h-3.5 w-3.5 text-primary" />
          <span>© 2025 LT4C · ZynHash Production</span>
        </div>
      </div>
    </footer>
  );
}
