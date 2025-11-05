import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Server, Zap, Shield, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BlurText, GlassBackground, GlassCard, MagneticButton } from "@/components/glass";
import { useAuth } from "@/context/AuthContext";
import { fetchVpsProducts } from "@/lib/api-client";
import type { VpsProduct } from "@/lib/types";

const marketingFeatures = [
  {
    icon: Server,
    title: "Tạo VPS trong vài giây",
    description: "Khởi tạo phiên Windows hoặc Linux thật, sẵn sàng dùng ngay.",
  },
  {
    icon: Zap,
    title: "Tự động hóa mọi thao tác",
    description: "Hệ thống tự cấp phát và kích hoạt máy, bạn chỉ việc bấm chọn.",
  },
  {
    icon: Shield,
    title: "Bảo mật tin cậy",
    description: "Quy trình đăng nhập và khởi chạy được bảo vệ nhiều lớp.",
  },
];

const formatCoins = (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 0 });

const getProductTagline = (product: VpsProduct): string => {
  if (product.description) {
    return product.description;
  }
  return "Tài nguyên VPS được quản lý bởi LT4C.";
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

const buildDiscordLoginUrl = (): string => {
  if (!API_BASE_URL) {
    return "/auth/discord/login";
  }
  return `${API_BASE_URL}/auth/discord/login`;
};

export default function Landing() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const { data: products = [], isLoading: loadingProducts } = useQuery({
    queryKey: ["vps-products"],
    queryFn: fetchVpsProducts,
    staleTime: 60_000,
  });

  const [primaryProduct] = products;
  const additionalProducts = useMemo(() => (primaryProduct ? products.slice(1) : products), [primaryProduct, products]);

  const goToDashboard = () => navigate("/dashboard");

  const handlePrimaryAction = () => {
    if (isAuthenticated) {
      goToDashboard();
    } else {
      window.location.href = buildDiscordLoginUrl();
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <GlassBackground className="pointer-events-none opacity-70" />
      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="sticky top-0 z-50 border-b border-white/10 bg-background/70 backdrop-blur-2xl">
          <div className="container mx-auto flex h-16 items-center justify-between px-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-accent to-secondary text-primary-foreground shadow-[var(--shadow-soft)]">
                <Server className="h-5 w-5" />
              </span>
              <span className="text-xl font-bold gradient-text">LifeTech4Code</span>
            </div>
            <nav className="hidden items-center gap-6 md:flex">
              <a
                href="#features"
                className="relative text-sm text-muted-foreground transition-all duration-200 hover:text-primary after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all after:duration-300 hover:after:w-full"
              >
                Tính năng
              </a>
              <a
                href="#pricing"
                className="relative text-sm text-muted-foreground transition-all duration-200 hover:text-primary after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all after:duration-300 hover:after:w-full"
              >
                Bảng giá
              </a>
              <a
                href="#about"
                className="relative text-sm text-muted-foreground transition-all duration-200 hover:text-primary after:absolute after:-bottom-1 after:left-0 after:h-px after:w-0 after:bg-primary after:transition-all after:duration-300 hover:after:w-full"
              >
                Giới thiệu
              </a>
            </nav>
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={handlePrimaryAction} className="hover-glow">
                {isAuthenticated ? "Bảng điều khiển" : "Đăng nhập"}
              </Button>
              <MagneticButton className="gap-2 px-6 py-2.5 text-sm font-semibold" onClick={handlePrimaryAction}>
                <span className="flex items-center gap-1">{isAuthenticated ? "Mở Console" : <><ArrowRight className="h-4 w-4" /> Bắt đầu</>}</span>
              </MagneticButton>
            </div>
          </div>
        </header>

        <section className="relative container mx-auto px-6 py-24 text-center md:py-32">
          <div className="pointer-events-none absolute inset-x-0 top-1/2 -z-10 h-64 max-w-4xl -translate-y-1/2 rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--primary)/0.2),transparent_70%)] blur-3xl" />
          <div className="relative mx-auto max-w-4xl space-y-8 animate-fade-in">
            <h1 className="text-5xl font-bold leading-tight tracking-tight md:text-7xl">
              Cloud VPS
              <span className="gradient-text"> cực đơn giản</span>
            </h1>
            <BlurText
              text="Khởi tạo VPS Windows thực, theo dõi tiến trình khởi chạy ngay trên bảng điều khiển. Trải nghiệm mượt, thao tác nhanh."
              className="mx-auto max-w-2xl text-xl leading-relaxed text-muted-foreground"
              animateBy="words"
              delay={120}
            />
            <div className="flex flex-col items-center justify-center gap-4 pt-6 sm:flex-row">
              <MagneticButton
                className="w-full gap-3 px-8 py-3 text-base font-semibold sm:w-auto"
                onClick={handlePrimaryAction}
              >
                <span className="flex items-center gap-1">{isAuthenticated ? "Vào bảng điều khiển" : <><ArrowRight className="h-5 w-5" /> Đăng nhập bằng Discord</>}</span>
              </MagneticButton>
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto"
                onClick={() => window.scrollTo({ top: window.innerHeight, behavior: "smooth" })}
              >
                Xem tính năng
              </Button>
            </div>
            <div className="flex flex-col gap-4 pt-8 text-sm text-muted-foreground md:flex-row md:flex-wrap md:items-center md:justify-center">
              {[
                "Đăng nhập Discord an toàn",
                "Hạ tầng ổn định, tốc độ cao",
                "Theo dõi trạng thái thời gian thực",
              ].map((item) => (
                <div
                  key={item}
                  className="glass-surface flex items-center gap-2 rounded-full px-4 py-2 shadow-[var(--shadow-soft)] transition-transform duration-300 ease-out hover:-translate-y-0.5"
                >
                  <Check className="h-4 w-4 text-success" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="features" className="container mx-auto px-6 py-24">
          <div className="mx-auto mb-16 max-w-3xl space-y-4 text-center">
            <h2 className="text-4xl font-bold">Vì sao chọn LT4C</h2>
            <p className="text-lg text-muted-foreground">Tất cả tính năng trên giao diện đều hoạt động thật, không phải demo.</p>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {marketingFeatures.map((feature) => (
              <GlassCard key={feature.title} variant="surface" className="group flex h-full flex-col gap-4 text-left">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-accent to-secondary text-primary-foreground shadow-[var(--shadow-soft)]">
                  <feature.icon className="h-6 w-6" />
                </span>
                <h3 className="text-xl font-semibold">{feature.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
              </GlassCard>
            ))}
          </div>
        </section>

        <section id="pricing" className="container mx-auto px-6 py-24">
          <div className="mx-auto mb-16 max-w-3xl space-y-4 text-center">
            <h2 className="text-4xl font-bold">Danh mục gói VPS</h2>
            <p className="text-lg text-muted-foreground">Danh sách gói được cập nhật theo thời gian thực.</p>
          </div>
          <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3">
            {loadingProducts && (
              <GlassCard variant="surface" hover={false} className="md:col-span-3 text-center">
                <div className="space-y-2">
                  <h3 className="text-2xl font-semibold">Đang tải gói VPS...</h3>
                  <p className="text-sm text-muted-foreground">Đang lấy dữ liệu mới nhất.</p>
                </div>
              </GlassCard>
            )}

            {!loadingProducts && products.length === 0 && (
              <GlassCard variant="surface" hover={false} className="md:col-span-3 text-center">
                <div className="space-y-2">
                  <h3 className="text-2xl font-semibold">Chưa có gói khả dụng</h3>
                  <p className="text-sm text-muted-foreground">
                    Vui lòng quay lại sau hoặc liên hệ hỗ trợ để biết thêm thông tin.
                  </p>
                </div>
              </GlassCard>
            )}

            {!loadingProducts && primaryProduct && (
              <PricingCard product={primaryProduct} highlight onAction={handlePrimaryAction} />
            )}

            {additionalProducts.map((product) => (
              <PricingCard key={product.id} product={product} onAction={handlePrimaryAction} />
            ))}
          </div>
        </section>

        <section id="about" className="container mx-auto px-6 py-24">
          <GlassCard variant="surface" hover={false} className="mx-auto max-w-4xl space-y-6 text-center">
            <h2 className="text-3xl font-bold">Thiết kế để vận hành thực tế</h2>
            <p className="text-lg text-muted-foreground">
              Giao diện hiện đại kết nối trực tiếp với hệ thống LT4C. Phiên làm việc, hỗ trợ, vai trò quản trị đều được
              lưu trữ an toàn và quản lý tập trung.
            </p>
          </GlassCard>
        </section>

        <footer className="mt-24 border-t border-white/10 bg-background/60 backdrop-blur-xl">
          <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-6 py-12 md:flex-row">
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-accent to-secondary text-primary-foreground shadow-[var(--shadow-soft)]">
                <Server className="h-5 w-5" />
              </span>
              <span className="font-bold gradient-text">LifeTech4Code</span>
            </div>
            <p className="text-sm text-muted-foreground">
              (c) {new Date().getFullYear()} LifeTech4Code. Mọi quyền được bảo lưu.
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
}

const PricingCard = ({
  product,
  highlight = false,
  onAction,
}: {
  product: VpsProduct;
  highlight?: boolean;
  onAction: () => void;
}) => (
  <GlassCard
    variant={highlight ? "liquid" : "default"}
    glow={highlight}
    className={`relative flex h-full flex-col justify-between ${highlight ? "md:col-span-2 lg:col-span-1 ring-2 ring-primary/60" : ""}`}
  >
    {highlight && (
      <div className="absolute -top-4 left-1/2 -translate-x-1/2">
        <span className="border-gradient glass-surface inline-flex items-center rounded-full px-4 py-1 text-sm font-medium text-primary-foreground">
          Nổi bật
        </span>
      </div>
    )}
    <div className="space-y-4 text-center">
      <h3 className="text-2xl capitalize">{product.name}</h3>
      <div className="mt-4">
        <span className="text-4xl font-bold text-warning">{formatCoins(product.price_coins)}</span>
        <span className="ml-2 text-muted-foreground">coin</span>
      </div>
      <p className="text-sm text-muted-foreground">{getProductTagline(product)}</p>
    </div>
    <Button className="w-full" variant={highlight ? "default" : "outline"} onClick={onAction}>
      {highlight ? "Khởi chạy trong bảng điều khiển" : "Đăng nhập để khởi chạy"}
    </Button>
  </GlassCard>
);