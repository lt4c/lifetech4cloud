import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAdminLogs } from "@/lib/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

export default function AdminLogs() {
  const [limit, setLimit] = useState(500);
  const [query, setQuery] = useState("");
  const { data, isLoading, refetch, isFetching, error } = useQuery({
    queryKey: ["admin-logs", limit],
    queryFn: () => fetchAdminLogs(limit),
    staleTime: 5_000,
    retry: 1,
  });

  useEffect(() => {
    // auto refresh after changing limit
  }, [limit]);

  const items = data?.items ?? [];
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => JSON.stringify(item).toLowerCase().includes(q));
  }, [items, query]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Admin Logs</h1>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min={1}
            max={5000}
            value={limit}
            onChange={(e) => setLimit(Math.min(5000, Math.max(1, Number(e.target.value) || 1)))}
            className="w-28"
          />
          <Button onClick={() => refetch()} disabled={isFetching} className="gap-2">
            {isFetching ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Tải lại
          </Button>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Input
          placeholder="Tìm kiếm nội dung log..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Nhật ký hành động ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin mr-2" /> Đang tải logs...
            </div>
          ) : error ? (
            <div className="rounded border border-border/40 bg-destructive/10 p-3 text-sm">
              Không tải được logs. Vui lòng thử lại sau.
            </div>
          ) : (
            <pre className="max-h-[70vh] overflow-auto rounded-md border border-border/40 bg-background/60 p-3 text-xs">
{filtered.map((item, idx) => JSON.stringify(item, null, 2)).join("\n")}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


