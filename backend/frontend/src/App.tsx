import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { AppSidebar } from "@/components/AppSidebar";
import { Header } from "@/components/Header";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Landing from "@/pages/Landing";
import Dashboard from "@/pages/Dashboard";
import Profile from "@/pages/Profile";
import VPS from "@/pages/VPS";
import Earn from "@/pages/Earn";
import GetsCoin from "@/pages/GetsCoin";
import Announcements from "@/pages/Announcements";
import AnnouncementDetail from "@/pages/AnnouncementDetail";
import Support from "@/pages/Support";
import Giftcode from "@/pages/Giftcode";
import Users from "@/pages/admin/Users";
import Roles from "@/pages/admin/Roles";
import Workers from "@/pages/admin/Workers";
import VpsProductsAdmin from "@/pages/admin/VpsProducts";
import GiftcodesAdmin from "@/pages/admin/Giftcodes";
import AdminAnnouncements from "@/pages/admin/Announcements";
import Analytics from "@/pages/admin/Analytics";
import Settings from "@/pages/admin/Settings";
import NotFound from "@/pages/NotFound";
import { ThreeDot } from "react-loading-indicators";
import { Footer } from "@/components/Footer";
import { fetchBannerMessage } from "@/lib/api-client";
import type { BannerMessage } from "@/lib/types";

const queryClient = new QueryClient();

const BANNER_STORAGE_KEY = "lt4c.banner.dismissed";
const BANNER_COOLDOWN_MS = 30 * 60 * 1000;

const GlobalBanner = () => {
  const { data } = useQuery<BannerMessage>({
    queryKey: ["banner-message"],
    queryFn: fetchBannerMessage,
    staleTime: 5 * 60 * 1000,
  });

  const message = useMemo(() => (data?.message ?? "").trim(), [data?.message]);
  const identifier = useMemo(
    () => (message ? `${message}|${data?.updated_at ?? ""}` : ""),
    [message, data?.updated_at],
  );
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!identifier) {
      setVisible(false);
      return;
    }
    if (typeof window === "undefined") {
      return;
    }
    const raw = window.localStorage.getItem(BANNER_STORAGE_KEY);
    if (!raw) {
      setVisible(true);
      return;
    }
    let timeoutId: ReturnType<typeof window.setTimeout> | undefined;
    try {
      const stored = JSON.parse(raw) as { identifier?: string; dismissedAt?: number };
      if (stored.identifier !== identifier) {
        setVisible(true);
      } else if (!stored.dismissedAt) {
        setVisible(true);
      } else {
        const elapsed = Date.now() - stored.dismissedAt;
        if (elapsed >= BANNER_COOLDOWN_MS) {
          setVisible(true);
        } else {
          setVisible(false);
          timeoutId = window.setTimeout(() => {
            setVisible(true);
          }, BANNER_COOLDOWN_MS - elapsed);
        }
      }
    } catch {
      setVisible(true);
    }
    return () => {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [identifier]);

  const handleDismiss = useCallback(() => {
    if (typeof window !== "undefined" && identifier) {
      window.localStorage.setItem(
        BANNER_STORAGE_KEY,
        JSON.stringify({ identifier, dismissedAt: Date.now() }),
      );
    }
    setVisible(false);
  }, [identifier]);

  useEffect(() => {
    if (!visible) {
      return;
    }
    if (typeof document === "undefined") {
      return;
    }
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [visible]);

  if (!identifier || !visible) {
    return null;
  }

  if (typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 dark:bg-black/60 px-6 backdrop-blur-sm">
      <div className="glass-card w-full max-w-2xl space-y-6 rounded-3xl border border-primary/40 bg-background/95 p-6 shadow-2xl">
        <div className="space-y-3">
          <p className="whitespace-pre-wrap text-base leading-relaxed text-foreground">{message}</p>
          {data?.updated_at && (
            <p className="text-xs text-muted-foreground">
              Cập nhật: {new Date(data.updated_at).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex justify-end">
          <Button variant="outline" onClick={handleDismiss}>
            Đã hiểu
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
};

const DashboardLayout = ({ children }: { children: ReactNode }) => (
  <SidebarProvider>
    <div className="min-h-screen flex w-full">
      <AppSidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <GlobalBanner />
          {children}
        </main>
        <Footer />
      </div>
    </div>
  </SidebarProvider>
);

const LoadingScreen = () => (
  <div className="flex min-h-screen items-center justify-center bg-background text-muted-foreground">
    <ThreeDot
      variant="bounce"
      color="#ffac00"
      size="large"
      text="Đang tải nội dung từ server"
      textColor=""
    />
  </div>
);

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return <LoadingScreen />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <DashboardLayout>{children}</DashboardLayout>;
};

const AdminRoute = ({ children }: { children: ReactNode }) => {
  const { isLoading, isAuthenticated, hasAdminAccess } = useAuth();
  if (isLoading) {
    return <LoadingScreen />;
  }
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  if (!hasAdminAccess) {
    return <Navigate to="/dashboard" replace />;
  }
  return <DashboardLayout>{children}</DashboardLayout>;
};

const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<Landing />} />
    <Route
      path="/dashboard"
      element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      }
    />
    <Route
      path="/profile"
      element={
        <ProtectedRoute>
          <Profile />
        </ProtectedRoute>
      }
    />
    <Route
      path="/vps"
      element={
        <ProtectedRoute>
          <VPS />
        </ProtectedRoute>
      }
    />
    <Route
      path="/earn"
      element={
        <ProtectedRoute>
          <Earn />
        </ProtectedRoute>
      }
    />
    <Route
      path="/gets-coin"
      element={
        <ProtectedRoute>
          <GetsCoin />
        </ProtectedRoute>
      }
    />
    <Route
      path="/announcements"
      element={
        <ProtectedRoute>
          <Announcements />
        </ProtectedRoute>
      }
    />
    <Route
      path="/announcements/:slug"
      element={
        <ProtectedRoute>
          <AnnouncementDetail />
        </ProtectedRoute>
      }
    />
    <Route
      path="/support"
      element={
        <ProtectedRoute>
          <Support />
        </ProtectedRoute>
      }
    />
    <Route
      path="/giftcode"
      element={
        <ProtectedRoute>
          <Giftcode />
        </ProtectedRoute>
      }
    />
    <Route
      path="/admin/users"
      element={
        <AdminRoute>
          <Users />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/roles"
      element={
        <AdminRoute>
          <Roles />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/vps-products"
      element={
        <AdminRoute>
          <VpsProductsAdmin />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/workers"
      element={
        <AdminRoute>
          <Workers />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/giftcodes"
      element={
        <AdminRoute>
          <GiftcodesAdmin />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/announcements"
      element={
        <AdminRoute>
          <AdminAnnouncements />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/analytics"
      element={
        <AdminRoute>
          <Analytics />
        </AdminRoute>
      }
    />
    <Route
      path="/admin/settings"
      element={
        <AdminRoute>
          <Settings />
        </AdminRoute>
      }
    />
    <Route path="*" element={<NotFound />} />
  </Routes>
);

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
