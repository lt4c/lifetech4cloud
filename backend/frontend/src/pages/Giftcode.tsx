import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Gift } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";
import { redeemGiftCode, ApiError } from "@/lib/api-client";

type GiftResult = {
  title: string;
  added: number;
  balance: number;
  remaining: number;
};

const Giftcode = () => {
  const queryClient = useQueryClient();
  const [giftCodeInput, setGiftCodeInput] = useState("");
  const [giftMessage, setGiftMessage] = useState<string | null>(null);
  const [giftResult, setGiftResult] = useState<GiftResult | null>(null);

  const redeemMutation = useMutation({
    mutationFn: redeemGiftCode,
    onSuccess: (data) => {
      setGiftResult({
        title: data.gift_title,
        added: data.added,
        balance: data.balance,
        remaining: data.remaining,
      });
      setGiftMessage(
        `Doi ma thanh cong ${data.gift_title}. Ban nhan +${data.added.toLocaleString()} xu, so du hien tai: ${data.balance.toLocaleString()} xu.`,
      );
      setGiftCodeInput("");
      queryClient.invalidateQueries({ queryKey: ["wallet-balance"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    onError: (error) => {
      let detail = "Khong the doi ma. Vui long kiem tra va thu lai.";
      if (error instanceof ApiError) {
        const raw = (error.data as { detail?: string } | undefined)?.detail;
        if (typeof raw === "string") {
          detail = raw;
        }
      } else if (error instanceof Error) {
        detail = error.message;
      }
      setGiftResult(null);
      setGiftMessage(detail);
      toast(detail);
    },
  });

  const handleRedeem = () => {
    const trimmed = giftCodeInput.trim().toUpperCase();
    if (!trimmed) {
      setGiftResult(null);
      setGiftMessage("Vui long nhap ma qua hop le.");
      return;
    }
    setGiftMessage(null);
    redeemMutation.mutate({ code: trimmed });
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Card className="glass-card">
        <CardHeader>
          <CardTitle>Giftcode</CardTitle>
          <CardDescription>
            Nhap ma qua de nhan xu thuong (moi tai khoan chi doi mot lan).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              placeholder="Nhap ma qua..."
              value={giftCodeInput}
              onChange={(event) => setGiftCodeInput(event.target.value)}
              className="sm:flex-1"
            />
            <Button
              onClick={handleRedeem}
              disabled={redeemMutation.isLoading}
              className="gap-2"
            >
              {redeemMutation.isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Gift className="h-4 w-4" />
              )}
              Doi ma
            </Button>
          </div>
          {giftResult && (
            <p className="text-xs text-muted-foreground">
              Ma {giftResult.title} con lai{" "}
              {giftResult.remaining.toLocaleString()} luot.
            </p>
          )}
          {giftMessage && (
            <p
              className={cn(
                "text-sm",
                giftResult ? "text-emerald-600" : "text-destructive",
              )}
            >
              {giftMessage}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Giftcode;

