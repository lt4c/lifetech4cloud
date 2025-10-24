import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/sonner";
import {
  createAdminVpsProduct,
  deactivateAdminVpsProduct,
  deleteAdminVpsProduct,
  fetchAdminVpsProducts,
  fetchWorkers,
  updateAdminVpsProduct,
} from "@/lib/api-client";
import type { VpsProduct, WorkerInfo } from "@/lib/types";
import { Archive, Loader2, Pencil, PlusCircle, Power, Trash2 } from "lucide-react";
import { Slab } from "react-loading-indicators";

type ProductFormState = {
  name: string;
  description: string;
  price_coins: string;
  provision_action: string;
  is_active: boolean;
  worker_ids: string[];
};

const emptyForm: ProductFormState = {
  name: "",
  description: "",
  price_coins: "0",
  provision_action: "1",
  is_active: true,
  worker_ids: [],
};

const parseNonNegativeInt = (value: string): number | null => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return null;
  }
  return Math.round(parsed);
};

const parsePositiveInt = (value: string): number | null => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return null;
  }
  return Math.floor(parsed);
};

const productStatus = (product: VpsProduct) =>
  product.is_active ? (
    <Badge variant="default">Đang hoạt động</Badge>
  ) : (
    <Badge variant="outline" className="text-muted-foreground">
      Đã lưu trữ
    </Badge>
  );

const workerBadge = (worker: WorkerInfo) => (
  <Badge key={worker.id} variant="outline" className="capitalize">
    {worker.name || worker.base_url} · {worker.active_sessions}/{worker.max_sessions}
  </Badge>
);

