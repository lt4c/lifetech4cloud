import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Server, Plus, Power, RefreshCw, Loader2, ExternalLink, Terminal, StopCircle } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  fetchVpsProducts,
  fetchVpsSessions,
  createVpsSession,
  stopVpsSession,
  fetchVpsSessionLog,
  ApiError,
} from "@/lib/api-client";
import type { VpsProduct, VpsSession } from "@/lib/types";
import { toast } from "@/components/ui/sonner";

type VmVariant = "linux" | "windows";

const VM_VARIANTS: VmVariant[] = ["linux", "windows"];

const VARIANT_ACTIONS: Record<VmVariant, number> = {
  linux: 1,
  windows: 2,
};

const VARIANT_LABELS: Record<VmVariant, string> = {
  linux: "Linux",
  windows: "Windows",
};

const VARIANT_DESCRIPTIONS: Record<VmVariant, string> = {
  linux: "Headless Ubuntu environment provisioned through worker action 1.",
  windows: "Windows 10 environment provisioned through worker action 2.",
};

const idempotencyKey = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
};

const normalizeAction = (raw: unknown): number | null => {
  if (typeof raw === "number" && Number.isFinite(raw)) {
    return raw;
  }
  if (typeof raw === "string") {
    const parsed = Number(raw);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return null;
};

const actionToVariant = (action: number | null | undefined): VmVariant | null => {
  switch (action) {
    case 1:
      return "linux";
    case 2:
      return "windows";
    default:
      return null;
  }
};

const resolveSessionVariant = (session: VpsSession): VmVariant | null => {
  const action =
    normalizeAction(session.worker_action) ??
    normalizeAction(session.provision_action) ??
    normalizeAction(session.product?.provision_action);
  return actionToVariant(action);
};

const workerActionLabel = (session: VpsSession): string => {
  const variant = resolveSessionVariant(session);
  if (variant) {
    return VARIANT_LABELS[variant];
  }
  const fallback =
    normalizeAction(session.worker_action) ??
    normalizeAction(session.provision_action) ??
    normalizeAction(session.product?.provision_action);
  if (fallback === 3) {
    return "Dummy";
  }
  return "Unknown";
};

const statusBadge = (status: string) => {
  switch (status) {
    case "ready":
      return { variant: "default" as const, className: "bg-success text-success-foreground" };
    case "failed":
      return { variant: "destructive" as const, className: "" };
    case "provisioning":
    case "pending":
      return { variant: "outline" as const, className: "border-warning text-warning" };
    case "deleted":
    case "expired":
      return { variant: "secondary" as const, className: "bg-muted text-muted-foreground" };
    default:
      return { variant: "secondary" as const, className: "" };
  }
};

const formatDateTime = (iso?: string | null) => {
  if (!iso) return "--";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString();
};

const computeRefetchInterval = (session: VpsSession): number | false => {
  if (!session.has_log || !session.worker_route) {
    return false;
  }
  const status = session.status;
  if (status === "deleted" || status === "failed" || status === "expired") {
    return false;
  }
  if (status === "ready") {
    return 15000;
  }
  if (status === "provisioning" || status === "pending") {
    return 4000;
  }
  return 8000;
};

const useSessionLog = (session: VpsSession) => {
  const enabled = Boolean(session.has_log && session.worker_route);
  return useQuery({
    queryKey: ["vps-session-log", session.id],
    queryFn: () => fetchVpsSessionLog(session.id),
    enabled,
    refetchInterval: () => computeRefetchInterval(session),
    retry: false,
  });
};

export default function VPS() {
  const queryClient = useQueryClient();
  const [launcherOpen, setLauncherOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<VpsProduct | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<VmVariant | null>(null);

  const {
    data: products = [],
    isLoading: productsLoading,
  } = useQuery({
    queryKey: ["vps-products"],
    queryFn: fetchVpsProducts,
    staleTime: 60_000,
  });

  const {
    data: sessions = [],
    isLoading: sessionsLoading,
    refetch: refetchSessions,
  } = useQuery({
    queryKey: ["vps-sessions"],
    queryFn: fetchVpsSessions,
    staleTime: 10_000,
  });

  const resetLauncherState = () => {
    setSelectedProduct(null);
    setSelectedVariant(null);
  };

  useEffect(() => {
    if (!selectedProduct) {
      setSelectedVariant(null);
      return;
    }
    const defaultVariant = actionToVariant(normalizeAction(selectedProduct.provision_action));
    setSelectedVariant(defaultVariant);
  }, [selectedProduct]);

  const visibleSessions = useMemo(() => {
    const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
    const now = Date.now();
    return sessions.filter((session) => {
      if (session.status !== "deleted") {
        return true;
      }
      const reference = session.updated_at ?? session.created_at;
      if (!reference) {
        return false;
      }
      const timestamp = new Date(reference).getTime();
      if (Number.isNaN(timestamp)) {
        return false;
      }
      return now - timestamp < sevenDaysMs;
    });
  }, [sessions]);

  const sortedSessions = useMemo(() => {
    const priority = (status: string) => {
      switch (status) {
        case "provisioning":
        case "pending":
          return 0;
        case "ready":
          return 1;
        case "failed":
          return 2;
        case "expired":
          return 3;
        case "deleted":
          return 4;
        default:
          return 5;
      }
    };
    return [...visibleSessions].sort((a, b) => {
      const diff = priority(a.status) - priority(b.status);
      if (diff !== 0) return diff;
      const aTime = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bTime = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bTime - aTime;
    });
  }, [visibleSessions]);

  const createSession = useMutation({
    mutationFn: ({ variant, productId }: { variant: VmVariant; productId: string }) =>
      createVpsSession({
        productId,
        vmType: variant,
        workerAction: VARIANT_ACTIONS[variant],
        idempotencyKey: idempotencyKey(),
      }),
    onSuccess: (session) => {
      toast("Provisioning request sent to worker.");
      resetLauncherState();
      setLauncherOpen(false);
      refetchSessions();
      queryClient.invalidateQueries({ queryKey: ["vps-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["vps-session-log", session.id] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError && error.status === 400) {
        const detail = (error.data as { detail?: string })?.detail ?? "Provisioning failed.";
        toast(detail);
        return;
      }
      const message = error instanceof Error ? error.message : "Unable to provision VPS.";
      toast(message);
    },
  });

  const stopSession = useMutation({
    mutationFn: stopVpsSession,
    onSuccess: (session) => {
      toast("Stop command sent to worker.");
      refetchSessions();
      queryClient.invalidateQueries({ queryKey: ["vps-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["vps-session-log", session.id] });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Unable to stop session.";
      toast(message);
    },
  });

  const handleLaunch = () => {
    if (!selectedProduct) {
      toast("Select a VPS package before launching.");
      return;
    }
    if (!selectedVariant) {
      toast("Choose an operating system to continue.");
      return;
    }
    createSession.mutate({ variant: selectedVariant, productId: selectedProduct.id });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2">VPS Control</h1>
          <p className="text-muted-foreground">
            Launch, monitor, and stop worker-provisioned VPS sessions from a single panel.
          </p>
        </div>
        <Button className="gap-2" onClick={() => setLauncherOpen(true)}>
          <Plus className="w-4 h-4" />
          Launch VPS
        </Button>
        <Dialog
          open={launcherOpen}
          onOpenChange={(open) => {
            setLauncherOpen(open);
            if (!open) {
              resetLauncherState();
            }
          }}
        >
          <DialogContent className="glass-panel max-w-4xl">
            <DialogHeader>
              <DialogTitle>Select VPS package</DialogTitle>
              <DialogDescription>Pick a machine configuration, then choose an operating system to launch.</DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div>
                <p className="text-sm font-semibold mb-2">Available packages</p>
                {productsLoading && <p className="text-sm text-muted-foreground px-1">Loading packages�</p>}
                {!productsLoading && products.length === 0 && (
                  <p className="text-sm text-muted-foreground px-1">No VPS packages are available right now.</p>
                )}
                {!productsLoading && products.length > 0 && (
                  <div className="grid gap-4 md:grid-cols-3">
                    {products.map((product) => {
                      const isActive = selectedProduct?.id === product.id;
                      return (
                        <Card
                          key={product.id}
                          role="button"
                          tabIndex={0}
                          className={`glass-card transition-all ${isActive ? "ring-2 ring-primary" : "hover:ring-1 hover:ring-primary/70"}`}
                          onClick={() => setSelectedProduct(product)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter" || event.key === " ") {
                              event.preventDefault();
                              setSelectedProduct(product);
                            }
                          }}
                        >
                          <CardHeader>
                            <CardTitle className="text-lg">{product.name}</CardTitle>
                            <CardDescription className="text-xs line-clamp-3">
                              {product.description || "Managed worker capacity."}
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="text-2xl font-semibold">
                              {product.price_coins.toLocaleString()}{" "}
                              <span className="text-sm text-muted-foreground">coins</span>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
              <div>
                <p className="text-sm font-semibold mb-2">Operating system</p>
                <p className="text-xs text-muted-foreground">
                  {selectedProduct
                    ? "Select the worker action to run on this package."
                    : "Choose a package above to unlock operating system selection."}
                </p>
                <div className="mt-3 grid gap-4 md:grid-cols-2">
                  {VM_VARIANTS.map((variant) => {
                    const isSelected = selectedVariant === variant;
                    const disabled = !selectedProduct;
                    const defaultVariant =
                      selectedProduct && actionToVariant(normalizeAction(selectedProduct.provision_action));
                    return (
                      <Card
                        key={variant}
                        role="button"
                        tabIndex={disabled ? -1 : 0}
                        className={`glass-card transition-all ${isSelected ? "ring-2 ring-primary" : ""} ${
                          disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:ring-1 hover:ring-primary/70"
                        }`}
                        onClick={() => {
                          if (disabled) return;
                          setSelectedVariant(variant);
                        }}
                        onKeyDown={(event) => {
                          if (disabled) return;
                          if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            setSelectedVariant(variant);
                          }
                        }}
                      >
                        <CardHeader>
                          <CardTitle className="flex items-center gap-2 text-lg">
                            <Server className="w-4 h-4" />
                            {VARIANT_LABELS[variant]}
                          </CardTitle>
                          <CardDescription className="text-xs">{VARIANT_DESCRIPTIONS[variant]}</CardDescription>
                        </CardHeader>
                        <CardContent className="text-xs text-muted-foreground space-y-1">
                          <div>Worker action #{VARIANT_ACTIONS[variant]}</div>
                          {defaultVariant === variant && (
                            <div className="font-medium text-primary">Default for this package</div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            </div>
            <DialogFooter className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  resetLauncherState();
                  setLauncherOpen(false);
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleLaunch} disabled={!selectedProduct || !selectedVariant || createSession.isPending} className="gap-2">
                {createSession.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Provisioning�
                  </>
                ) : (
                  "Launch"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {sessionsLoading && (
        <Card className="glass-card">
          <CardContent className="flex items-center gap-2 py-10">
            <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Loading sessions…</span>
          </CardContent>
        </Card>
      )}

      {!sessionsLoading && sortedSessions.length === 0 && (
        <Card className="glass-card">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No VPS sessions yet. Launch one to see worker activity.
          </CardContent>
        </Card>
      )}

      {!sessionsLoading &&
        sortedSessions.map((session) => {
          const isStopping = stopSession.isPending && stopSession.variables === session.id;
          return (
            <SessionCard
              key={session.id}
              session={session}
              onStop={() => stopSession.mutate(session.id)}
              isStopping={isStopping}
            />
          );
        })}
    </div>
  );
}

type SessionCardProps = {
  session: VpsSession;
  onStop: () => void;
  isStopping: boolean;
};

const SessionCard = ({ session, onStop, isStopping }: SessionCardProps) => {
  const logQuery = useSessionLog(session);
  const status = statusBadge(session.status);
  const variantLabel = workerActionLabel(session);
  const canStop = !["deleted", "failed", "expired"].includes(session.status);

  return (
    <Card className="glass-card">
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Power className="w-4 h-4 text-primary" />
              {variantLabel}
            </CardTitle>
            <CardDescription className="text-xs">
              Session {session.id}
              {session.product?.name ? ` · ${session.product.name}` : ""}
            </CardDescription>
          </div>
          <Badge variant={status.variant} className={status.className}>
            {session.status.toUpperCase()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="space-y-4 text-sm">
            <div className="space-y-2">
              <InfoRow label="Worker route" value={session.worker_route ?? "--"} />
              <InfoRow label="Created" value={formatDateTime(session.created_at)} />
              <InfoRow label="Updated" value={formatDateTime(session.updated_at)} />
              <InfoRow label="Log endpoint" value={session.log_url ?? "Not assigned"} />
            </div>
            {session.status === "ready" && session.rdp && <ConnectionDetails session={session} />}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="destructive"
                size="sm"
                className="gap-2"
                onClick={onStop}
                disabled={!canStop || isStopping}
              >
                {isStopping ? <Loader2 className="w-4 h-4 animate-spin" /> : <StopCircle className="w-4 h-4" />}
                {isStopping ? "Stopping…" : "Stop session"}
              </Button>
              {session.log_url && (
                <Button variant="outline" size="sm" className="gap-2" asChild>
                  <a href={session.log_url} target="_blank" rel="noreferrer">
                    <ExternalLink className="w-4 h-4" />
                    Open worker log
                  </a>
                </Button>
              )}
            </div>
          </div>
          <SessionLogPanel session={session} query={logQuery} />
        </div>
      </CardContent>
    </Card>
  );
};

const InfoRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex flex-col">
    <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
    <span className="break-all text-sm font-medium">{value}</span>
  </div>
);

const ConnectionDetails = ({ session }: { session: VpsSession }) => {
  const rdp = session.rdp;
  if (!rdp) return null;

  const { host, port, user, password } = rdp;
  if (!host && !port && !user && !password) {
    return null;
  }

  return (
    <div className="space-y-1 rounded-lg border border-border/40 bg-muted/30 p-3 text-xs">
      <p className="text-sm font-semibold">RDP credentials</p>
      {host && (
        <div>
          Host: <span className="font-mono">{host}</span>
        </div>
      )}
      {port && (
        <div>
          Port: <span className="font-mono">{port}</span>
        </div>
      )}
      {user && (
        <div>
          User: <span className="font-mono">{user}</span>
        </div>
      )}
      {password && (
        <div>
          Password: <span className="font-mono">{password}</span>
        </div>
      )}
    </div>
  );
};

type SessionLogPanelProps = {
  session: VpsSession;
  query: ReturnType<typeof useSessionLog>;
};

const SessionLogPanel = ({ session, query }: SessionLogPanelProps) => {
  const hasLog = Boolean(session.has_log && session.worker_route);
  const autoRefresh = computeRefetchInterval(session);
  let content: ReactNode;

  if (!hasLog) {
    content = <p className="text-xs text-muted-foreground">Worker has not exposed a log yet.</p>;
  } else if (query.isLoading) {
    content = (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Fetching log…
      </div>
    );
  } else if (query.isError) {
    const message =
      query.error instanceof ApiError
        ? query.error.message
        : query.error instanceof Error
          ? query.error.message
          : "Unable to load log.";
    content = <p className="text-xs text-destructive">{message}</p>;
  } else {
    const text = query.data ?? "";
    content = (
      <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed">{text || "(empty log)"}</pre>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-sm font-semibold">
          <Terminal className="w-4 h-4" />
          Worker log
        </p>
        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={() => query.refetch()}
          disabled={!hasLog || query.isFetching}
        >
          {query.isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Refresh
        </Button>
      </div>
      <ScrollArea className="h-[260px] rounded-md border border-border/40 bg-muted/20">
        <div className="p-4">{content}</div>
      </ScrollArea>
      <p className="text-[10px] text-muted-foreground">
        {autoRefresh ? `Auto refresh every ${Math.round(autoRefresh / 1000)}s.` : "Auto refresh disabled."}
      </p>
    </div>
  );
};
