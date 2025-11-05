import { useCallback, useMemo } from "react";
import {
  Coins,
  Gift,
  LayoutDashboard,
  LogOut,
  Megaphone,
  MessageSquare,
  Package,
  Server,
  Settings,
  Shield,
  Ticket,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { Sidebar, useSidebar } from "@/components/ui/sidebar";
import { Button, buttonVariants } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";
import { GlassSurface, HoverBorderGradient } from "@/components/glass";

type NavItem = { title: string; url: string; icon: React.ComponentType<{ className?: string }> };

const menuItems: NavItem[] = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "VPS Manager", url: "/vps", icon: Server },
  { title: "Earn Coins", url: "/earn", icon: Gift },
  { title: "Referral Boost", url: "/gets-coin", icon: Coins },
  { title: "Gift codes", url: "/giftcode", icon: Ticket },
  { title: "Support", url: "/support", icon: MessageSquare },
];

const adminItems: NavItem[] = [
  { title: "Announcements", url: "/admin/announcements", icon: Megaphone },
  { title: "Users", url: "/admin/users", icon: Users },
  { title: "Roles & Access", url: "/admin/roles", icon: Shield },
  { title: "VPS Products", url: "/admin/vps-products", icon: Package },
  { title: "Gift codes", url: "/admin/giftcodes", icon: Gift },
  { title: "Worker Fleet", url: "/admin/workers", icon: Zap },
  { title: "Analytics", url: "/admin/analytics", icon: TrendingUp },
  { title: "System Logs", url: "/admin/logs", icon: Settings },
  { title: "Settings", url: "/admin/settings", icon: Settings },
];

const renderNavLink =
  (collapsed: boolean) =>
  ({ title, url, icon: Icon }: NavItem) =>
    (
      <li key={url}>
        <NavLink
          to={url}
          className={({ isActive }) =>
            cn(
              buttonVariants({
                variant: isActive ? "glass" : "ghost",
                effect: isActive ? "border" : "fluid",
                size: "lg",
              }),
              "group/nav relative flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all duration-300 ease-out",
              collapsed ? "h-12 justify-center px-0" : "justify-start",
              !isActive && "text-muted-foreground hover:text-foreground",
            )
          }
        >
          <Icon className={cn("h-5 w-5 shrink-0", !collapsed && "text-primary/80")} />
          {!collapsed && <span className="truncate">{title}</span>}
        </NavLink>
      </li>
    );

export function AppSidebar() {
  const { state } = useSidebar();
  const { hasAdminAccess, logout } = useAuth();
  const navigate = useNavigate();

  const collapsed = state === "collapsed";

  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/");
  }, [logout, navigate]);

  const sections = useMemo(
    () => [
      { heading: "Overview", items: menuItems },
      ...(hasAdminAccess ? [{ heading: "Admin", items: adminItems }] : []),
    ],
    [hasAdminAccess],
  );

  return (
    <Sidebar collapsible="icon" className="border-none bg-transparent px-3 py-6">
      <GlassSurface
        className="flex h-full flex-col gap-6 rounded-[2rem] border border-white/10 bg-white/15 px-3 py-5 shadow-none backdrop-blur-2xl dark:border-white/5 dark:bg-white/5"
        glow={false}
      >
        <div
          className={cn(
            "flex items-center gap-3 rounded-2xl border border-white/15 bg-white/60 px-3 py-3 text-left shadow-[var(--shadow-soft)] dark:border-white/5 dark:bg-white/10",
            collapsed && "justify-center px-0",
          )}
        >
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-accent to-secondary text-primary-foreground shadow-[var(--shadow-soft)]">
            <Server className="h-5 w-5" />
          </span>
          {!collapsed && (
            <div className="leading-tight">
              <p className="text-sm font-semibold text-foreground">LifeTech4Cloud</p>
              <p className="text-xs text-muted-foreground">Cloud control center</p>
            </div>
          )}
        </div>

        <nav className="lt4c-scrollbar flex-1 space-y-8 overflow-y-auto pr-1">
          {sections.map(({ heading, items }) => (
            <div key={heading} className="space-y-3">
              <p
                className={cn(
                  "px-3 text-[11px] font-semibold uppercase tracking-[0.32em] text-muted-foreground/70",
                  collapsed && "sr-only",
                )}
              >
                {heading}
              </p>
              <ul className={cn("space-y-2", collapsed && "space-y-1")}>{items.map(renderNavLink(collapsed))}</ul>
            </div>
          ))}
        </nav>

        <HoverBorderGradient className="rounded-2xl border border-transparent">
          <Button
            variant="ghost"
            effect="glow"
            className={cn(
              "flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-semibold text-destructive transition-all duration-300 ease-out hover:text-destructive",
              collapsed && "h-12 justify-center px-0",
            )}
            onClick={handleLogout}
          >
            <LogOut className="h-5 w-5" />
            {!collapsed && <span className="truncate">Sign out</span>}
          </Button>
        </HoverBorderGradient>
      </GlassSurface>
    </Sidebar>
  );
}
