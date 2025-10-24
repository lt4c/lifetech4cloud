import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Coins, Database, Globe, Server, Users, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  fetchAdminUsers,
  fetchHealthConfig,
  fetchStatusDb,
  fetchStatusDeps,
  fetchStatusHealth,
  fetchVpsSessions,
  fetchRewardMetrics,
  fetchWorkers,
} from "@/lib/api-client";
import type { AdminUsersResponse, HealthConfig, RewardMetricsSummary, StatusDb, StatusDeps, StatusHealth } from "@/lib/types";

const formatNumber = (value: number | null | undefined, digits = 1) => {
  if (value === null || value === undefined) return "--";
  return Number(value).toFixed(digits);
};

const formatMs = (value: number | null | undefined) => {
  if (value === null || value === undefined) return "--";
  return `${value.toFixed(1)} ms`;
};

export default function Analytics() {
  const { data: health } = useQuery<StatusHealth>({
    queryKey: ["admin-health"],
    queryFn: fetchStatusHealth,
    staleTime: 60_000,
  });

  const { data: deps } = useQuery<StatusDeps>({
    queryKey: ["admin-deps"],
    queryFn: fetchStatusDeps,
    staleTime: 60_000,
  });

  const { data: dbStatus } = useQuery<StatusDb>({
    queryKey: ["admin-db-status"],
    queryFn: fetchStatusDb,
    staleTime: 60_000,
  });

  const { data: users } = useQuery<AdminUsersResponse>({
    queryKey: ["admin-users", "analytics"],
    queryFn: () => fetchAdminUsers({ page_size: 1, page: 1 }),
    staleTime: 60_000,
  });

  const { data: rewardMetrics } = useQuery<RewardMetricsSummary>({
    queryKey: ["reward-metrics", "admin"],
    queryFn: fetchRewardMetrics,
    staleTime: 60_000,
  });

  const { data: workers = [] } = useQuery({
    queryKey: ["admin-workers", "analytics"],
    queryFn: fetchWorkers,
    staleTime: 10_000,
  });

  const { data: sessions = [] } = useQuery({
    queryKey: ["vps-sessions", "analytics"],
    queryFn: fetchVpsSessions,
    staleTime: 10_000,
  });

  const { data: healthConfig } = useQuery<HealthConfig>({
    queryKey: ["health-config"],
    queryFn: fetchHealthConfig,
    staleTime: 60_000,
  });

  const rewardSummary: RewardMetricsSummary = rewardMetrics ?? {
    prepareOk: 0,
    prepareRejected: 0,
    ssvSuccess: 0,
    ssvInvalid: 0,
    ssvDuplicate: 0,
    ssvError: 0,
    rewardCoins: 0,
    failureRatio: 0,
    effectiveDailyCap: 0,
  };

  const currentOrigin = typeof window !== "undefined" ? window.location.origin : "";

  const summaries = useMemo(() => {
    const activeSessions = sessions.filter((s) => s.status !== "deleted").length;
    const readySessions = sessions.filter((s) => s.status === "ready").length;
    const busyWorkers = workers.filter((w) => w.status === "busy").length;
    const idleWorkers = workers.filter((w) => w.status === "idle").length;
    return { activeSessions, readySessions, busyWorkers, idleWorkers };
  }, [sessions, workers]);

  const totalSsvAttempts =
    rewardSummary.ssvSuccess + rewardSummary.ssvInvalid + rewardSummary.ssvError + rewardSummary.ssvDuplicate;
  const fillRate = rewardSummary.prepareOk ? rewardSummary.ssvSuccess / rewardSummary.prepareOk : 0;
  const successRate = totalSsvAttempts ? rewardSummary.ssvSuccess / totalSsvAttempts : 0;
  const rpmUser = users?.total ? rewardSummary.rewardCoins / Math.max(users.total, 1) : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Phân tích vận hành</h1>
        <p className="text-muted-foreground">Số liệu thời gian thực lấy từ các endpoint trạng thái của LT4C.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[
          {
            label: "Trạng thái API",
            value: health?.api_up ? "Online" : "Offline",
            description: health?.version ? `Phiên bản ${health.version}` : "Theo dõi từ /status/health",
            icon: Activity,
          },
          {
            label: "Người dùng trong DB",
            value: users?.total?.toLocaleString() ?? "--",
            description: "Tổng từ /admin/users",
            icon: Users,
          },
          {
            label: "Phiên VPS đang hoạt động",
            value: summaries.activeSessions.toString(),
            description: `${summaries.readySessions} sẵn sàng`,
            icon: Server,
          },
          {
            label: "Workers",
            value: workers.length.toString(),
            description: `${summaries.busyWorkers} bận / ${summaries.idleWorkers} rảnh`,
            icon: Zap,
          },
          {
            label: "Rewarded Ads",
            value: rewardSummary.prepareOk ? `${rewardSummary.ssvSuccess}/${rewardSummary.prepareOk}` : "--",
            description: `Fill ${(fillRate * 100).toFixed(0)}% · SSV ${(successRate * 100).toFixed(0)}%`,
            icon: Coins,
          },
          {
            label: "CORS Origins",
            value: healthConfig?.allowed_origins?.length ? healthConfig.allowed_origins.length.toString() : "--",
            description: healthConfig?.allowed_origins?.[0]
              ? `Origin đầu tiên: ${healthConfig.allowed_origins[0]}`
              : "Từ /health/config",
            icon: Globe,
          },
        ].map((stat) => (
          <Card key={stat.label} className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
              <stat.icon className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Sức khỏe phụ thuộc (Dependencies)</CardTitle>
            <CardDescription>
              Dữ liệu từ <code className="font-mono text-xs">/api/v1/admin/status/deps</code>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full overflow-x-auto rounded-lg border border-border/40">
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Ping Postgres</TableCell>
                    <TableCell>{formatMs(deps?.db_ping_ms)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Ping Redis</TableCell>
                    <TableCell>{formatMs(deps?.redis_ping_ms)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Dung lượng đĩa trống</TableCell>
                    <TableCell>{deps?.disk_free_mb ? `${deps.disk_free_mb.toFixed(0)} MB` : "--"}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">CPU đang dùng</TableCell>
                    <TableCell>{formatNumber(deps?.cpu_percent)}%</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">RAM đang dùng</TableCell>
                    <TableCell>{formatNumber(deps?.memory_percent)}%</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Chẩn đoán CSDL</CardTitle>
            <CardDescription>
              Thông tin từ <code className="font-mono text-xs">/api/v1/admin/status/db</code>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="w-full overflow-x-auto rounded-lg border border-border/40">
              <Table>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Phiên bản</TableCell>
                    <TableCell>{dbStatus?.version ?? "không rõ"}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Kết nối đang hoạt động</TableCell>
                    <TableCell>{dbStatus?.active_connections ?? "--"}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Migration gần nhất</TableCell>
                    <TableCell>{dbStatus?.last_migration ?? "--"}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
            <div>
              <h3 className="text-sm font-semibold mb-2">Truy vấn chậm</h3>
              {dbStatus?.slow_queries?.length ? (
                <div className="space-y-2">
                  {dbStatus.slow_queries.map((entry) => (
                    <div key={entry.query} className="rounded-lg border border-border/40 p-3">
                      <code className="block text-xs break-all">{entry.query}</code>
                      <p className="text-xs text-muted-foreground mt-1">{entry.duration_ms.toFixed(2)} ms</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Không có truy vấn chậm nào được ghi nhận.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Rewarded Ads — Tổng quan</CardTitle>
          <CardDescription>Bộ đếm tổng hợp từ Prometheus</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2 text-sm">
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">SSV thành công</span>
              <span>
                {rewardSummary.ssvSuccess.toLocaleString()} / {totalSsvAttempts.toLocaleString()}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">Tỷ lệ fill</span>
              <span>{(fillRate * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">Tỷ lệ lỗi (30 phút)</span>
              <span>{(rewardSummary.failureRatio * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">Giới hạn/ngày hiệu dụng</span>
              <span>{rewardSummary.effectiveDailyCap}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">Tổng xu đã phát</span>
              <span>{rewardSummary.rewardCoins.toLocaleString()} xu</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <span className="font-medium">Xu/người dùng</span>
              <span>{rpmUser.toFixed(2)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Cấu hình CORS</CardTitle>
          <CardDescription>
            Dữ liệu runtime từ <code className="font-mono text-xs">/health/config</code>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold mb-2">Origin được phép</h3>
            {healthConfig?.allowed_origins?.length ? (
              <ul className="space-y-2">
                {healthConfig.allowed_origins.map((origin) => (
                  <li
                    key={origin}
                    className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2 text-sm"
                  >
                    <code className="break-all">{origin}</code>
                    {currentOrigin && origin === currentOrigin && (
                      <span className="ml-3 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
                        hiện tại
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">API không trả về danh sách origin.</p>
            )}
          </div>
          <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2 text-sm">
            <span className="font-medium">Kèm thông tin đăng nhập (credentials)</span>
            <span>{healthConfig?.allow_credentials ? "Bật" : "Tắt"}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
