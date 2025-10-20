import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404: route not found ->", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/20">
      <div className="text-center px-6">
        <h1 className="mb-2 text-6xl font-extrabold tracking-tight">404</h1>
        <p className="mb-3 text-xl text-muted-foreground">Không tìm thấy trang</p>
        <p className="mb-6 text-sm text-muted-foreground">
          Liên kết bạn truy cập có thể đã bị đổi hoặc không còn tồn tại.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link
            to="/"
            className="rounded-lg bg-primary px-4 py-2 text-primary-foreground shadow hover:opacity-90"
          >
            Về trang chủ
          </Link>
          <Link
            to="/support"
            className="rounded-lg border px-4 py-2 text-foreground hover:bg-muted"
          >
            Cần hỗ trợ?
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
