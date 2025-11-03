import { useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bell, Coins, LogOut, Megaphone, MessageSquare, User } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { fetchAnnouncements } from "@/lib/api-client";
import type { AnnouncementSummary } from "@/lib/types";
import { FluidContainer, GlassSurface, HoverBorderGradient, MagneticButton } from "@/components/glass";

const formatInitials = (value: string) =>
  value
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase() || "U";

export function Header() {
  const { profile, logout, hasAdminAccess } = useAuth();
  const navigate = useNavigate();

  const handleLogout = useCallback(async () => {
    await logout();
    navigate("/");
  }, [logout, navigate]);

  const { data: announcements = [] } = useQuery<AnnouncementSummary[]>({
    queryKey: ["announcements"],
    queryFn: fetchAnnouncements,
    staleTime: 60_000,
  });

  const coins = profile?.coins ?? 0;
  const displayName = profile?.display_name || profile?.username || "Member";
  const email = profile?.email ?? "No email linked";
  const latestAnnouncement = announcements.at(0);

  const coinLabel = useMemo(() => new Intl.NumberFormat("en-US").format(coins), [coins]);

  return (
    <header className="sticky top-0 z-40 w-full px-4 pt-4 sm:px-6 lg:px-10">
      <GlassSurface
        className="flex min-h-[76px] items-center gap-4 rounded-3xl border border-white/10 bg-white/80 px-4 py-3 backdrop-blur-2xl dark:border-white/5 dark:bg-white/10 sm:px-6"
        glow={false}
      >
        <div className="flex items-center gap-3">
          <SidebarTrigger
            variant="glass"
            effect="border"
            size="icon"
            className="h-11 w-11 rounded-2xl border border-white/20 bg-white/70 text-foreground hover:bg-white/80 dark:border-white/10 dark:bg-white/10 dark:hover:bg-white/20"
          />

          <HoverBorderGradient className="hidden rounded-2xl border border-transparent bg-transparent px-3 py-2 md:flex">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary/90 to-accent/70 text-primary-foreground shadow-[var(--shadow-soft)]">
                <Coins className="h-5 w-5" />
              </span>
              <div className="leading-tight">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Available balance</p>
                <p className="text-lg font-semibold text-foreground">
                  {coinLabel}
                  <span className="ml-1 text-xs font-medium text-muted-foreground">coins</span>
                </p>
              </div>
            </div>
          </HoverBorderGradient>
        </div>

        <div className="hidden flex-1 items-center justify-center md:flex">
          <FluidContainer className="hidden min-w-[260px] flex-col gap-1 px-4 py-3 text-xs font-medium uppercase tracking-wide text-muted-foreground sm:flex">
            <span className="flex items-center gap-2 text-[11px] font-semibold text-muted-foreground/80">
              {latestAnnouncement ? "Latest update" : "Welcome back"}
              <span className="inline-flex h-2 w-2 rounded-full bg-success shadow-[0_0_0_6px_hsl(var(--success)/0.25)]" />
            </span>
            <span className="line-clamp-1 text-sm text-foreground">
              {latestAnnouncement ? latestAnnouncement.title : "Everything is running smoothly"}
            </span>
          </FluidContainer>
        </div>

        <div className="flex items-center gap-2">
          <MagneticButton
            strength={0.28}
            onClick={() => navigate("/support")}
            className="hidden text-xs uppercase tracking-[0.18em] text-primary-foreground shadow-[var(--shadow-glow)] hover:shadow-[var(--shadow-glow)] sm:inline-flex"
          >
            Support
          </MagneticButton>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="glass"
                size="icon"
                effect="border"
                aria-label="Notifications"
                className="relative h-11 w-11 rounded-2xl"
              >
                <Bell className="h-[1.1rem] w-[1.1rem]" />
                {announcements.length > 0 ? (
                  <span className="absolute right-2 top-2 inline-flex h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_0_6px_hsl(var(--primary)/0.35)]" />
                ) : null}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              sideOffset={12}
              className="w-80 overflow-hidden rounded-3xl border border-white/15 bg-background/80 p-0 backdrop-blur-2xl dark:border-white/10"
            >
              <div className="space-y-2 px-4 py-4">
                <DropdownMenuLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Notifications
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-white/10" />
                {announcements.length === 0 ? (
                  <p className="text-xs text-muted-foreground">You are all caught up.</p>
                ) : (
                  <ul className="space-y-2">
                    {announcements.slice(0, 5).map((item) => (
                      <li key={item.id}>
                        <DropdownMenuItem
                          className="flex flex-col gap-1 rounded-xl bg-white/5 px-3 py-2 text-left text-sm text-foreground transition hover:bg-white/10"
                          onSelect={() => navigate(`/announcements/${item.slug}`)}
                        >
                          <span className="font-semibold">{item.title}</span>
                          {item.excerpt && (
                            <span className="text-xs text-muted-foreground line-clamp-2">{item.excerpt}</span>
                          )}
                          {item.created_at ? (
                            <span className="text-[10px] uppercase tracking-wide text-muted-foreground/70">
                              {new Date(item.created_at).toLocaleString()}
                            </span>
                          ) : null}
                        </DropdownMenuItem>
                      </li>
                    ))}
                  </ul>
                )}
                <DropdownMenuSeparator className="bg-white/10" />
                <Button
                  variant="ghost"
                  effect="fluid"
                  className="w-full justify-between rounded-2xl text-xs font-semibold uppercase tracking-wider"
                  onClick={() => navigate("/announcements")}
                >
                  View all
                  <Megaphone className="h-4 w-4" />
                </Button>
                {hasAdminAccess ? (
                  <Button
                    variant="ghost"
                    effect="border"
                    className="w-full justify-between rounded-2xl text-xs font-semibold uppercase tracking-wider"
                    onClick={() => navigate("/admin/announcements")}
                  >
                    Manage board
                    <MessageSquare className="h-4 w-4" />
                  </Button>
                ) : null}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="glass" className="relative h-11 w-11 rounded-full p-0" effect="glow">
                <Avatar className="h-11 w-11">
                  {profile?.avatar_url ? (
                    <AvatarImage src={profile.avatar_url} alt={displayName} />
                  ) : (
                    <AvatarFallback className="uppercase">{formatInitials(displayName)}</AvatarFallback>
                  )}
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              sideOffset={12}
              className="w-64 overflow-hidden rounded-3xl border border-white/15 bg-background/85 p-0 backdrop-blur-2xl dark:border-white/10"
            >
              <div className="space-y-3 px-4 py-4">
                <DropdownMenuLabel className="space-y-1">
                  <p className="text-sm font-semibold text-foreground">{displayName}</p>
                  <p className="text-xs text-muted-foreground break-words">{email}</p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-white/10" />
                <DropdownMenuItem
                  onSelect={() => navigate("/profile")}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-foreground transition hover:bg-white/10"
                >
                  <User className="h-4 w-4 text-primary" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={() => navigate("/support")}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-foreground transition hover:bg-white/10"
                >
                  <MessageSquare className="h-4 w-4 text-primary" />
                  Support
                </DropdownMenuItem>
                <DropdownMenuItem
                  onSelect={() => navigate("/announcements")}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-foreground transition hover:bg-white/10"
                >
                  <Megaphone className="h-4 w-4 text-primary" />
                  Announcements
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-white/10" />
                <DropdownMenuItem
                  onSelect={handleLogout}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-destructive transition hover:bg-destructive/15"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </div>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </GlassSurface>
    </header>
  );
}
