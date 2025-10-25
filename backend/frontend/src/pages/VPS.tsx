import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Server, Plus, Power, RefreshCw, Loader2, ExternalLink, Terminal, StopCircle, Copy, Check } from "lucide-react";

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
  linux: "Môi trường Ubuntu tối giản, phù hợp tác vụ nền và máy chủ.",
  windows: "Môi trường Windows 10 có giao diện, tiện điều khiển từ xa.",
};

const idempotencyKey = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2);
};

type ParsedSessionLog = {
  text: string;
  sshLink?: string;
  ipAddress?: string;
};

const normalizeSessionLog = (raw: string): ParsedSessionLog => {
  if (!raw) {
    return { text: "" };
  }

  const withoutBreaks = raw.replace(/<br\s*\/?>/gi, "\n");
  const normalized = withoutBreaks.replace(/\r\n?/g, "\n");
  const lines = normalized.split("\n");

  const sshLine = lines.find((line) => line.toLowerCase().includes("sshx link"));
  const ipLine = lines.find((line) => /^ip\s*:/i.test(line.trim()));

  const sshLink = sshLine ? sshLine.split(":").slice(1).join(":").trim() : undefined;

  let ipAddress: string | undefined;
  if (ipLine) {
    const match = ipLine.match(/IP\s*:\s*([0-9a-fA-F:.]+)/i);
    ipAddress = match ? match[1].trim() : ipLine.split(":").slice(1).join(":").trim();
  }

  return {
    text: normalized.trim(),
    sshLink: sshLink || undefined,
    ipAddress: ipAddress || undefined,
  };
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
    return "Mô phỏng";
  }
  return "Không xác định";
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

