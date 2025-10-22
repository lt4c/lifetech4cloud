import { Activity, Code2 } from "lucide-react";
import { useSidebar } from "@/components/ui/sidebar";
// optional: import { cn } from "@/lib/utils";

export function Footer() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const version = "devStable v1.2.67";

  // Fallback nếu project không có CSS var:
  // const leftPx = collapsed ? 64 : 256;

  return (
    <footer
      className={[
        "fixed bottom-0 right-0 border-t glass-panel text-xs text-muted-foreground z-40",
        "transition-[left] duration-200",
        collapsed
          ? "left-[var(--sidebar-width-icon)]" // khi thu gọn
          : "left-[var(--sidebar-width)]", // khi mở rộng
      ].join(" ")}
      // style={{ left: leftPx }} // dùng fallback px nếu cần
    >
      <div className="flex items-center justify-between px-6 py-2">
        <div className="flex items-center gap-1.5">
          <Code2 className="w-3.5 h-3.5 text-primary" />
          <span>Phiên bản: {version}</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-primary" />
          <span>© 2025 LT4C - ZynHash Production</span>
        </div>
      </div>
    </footer>
  );
}
