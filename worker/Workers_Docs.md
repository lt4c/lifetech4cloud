
# 🧠 **Worker Server API Documentation**

**Port mặc định:** `4000`
**Công nghệ:** Node.js (Express + Puppeteer + Cloudflared Tunnel)

---

## ⚙️ Tổng quan hoạt động

Server này có nhiệm vụ:

1. **Đăng nhập NVIDIA DLI** để lấy `sessionid` token.
2. **Lưu token** vào file `worker-tokens.json` để dùng tạo VM.
3. **Tạo VM** (Linux / Windows / Dummy) qua script tương ứng (`linux.js`, `win10.js`, `2z2.js`).
4. **Nhận SSH link** qua Cloudflare tunnel (cổng 3001).
5. **Theo dõi log VM** qua `/log/:route`.
6. **Dừng VM** và gửi request “end_task” tới NVIDIA.
7. **Tự dọn token** hết slot mỗi 20 phút.

---

## 🔑 **1. POST `/yud-ranyisi`**

### 🧭 Mục đích:

Đăng nhập NVIDIA Learn để lấy token (`sessionid`) hợp lệ và lưu vào `worker-tokens.json`.

### 🧰 Body (JSON):

```json
{
  "email": "user@example.com",
  "password": "12345678"
}
```

### 🧠 Cách hoạt động:

* Puppeteer mở trình duyệt thật đến trang [https://learn.learn.nvidia.com/login](https://learn.learn.nvidia.com/login)
* Tự nhập email + password
* Sau khi đăng nhập thành công → lấy cookie `sessionid`
* Ghi token vào file `worker-tokens.json` dạng:

```json
{
  "abcd1234sessionidtoken": {
    "slot": 3,
    "inuse": false
  }
}
```

### ✅ Response:

* **200 (OK)** → đăng nhập thành công:

```json
true
```

* **401 (Unauthorized)** → sai mật khẩu hoặc không lấy được cookie:

```json
{
  "error": "Authentication failed - no session cookie"
}
```

* **400 (Bad Request)** → thiếu email/password:

```json
{
  "error": "Email and password required"
}
```

### 💡 Curl ví dụ:

```bash
curl -X POST http://localhost:4000/yud-ranyisi \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"123456"}'
```

---

## 💻 **2. POST `/vm-loso`**

### 🧭 Mục đích:

Khởi tạo 1 VM mới bằng token có sẵn (Linux/Windows/2z2).

### 🧰 Body (JSON):

```json
{
  "action": 1
}
```

### 🔢 Action Mapping:

| Action | Script chạy | Mô tả             |
| ------ | ----------- | ----------------- |
| 1      | `linux.js`  | Tạo VM Linux      |
| 2      | `win10.js`  | Tạo VM Windows 10 |
| 3      | `2z2.js`    | Dummy hoặc test   |

### 🧠 Cách hoạt động:

1. Đọc file `worker-tokens.json`.
2. Tìm token có `slot >= 1` và `inuse = false`.
3. Giảm `slot` đi 1 và set `inuse = true`.
4. Sinh route ngẫu nhiên: `quack_xxxxx`.
5. Chạy `node <script> <token> <route> <tunnelUrl>` bằng child_process.
6. Trả về log URL.

### ✅ Response:

* **200 (OK)**:

```json
{
  "logUrl": "/log/quack_ab123"
}
```

* **400 (Invalid action)**:

```json
{
  "error": "Invalid action. Must be 1, 2, or 3"
}
```

* **400 (No token)**:

```json
{
  "error": "No available tokens"
}
```

* **500 (Token file lỗi)**:

```json
{
  "error": "Invalid worker token file"
}
```

### 💡 Curl ví dụ:

```bash
curl -X POST http://localhost:4000/vm-loso \
     -H "Content-Type: application/json" \
     -d '{"action":2}'
```

---

## 📜 **3. GET `/log/:route`**

### 🧭 Mục đích:

Xem log (stdout) của VM đang chạy hoặc đã dừng.

### 🧰 URL Param:

* `:route` = route đã trả về khi tạo VM (ví dụ `quack_xd5hj`)

### ✅ Response:

* **200 (OK)** → nội dung log, tự động thêm `<br>` giữa các dòng.
* **404 (Not Found)** → không tồn tại file log.

### 💡 Curl ví dụ:

```bash
curl http://localhost:4000/log/quack_xd5hj
```

---

## 🛑 **4. POST `/stop/:route`**

### 🧭 Mục đích:

Dừng một VM đang chạy và gửi yêu cầu “end_task” về NVIDIA.

### 🧰 URL Param:

* `:route` = route của VM cần dừng.

### 🧠 Cách hoạt động:

1. Tìm token đang được `inuse: true` trong `worker-tokens.json`.
2. Gửi `POST` đến endpoint NVIDIA:

   ```
   https://learn.learn.nvidia.com/.../handler/end_task
   ```
3. Dùng PowerShell kill process Node có route tương ứng.
4. Đặt `inuse = false` trong token.
5. Ghi log “VM STOPPED” vào file `route.txt`.

### ✅ Response:

```json
{
  "success": true,
  "message": "VM stopped successfully for route quack_xd5hj",
  "tokenReset": "abcd1234sessionidtoken"
}
```

### 💡 Curl ví dụ:

```bash
curl -X POST http://localhost:4000/stop/quack_xd5hj
```

---

## ☁️ **5. Cloudflare Tunnel (tự động)**

### 🧭 Mục đích:

Tạo public tunnel để nhận SSHx link từ script (qua `POST /sshx`).

### ⚙️ Hoạt động:

* Khi server start → gọi `setupCloudflareTunnel()`
* Nếu chưa có `cloudflared` → tự tải.
* Chạy tunnel cho `localhost:3001`
* Lấy URL như:
  `https://randomstring.trycloudflare.com`

### 🧰 Endpoint nội bộ:

`POST /sshx` (chạy trên port `3001`, không phải `4000`)

#### Body (JSON):

```json
{
  "sshx": "https://sshx.io/abcdef",
  "route": "quack_xd5hj"
}
```

#### ✅ Response:

```json
{ "success": true }
```

Khi nhận → server sẽ append link vào file `quack_xd5hj.txt`.
Cái này ko cần backend post chỉ xài để lab gửi link sshx về cho ta

---

## ♻️ **6. Token cleanup (tự động mỗi 20 phút)**

### 🧭 Mục đích:

Xóa token đã hết `slot` khỏi file `worker-tokens.json`.

### ⚙️ Cách hoạt động:

* Mỗi 20 phút, server quét file:

  * Nếu `slot === 0` → xóa token đó.
* Log ra console:

  ```
  Worker server: Cleaned up 2 expired tokens
  ```

---

## 📁 **Cấu trúc dữ liệu token (`worker-tokens.json`):**

```json
{
  "abcd1234token": {
    "slot": 2,
    "inuse": true
  },
  "efgh5678token": {
    "slot": 3,
    "inuse": false
  }
}
```

| Thuộc tính | Ý nghĩa                                 |
| ---------- | --------------------------------------- |
| `slot`     | Số lần còn có thể tạo VM bằng token này |
| `inuse`    | `true` = đang dùng, `false` = sẵn sàng  |

---

## 🚀 Khởi động server:

```bash
node worker-server.js
```

**Console log:**

```
Worker server running on port 4000
Endpoints:
  POST /yud-ranyisi - Login and add worker token
  POST /vm-loso - Create VM (1=linux, 2=windows, 3=trash)
  POST /stop/:route - Stop VM by route
  GET /log/:route - Get VM logs
```