const statusLabel = (status: string) => {
  switch (status) {
    case "ready":
      return "Sẵn sàng";
    case "failed":
      return "Lỗi";
    case "provisioning":
      return "Đang khởi tạo";
    case "pending":
      return "Đang xử lý";
    case "deleted":
      return "Đã xóa";
    case "expired":
      return "Hết hạn";
    default:
      return status;
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
    select: normalizeSessionLog,
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

  const visibleSessions = useMemo(
    () => sessions.filter((session) => session.status !== "deleted"),
    [sessions],
  );

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
      toast("Đã gửi yêu cầu khởi tạo.");
      resetLauncherState();
      setLauncherOpen(false);
      refetchSessions();
      queryClient.invalidateQueries({ queryKey: ["vps-sessions"] });
      queryClient.invalidateQueries({ queryKey: ["vps-session-log", session.id] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError && error.status === 400) {
        const detail = (error.data as { detail?: string })?.detail ?? "Khởi tạo thất bại.";
        toast(detail);
        return;
      }
      const message = error instanceof Error ? error.message : "Không thể khởi tạo VPS.";
      toast(message);
    },
  });

  const stopSession = useMutation({
    mutationFn: stopVpsSession,
    onSuccess: (session) => {
      toast("Đã gửi lệnh dừng.");
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
            : "Không thể dừng phiên.";
      toast(message);
    },
  });

  const handleLaunch = () => {
    if (!selectedProduct) {
      toast("Hãy chọn gói VPS trước khi khởi chạy.");
      return;
    }
    if (!selectedVariant) {
      toast("Hãy chọn hệ điều hành để tiếp tục.");
      return;
    }
    createSession.mutate({ variant: selectedVariant, productId: selectedProduct.id });
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-2">Quản lý VPS</h1>
          <p className="text-muted-foreground">
            Khởi chạy, theo dõi và dừng các phiên VPS ở một nơi.
          </p>
        </div>
        <Button className="gap-2" onClick={() => setLauncherOpen(true)}>
          <Plus className="w-4 h-4" />
          Tạo VPS
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
              <DialogTitle>Chọn gói VPS</DialogTitle>
              <DialogDescription>Chọn cấu hình máy và hệ điều hành để bắt đầu.</DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div>
                <p className="text-sm font-semibold mb-2">Gói khả dụng</p>
                {productsLoading && <p className="text-sm text-muted-foreground px-1">Đang tải gói…</p>}
                {!productsLoading && products.length === 0 && (
                  <p className="text-sm text-muted-foreground px-1">Hiện chưa có gói khả dụng.</p>
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
                              {product.description || "Tài nguyên VPS được quản lý."}
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="text-2xl font-semibold">
                              {product.price_coins.toLocaleString()}{" "}
                              <span className="text-sm text-muted-foreground">coin</span>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
              <div>
                <p className="text-sm font-semibold mb-2">Hệ điều hành</p>
                <p className="text-xs text-muted-foreground">
                  {selectedProduct
                    ? "Chọn hệ điều hành bạn muốn dùng cho gói này."
                    : "Chọn gói ở trên để mở tùy chọn hệ điều hành."}
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
                          {defaultVariant === variant && (
                            <div className="font-medium text-primary">Mặc định cho gói này</div>
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
                Hủy
              </Button>
              <Button onClick={handleLaunch} disabled={!selectedProduct || !selectedVariant || createSession.isPending} className="gap-2">
                {createSession.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Đang khởi tạo…
                  </>
                ) : (
                  "Khởi chạy"
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
            <span className="text-sm text-muted-foreground">Đang tải danh sách phiên…</span>
          </CardContent>
        </Card>
      )}

      {!sessionsLoading && sortedSessions.length === 0 && (
        <Card className="glass-card">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Chưa có phiên VPS nào. Hãy khởi chạy để xem hoạt động.
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
  const hasLog = Boolean(session.has_log && session.worker_route);
  const parsedLog = logQuery.data;
  const logText = parsedLog?.text ?? "";
  const sshLink = parsedLog?.sshLink;
  const ipAddress = parsedLog?.ipAddress;
  const connectionSummary = ipAddress ? `${ipAddress} | Admin | Quackxlt4c` : null;
  const [showFullLog, setShowFullLog] = useState(false);
  const [sshCopied, setSshCopied] = useState(false);
  const [ipCopied, setIpCopied] = useState(false);

  useEffect(() => {
    setSshCopied(false);
  }, [sshLink]);

  useEffect(() => {
    setIpCopied(false);
  }, [connectionSummary]);

  const copyToClipboard = useCallback(async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch (error) {
      console.error("copy-to-clipboard", error);
      return false;
    }
  }, []);

  const handleCopySsh = useCallback(async () => {
    if (!sshLink) return;
    const ok = await copyToClipboard(sshLink);
    if (ok) {
      setSshCopied(true);
      setTimeout(() => setSshCopied(false), 1500);
    }
  }, [copyToClipboard, sshLink]);

  const handleCopyConnection = useCallback(async () => {
    if (!connectionSummary) return;
    const ok = await copyToClipboard(connectionSummary);
    if (ok) {
      setIpCopied(true);
      setTimeout(() => setIpCopied(false), 1500);
    }
  }, [connectionSummary, copyToClipboard]);

  const handleDownloadRdp = useCallback(() => {
    if (!ipAddress) return;
    const rdpContent = [
      "screen mode id:i:2",
      "use multimon:i:0",
      "session bpp:i:32",
      "compression:i:1",
      "keyboardhook:i:2",
      "redirectclipboard:i:1",
      "audio mode:i:0",
      "redirectprinters:i:0",
      "redirectcomports:i:0",
      "redirectsmartcards:i:1",
      "redirectdrives:i:0",
      "networkautodetect:i:1",
      "bandwidthautodetect:i:1",
      "displayconnectionbar:i:1",
      "authentication level:i:2",
      "prompt for credentials:i:0",
      "negotiate security layer:i:1",
      "remoteapplicationmode:i:0",
      "alternate shell:s:",
      "shell working directory:s:",
      `full address:s:${ipAddress}`,
      "gatewayhostname:s:",
      "gatewayusagemethod:i:4",
      "gatewaycredentialssource:i:4",
      "gatewayprofileusagemethod:i:0",
      "promptcredentialonce:i:0",
      "kdcproxyname:s:",
      "drivestoredirect:s:",
      "disableconnectionsharing:i:0",
      "autoreconnection enabled:i:1",
      "authentication service class:s:",
      "pcb:s:",
      "gatewaybrokeringtype:i:0",
      "prompt for credentials on client:i:0",
      "username:s:Admin",
    ].join("\n");
    const blob = new Blob([rdpContent], { type: "application/x-rdp" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    const filenameBase = session.worker_route || session.id;
    anchor.download = `${filenameBase}.rdp`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }, [ipAddress, session.id, session.worker_route]);

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
              Phiên {session.id}
              {session.product?.name ? ` · ${session.product.name}` : ""}
            </CardDescription>
          </div>
          <Badge variant={status.variant} className={status.className}>
            {statusLabel(session.status)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="space-y-4 text-sm">
            <div className="space-y-2">
              <InfoRow label="Máy chủ thực thi" value={session.worker_route ?? "--"} />
              <InfoRow label="Tạo lúc" value={formatDateTime(session.created_at)} />
              <InfoRow label="Cập nhật" value={formatDateTime(session.updated_at)} />
              <InfoRow label="Nhật ký" value={hasLog ? "Có sẵn" : "Chưa khả dụng"} />
              {sshLink && (
                <ActionRow
                  label="Kết nối SSHx"
                  displayValue={sshLink}
                  onCopy={handleCopySsh}
                  copied={sshCopied}
                />
              )}
              {connectionSummary && (
                <ActionRow
                  label="Kết nối RDP"
                  displayValue={connectionSummary}
                  onCopy={handleCopyConnection}
                  copied={ipCopied}
                  trailing={
                    <Button variant="outline" size="sm" onClick={handleDownloadRdp} className="px-2">
                      📂
                    </Button>
                  }
                />
              )}
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
                {isStopping ? "Đang dừng…" : "Dừng phiên"}
              </Button>
              {hasLog && (
                <Button variant="outline" size="sm" className="gap-2" onClick={() => setShowFullLog(true)}>
                  <ExternalLink className="w-4 h-4" />
                  Xem nhật ký
                </Button>
              )}
            </div>
          </div>
          <SessionLogPanel
            session={session}
            query={logQuery}
            logText={logText}
            onOpenFullLog={() => setShowFullLog(true)}
          />
        </div>
      </CardContent>
      <Dialog open={showFullLog} onOpenChange={setShowFullLog}>
        <DialogContent className="max-w-3xl space-y-4">
          <DialogHeader>
            <DialogTitle>Nhật ký hoạt động</DialogTitle>
            <DialogDescription>Toàn bộ nhật ký của phiên {session.worker_route ?? session.id}.</DialogDescription>
          </DialogHeader>
          <div className="max-h-[70vh] overflow-y-auto rounded-md border border-border/40 bg-muted/20 p-4">
            {logQuery.isLoading ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="w-4 h-4 animate-spin" />
                Đang tải nhật ký...
              </div>
            ) : logQuery.isError ? (
              <p className="text-sm text-destructive">
                {logQuery.error instanceof ApiError
                  ? logQuery.error.message
                  : logQuery.error instanceof Error
                    ? logQuery.error.message
                    : "Không thể tải nhật ký."}
              </p>
            ) : (
              <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed">{logText || "(nhật ký trống)"}</pre>
            )}
          </div>
          <DialogFooter className="justify-end">
            <Button variant="outline" onClick={() => setShowFullLog(false)}>
              Đóng
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

type ActionRowProps = {
  label: string;
  displayValue: string;
  onCopy: () => void;
  copied: boolean;
  trailing?: ReactNode;
};

const ActionRow = ({ label, displayValue, onCopy, copied, trailing }: ActionRowProps) => (
  <div className="flex flex-col">
    <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onCopy}
        className="flex items-center gap-2 rounded border border-transparent px-2 py-1 text-sm font-medium text-primary transition hover:border-primary/40 hover:bg-primary/5"
      >
        <span className="break-all text-left">{displayValue}</span>
        {copied ? <Check className="h-4 w-4 text-primary" /> : <Copy className="h-4 w-4 text-primary" />}
      </button>
      {trailing}
    </div>
  </div>
);

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
      <p className="text-sm font-semibold">Thông tin kết nối RDP</p>
      {host && (
        <div>
          Máy chủ: <span className="font-mono">{host}</span>
        </div>
      )}
      {port && (
        <div>
          Cổng: <span className="font-mono">{port}</span>
        </div>
      )}
      {user && (
        <div>
          Tài khoản: <span className="font-mono">{user}</span>
        </div>
      )}
      {password && (
        <div>
          Mật khẩu: <span className="font-mono">{password}</span>
        </div>
      )}
    </div>
  );
};

type SessionLogPanelProps = {
  session: VpsSession;
  query: ReturnType<typeof useSessionLog>;
  logText: string;
  onOpenFullLog: () => void;
};

const SessionLogPanel = ({ session, query, logText, onOpenFullLog }: SessionLogPanelProps) => {
  const hasLog = Boolean(session.has_log && session.worker_route);
  const autoRefresh = computeRefetchInterval(session);
  let content: ReactNode;

  if (!hasLog) {
    content = <p className="text-xs text-muted-foreground">Nhật ký chưa sẵn sàng.</p>;
  } else if (query.isLoading) {
    content = (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" />
        Đang tải nhật ký…
      </div>
    );
  } else if (query.isError) {
    const message =
      query.error instanceof ApiError
        ? query.error.message
        : query.error instanceof Error
          ? query.error.message
          : "Không thể tải nhật ký.";
    content = <p className="text-xs text-destructive">{message}</p>;
  } else {
    content = <pre className="text-xs font-mono whitespace-pre-wrap leading-relaxed">{logText || "(nhật ký trống)"}</pre>;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <p className="flex items-center gap-2 text-sm font-semibold">
          <Terminal className="w-4 h-4" />
          Nhật ký hoạt động
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={() => query.refetch()}
            disabled={!hasLog || query.isFetching}
          >
            {query.isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Làm mới
          </Button>
          <Button variant="ghost" size="sm" className="gap-2" onClick={onOpenFullLog} disabled={!hasLog}>
            <ExternalLink className="w-4 h-4" />
            Xem toàn bộ
          </Button>
        </div>
      </div>
      <ScrollArea className="h-[260px] rounded-md border border-border/40 bg-muted/20">
        <div className="p-4">{content}</div>
      </ScrollArea>
      <p className="text-[10px] text-muted-foreground">
        {autoRefresh ? `Tự động làm mới mỗi ${Math.round(autoRefresh / 1000)}s.` : "Đã tắt tự động làm mới."}
      </p>
    </div>
  );
};
