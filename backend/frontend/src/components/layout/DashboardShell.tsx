import type { PropsWithChildren, ReactNode } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import { Header } from "./Header";
import { Footer } from "./Footer";

interface DashboardShellProps extends PropsWithChildren {
  banner?: ReactNode;
}

export function DashboardShell({ children, banner }: DashboardShellProps) {
  return (
    <SidebarProvider>
      <div className="relative flex min-h-screen w-full overflow-hidden bg-background">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-32 top-16 h-72 w-72 rounded-full bg-primary/30 blur-3xl md:-left-20" />
          <div className="absolute -right-24 bottom-10 h-80 w-80 rounded-full bg-accent/25 blur-3xl" />
        </div>
        <AppSidebar />
        <SidebarInset className="flex min-h-screen flex-1 flex-col bg-transparent">
          {banner}
          <Header />
          <main className="relative flex-1 px-4 pb-10 pt-4 sm:px-6 lg:px-10">
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-8">{children}</div>
          </main>
          <Footer />
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
}
