import { useCallback } from "react";
import {
  LayoutDashboard,
  Server,
  Users,
  Shield,
  Megaphone,
  MessageSquare,
  TrendingUp,
  Settings,
  LogOut,
  Zap,
  Package,
  Gift,
  Coins,
  Ticket,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { Sidebar, useSidebar } from "@/components/ui/sidebar";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/utils";

type NavItem = { title: string; url: string; icon: typeof LayoutDashboard }

const menuItems: NavItem[] = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "VPS", url: "/vps", icon: Server },
  { title: "Earn Coins", url: "/earn", icon: Gift },
  { title: "Gets Coin", url: "/gets-coin", icon: Coins },
  { title: "Giftcode", url: "/giftcode", icon: Ticket },
  { title: "Support", url: "/support", icon: MessageSquare },
];

const adminItems: NavItem[] = [
  { title: "Announcements", url: "/admin/announcements", icon: Megaphone },
  { title: "Users", url: "/admin/users", icon: Users },
  { title: "Roles & Permissions", url: "/admin/roles", icon: Shield },
  { title: "VPS Products", url: "/admin/vps-products", icon: Package },
  { title: "Giftcode", url: "/admin/giftcodes", icon: Gift },
  { title: "Workers", url: "/admin/workers", icon: Zap },
  { title: "Analytics", url: "/admin/analytics", icon: TrendingUp },
  { title: "Settings", url: "/admin/settings", icon: Settings },
];

const navItemClasses = (
  collapsed: boolean,
  isActive: boolean,
) =>
  cn(
    "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm font-medium transition-all duration-200",
    "text-muted-foreground hover:text-primary hover:bg-primary/10",
    collapsed && "justify-center px-0",
    isActive &&
      "bg-gradient-to-r from-primary/20 via-primary/10 to-transparent text-primary shadow-sm",
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

  const renderNavItem = (item: NavItem) => (
    <li key={item.title}>
      <NavLink to={item.url} className={({ isActive }) => navItemClasses(collapsed, Boolean(isActive))}>
        <item.icon className="h-5 w-5 shrink-0" />
        {!collapsed && <span className="truncate">{item.title}</span>}
      </NavLink>
    </li>
  );

  return (
    <Sidebar
      collapsible="icon"
      className="border-r border-border/40 bg-gradient-to-b from-background/85 via-background/70 to-background/60 backdrop-blur-xl"
    >
      <div className="flex h-full flex-col px-3 py-5">
        <div
          className={cn(
            "mb-6 flex items-center gap-3 rounded-2xl border border-border/40 bg-background/70 px-3 py-3 shadow-sm",
            collapsed && "justify-center",
          )}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary text-background shadow-md">
            <Server className="h-5 w-5" />
          </div>
          {!collapsed && (
            <div className="leading-tight">
              <p className="text-sm font-semibold text-foreground">LifeTech4Cloud</p>
              <p className="text-xs text-muted-foreground">Cửa hàng Cloud Gaming</p>
            </div>
          )}
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto">
          <div>
            <p
              className={cn(
                "mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground/80",
                collapsed && "sr-only",
              )}
            >
              Menu chính
            </p>
            <ul className={cn("space-y-1", collapsed && "space-y-0")}>{menuItems.map(renderNavItem)}</ul>
          </div>

          {hasAdminAccess && (
            <div>
              <p
                className={cn(
                  "mb-2 px-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground/80",
                  collapsed && "sr-only",
                )}
              >
                Khu vực quản trị
              </p>
              <ul className={cn("space-y-1", collapsed && "space-y-0")}>{adminItems.map(renderNavItem)}</ul>
            </div>
          )}
        </nav>

        <div className="mt-6 border-t border-border/30 pt-4">
          <button
            type="button"
            onClick={handleLogout}
            className={cn(
              "flex items-center gap-3 rounded-2xl px-3 py-2 text-sm font-medium text-destructive transition",
              "hover:bg-destructive/10 hover:text-destructive",
              collapsed && "justify-center",
            )}
          >
            <LogOut className="h-5 w-5" />
            {!collapsed && <span>Đăng xuất</span>}
          </button>
        </div>
      </div>
    </Sidebar>
  );
}