export default function AdminVpsProducts() {
  const queryClient = useQueryClient();
  const [showInactive, setShowInactive] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<VpsProduct | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<VpsProduct | null>(null);

  const [createForm, setCreateForm] = useState<ProductFormState>(emptyForm);
  const [editForm, setEditForm] = useState<ProductFormState>(emptyForm);

  const productsQuery = useQuery({
    queryKey: ["admin-vps-products", showInactive ? "all" : "active"],
    queryFn: () => fetchAdminVpsProducts({ includeInactive: showInactive }),
    keepPreviousData: true,
  });

  const { data: workerOptions = [], isLoading: workersLoading } = useQuery<WorkerInfo[]>({
    queryKey: ["admin-workers", "options"],
    queryFn: fetchWorkers,
    staleTime: 60_000,
  });

  const products = useMemo(() => productsQuery.data ?? [], [productsQuery.data]);

  useEffect(() => {
    if (!createOpen) {
      setCreateForm(emptyForm);
      setCreateError(null);
    }
  }, [createOpen]);

  useEffect(() => {
    if (!editOpen) {
      setEditTarget(null);
      setEditForm(emptyForm);
      setEditError(null);
      return;
    }
    if (editTarget) {
      setEditForm({
        name: editTarget.name ?? "",
        description: editTarget.description ?? "",
        price_coins: String(editTarget.price_coins ?? 0),
        provision_action: String(editTarget.provision_action ?? 1),
        is_active: Boolean(editTarget.is_active),
        worker_ids: (editTarget.workers ?? []).map((worker) => worker.id),
      });
    }
  }, [editOpen, editTarget]);

  const invalidateProducts = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-vps-products"] });
  };

  const createMutation = useMutation({
    mutationFn: async (formState: ProductFormState) => {
      const price = parseNonNegativeInt(formState.price_coins);
      if (price === null) {
        throw new Error("Giá phải là số không âm.");
      }
      const action = parsePositiveInt(formState.provision_action);
      if (action === null) {
        throw new Error("Hành động cấp phát phải là số nguyên dương.");
      }
      return createAdminVpsProduct({
        name: formState.name.trim(),
        description: formState.description.trim() || null,
        price_coins: price,
        provision_action: action,
        is_active: formState.is_active,
        worker_ids: formState.worker_ids,
      });
    },
    onSuccess: () => {
      toast("Đã tạo sản phẩm.");
      invalidateProducts();
      setCreateOpen(false);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Tạo sản phẩm thất bại.";
      setCreateError(message);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, formState, original }: { id: string; formState: ProductFormState; original: VpsProduct }) => {
      const payload: Record<string, unknown> = {};
      if (formState.name.trim() !== (original.name ?? "")) {
        payload.name = formState.name.trim();
      }
      if (formState.description.trim() !== (original.description ?? "")) {
        payload.description = formState.description.trim() || null;
      }
      const price = parseNonNegativeInt(formState.price_coins);
      if (price === null) {
        throw new Error("Giá phải là số không âm.");
      }
      if (price !== original.price_coins) {
        payload.price_coins = price;
      }
      const action = parsePositiveInt(formState.provision_action);
      if (action === null) {
        throw new Error("Hành động cấp phát phải là số nguyên dương.");
      }
      if (action !== (original.provision_action ?? 1)) {
        payload.provision_action = action;
      }
      if (formState.is_active !== Boolean(original.is_active)) {
        payload.is_active = formState.is_active;
      }
      const currentIds = new Set((original.workers ?? []).map((worker) => worker.id));
      const desiredIds = new Set(formState.worker_ids);
      const sameSize = currentIds.size === desiredIds.size;
      let workersChanged = !sameSize;
      if (sameSize) {
        for (const id of currentIds) {
          if (!desiredIds.has(id)) {
            workersChanged = true;
            break;
          }
        }
      }
      if (workersChanged) {
        payload.worker_ids = Array.from(desiredIds);
      }
      if (Object.keys(payload).length === 0) {
        return original;
      }
      return updateAdminVpsProduct(id, payload);
    },
    onSuccess: () => {
      toast("Đã cập nhật sản phẩm.");
      invalidateProducts();
      setEditOpen(false);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Cập nhật sản phẩm thất bại.";
      setEditError(message);
    },
  });

  const statusMutation = useMutation({
    mutationFn: async (product: VpsProduct) => {
      if (product.is_active) {
        return deactivateAdminVpsProduct(product.id);
      }
      return updateAdminVpsProduct(product.id, { is_active: true });
    },
    onSuccess: () => {
      invalidateProducts();
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Cập nhật trạng thái sản phẩm thất bại.";
      toast(message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (productId: string) => deleteAdminVpsProduct(productId),
    onSuccess: () => {
      toast("Đã xóa sản phẩm.");
      invalidateProducts();
      setDeleteTarget(null);
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Xóa sản phẩm thất bại.";
      toast(message);
    },
    onSettled: () => {
      setDeleteTarget(null);
    },
  });

  const handleCreateSubmit = () => {
    setCreateError(null);
    createMutation.mutate(createForm);
  };

  const handleEditSubmit = () => {
    if (!editTarget) return;
    setEditError(null);
    updateMutation.mutate({ id: editTarget.id, formState: editForm, original: editTarget });
  };

  const toggleCreateWorker = (workerId: string) => {
    setCreateForm((prev) => {
      const exists = prev.worker_ids.includes(workerId);
      return {
        ...prev,
        worker_ids: exists ? prev.worker_ids.filter((id) => id !== workerId) : [...prev.worker_ids, workerId],
      };
    });
  };

  const toggleEditWorker = (workerId: string) => {
    setEditForm((prev) => {
      const exists = prev.worker_ids.includes(workerId);
      return {
        ...prev,
        worker_ids: exists ? prev.worker_ids.filter((id) => id !== workerId) : [...prev.worker_ids, workerId],
      };
    });
  };

  const busy =
    productsQuery.isLoading ||
    createMutation.isLoading ||
    updateMutation.isLoading ||
    statusMutation.isLoading ||
    deleteMutation.isLoading;

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Sản phẩm VPS</h1>
          <p className="text-muted-foreground">
            Quản lý các gói hiển thị tại <code className="font-mono text-xs">/vps/products</code>.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2">
            <Switch
              checked={showInactive}
              onCheckedChange={(value) => setShowInactive(Boolean(value))}
              aria-label="Hiện sản phẩm đã lưu trữ"
            />
            <span className="text-sm text-muted-foreground">Hiện sản phẩm đã lưu trữ</span>
          </div>
          <Button className="gap-2" onClick={() => setCreateOpen(true)}>
            <PlusCircle className="h-4 w-4" />
            Sản phẩm mới
          </Button>
        </div>
      </div>

      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Danh mục</CardTitle>
          <CardDescription>Tùy theo bộ lọc sẽ gồm sản phẩm đang hoạt động và đã lưu trữ. Giá được lưu bằng đơn vị xu.</CardDescription>
        </CardHeader>
        <CardContent>
          {productsQuery.isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Slab color="#d18d00" size="large" text="Đang tải nội dung từ server" textColor="" />
            </div>
          ) : products.length === 0 ? (
            <p className="text-sm text-muted-foreground">Chưa có sản phẩm nào. Hãy tạo sản phẩm đầu tiên.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tên</TableHead>
                  <TableHead>Mô tả</TableHead>
                  <TableHead className="w-24">Giá</TableHead>
                  <TableHead className="w-28">Hành động cấp phát</TableHead>
                  <TableHead className="w-48">Worker</TableHead>
                  <TableHead className="w-32">Trạng thái</TableHead>
                  <TableHead className="w-48">Cập nhật</TableHead>
                  <TableHead className="w-40 text-right">Thao tác</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id} className={!product.is_active ? "opacity-70" : undefined}>
                    <TableCell className="font-medium">{product.name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground whitespace-pre-wrap">
                      {product.description || "—"}
                    </TableCell>
                    <TableCell>{product.price_coins.toLocaleString()}</TableCell>
                    <TableCell>{product.provision_action ?? 1}</TableCell>
                    <TableCell className="space-x-1 space-y-1">
                      {product.workers && product.workers.length > 0
                        ? product.workers.map((worker) => workerBadge(worker))
                        : <span className="text-xs text-muted-foreground">Không</span>}
                    </TableCell>
                    <TableCell>{productStatus(product)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {product.updated_at
                        ? formatDistanceToNow(new Date(product.updated_at), { addSuffix: true })
                        : "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditTarget(product);
                            setEditOpen(true);
                          }}
                        >
                          <Pencil className="mr-2 h-4 w-4" />
                          Sửa
                        </Button>
                        <Button
                          variant={product.is_active ? "destructive" : "secondary"}
                          size="sm"
                          onClick={() => statusMutation.mutate(product)}
                          disabled={statusMutation.isLoading}
                        >
                          {product.is_active ? (
                            <>
                              <Archive className="mr-2 h-4 w-4" />
                              Lưu trữ
                            </>
                          ) : (
                            <>
                              <Power className="mr-2 h-4 w-4" />
                              Kích hoạt
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive hover:text-destructive border-destructive/40"
                          onClick={() => setDeleteTarget(product)}
                          disabled={deleteMutation.isLoading}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Xóa
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg glass-card">
          <DialogHeader>
            <DialogTitle>Tạo sản phẩm VPS</DialogTitle>
            <DialogDescription>Thiết lập giá và trạng thái cho sản phẩm mới.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="create-name">Tên</Label>
              <Input
                id="create-name"
                value={createForm.name}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Premium VPS"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-description">Mô tả</Label>
              <Textarea
                id="create-description"
                value={createForm.description}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, description: event.target.value }))}
                placeholder="Mô tả tài nguyên bao gồm..."
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-price">Giá (xu)</Label>
              <Input
                id="create-price"
                type="number"
                min={0}
                value={createForm.price_coins}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, price_coins: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="create-action">Hành động cấp phát</Label>
              <Input
                id="create-action"
                type="number"
                min={1}
                value={createForm.provision_action}
                onChange={(event) => setCreateForm((prev) => ({ ...prev, provision_action: event.target.value }))}
              />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <div>
                <Label htmlFor="create-active" className="text-sm font-medium">
                  Kích hoạt
                </Label>
                <p className="text-xs text-muted-foreground">Sản phẩm không kích hoạt sẽ ẩn với người dùng.</p>
              </div>
              <Switch
                id="create-active"
                checked={createForm.is_active}
                onCheckedChange={(value) => setCreateForm((prev) => ({ ...prev, is_active: Boolean(value) }))}
              />
            </div>
            <div className="grid gap-2">
              <Label>Worker</Label>
              <div className="max-h-48 overflow-auto rounded-lg border border-border/40 p-3 space-y-2">
                {workersLoading ? (
                  <p className="text-xs text-muted-foreground">Đang tải danh sách worker...</p>
                ) : workerOptions.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Chưa có worker nào được đăng ký.</p>
                ) : (
                  workerOptions.map((worker) => (
                    <label key={worker.id} className="flex items-center gap-2 text-sm">
                      <Checkbox
                        checked={createForm.worker_ids.includes(worker.id)}
                        onCheckedChange={() => toggleCreateWorker(worker.id)}
                      />
                      <span className="font-medium">{worker.name || worker.base_url}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
            {createError && <p className="text-sm text-destructive">{createError}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)} disabled={createMutation.isLoading}>
              Hủy
            </Button>
            <Button onClick={handleCreateSubmit} disabled={createMutation.isLoading}>
              {createMutation.isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Tạo mới"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-lg glass-card">
          <DialogHeader>
            <DialogTitle>Sửa sản phẩm VPS</DialogTitle>
            <DialogDescription>Cập nhật thông tin hoặc trạng thái cho {editTarget?.name ?? "sản phẩm"}.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="edit-name">Tên</Label>
              <Input
                id="edit-name"
                value={editForm.name}
                onChange={(event) => setEditForm((prev) => ({ ...prev, name: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-description">Mô tả</Label>
              <Textarea
                id="edit-description"
                value={editForm.description}
                onChange={(event) => setEditForm((prev) => ({ ...prev, description: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-price">Giá (xu)</Label>
              <Input
                id="edit-price"
                type="number"
                min={0}
                value={editForm.price_coins}
                onChange={(event) => setEditForm((prev) => ({ ...prev, price_coins: event.target.value }))}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-action">Hành động cấp phát</Label>
              <Input
                id="edit-action"
                type="number"
                min={1}
                value={editForm.provision_action}
                onChange={(event) => setEditForm((prev) => ({ ...prev, provision_action: event.target.value }))}
              />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/40 px-3 py-2">
              <div>
                <Label htmlFor="edit-active" className="text-sm font-medium">
                  Kích hoạt
                </Label>
                <p className="text-xs text-muted-foreground">Sản phẩm không kích hoạt sẽ ẩn với người dùng.</p>
              </div>
              <Switch
                id="edit-active"
                checked={editForm.is_active}
                onCheckedChange={(value) => setEditForm((prev) => ({ ...prev, is_active: Boolean(value) }))}
              />
            </div>
            <div className="grid gap-2">
              <Label>Worker</Label>
              <div className="max-h-48 overflow-auto rounded-lg border border-border/40 p-3 space-y-2">
                {workersLoading ? (
                  <p className="text-xs text-muted-foreground">Đang tải danh sách worker...</p>
                ) : workerOptions.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Chưa có worker nào được đăng ký.</p>
                ) : (
                  workerOptions.map((worker) => (
                    <label key={worker.id} className="flex items-center gap-2 text-sm">
                      <Checkbox
                        checked={editForm.worker_ids.includes(worker.id)}
                        onCheckedChange={() => toggleEditWorker(worker.id)}
                      />
                      <span className="font-medium">{worker.name || worker.base_url}</span>
                    </label>
                  ))
                )}
              </div>
            </div>
            {editError && <p className="text-sm text-destructive">{editError}</p>}
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setEditOpen(false)} disabled={updateMutation.isLoading}>
              Hủy
            </Button>
            <Button onClick={handleEditSubmit} disabled={updateMutation.isLoading || !editTarget}>
              {updateMutation.isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Lưu thay đổi"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open && !deleteMutation.isLoading) {
            setDeleteTarget(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xóa sản phẩm</AlertDialogTitle>
            <AlertDialogDescription>
              Xóa vĩnh viễn {deleteTarget?.name ?? "sản phẩm này"} khỏi danh mục. Thao tác không thể hoàn tác.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isLoading}>Hủy</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
              disabled={deleteMutation.isLoading}
            >
              {deleteMutation.isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Xóa
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {busy && <div className="sr-only">Processing...</div>}
    </div>
  );
}
