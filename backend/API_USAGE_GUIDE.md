# API Usage Guide - Worker System

## Admin: Quản lý Coins của User

### Cập nhật coins cho user

**Endpoint:** `PATCH /admin/users/{user_id}/coins`

**Headers:**
```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Body:**
```json
{
  "op": "add",      // "add", "sub", hoặc "set"
  "amount": 1000,   // Số lượng coin (phải > 0)
  "reason": "Nạp tiền cho user"  // Lý do (optional)
}
```

**Ví dụ:**

1. **Thêm coins:**
```bash
curl -X PATCH http://localhost:8000/admin/users/{user_id}/coins \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"op":"add","amount":500,"reason":"Bonus"}'
```

2. **Trừ coins:**
```bash
curl -X PATCH http://localhost:8000/admin/users/{user_id}/coins \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"op":"sub","amount":100,"reason":"Penalty"}'
```

3. **Set coins (đặt số lượng cụ thể):**
```bash
curl -X PATCH http://localhost:8000/admin/users/{user_id}/coins \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"op":"set","amount":1000,"reason":"Reset balance"}'
```

## Admin: Quản lý Workers

### 1. Đăng ký Worker mới

**Endpoint:** `POST /admin/workers/register`

**Body:**
```json
{
  "name": "Worker 1",              // Tên gợi nhớ (optional)
  "base_url": "http://192.168.1.100:4000",  // URL của worker
  "max_sessions": 3                // Số session tối đa (default: 3)
}
```

**Ví dụ:**
```bash
curl -X POST http://localhost:8000/admin/workers/register \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Worker Main","base_url":"http://example.com:4000","max_sessions":5}'
```

**Lưu ý:**
- Chỉ cần cung cấp base URL (VD: http://example.com:4000)
- Backend tự động ghép các endpoint:
  - `/vm-loso` - Tạo VM
  - `/log/:route` - Xem log
  - `/stop/:route` - Dừng VM

### 2. Liệt kê Workers

**Endpoint:** `GET /admin/workers`

```bash
curl http://localhost:8000/admin/workers \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Worker 1",
    "base_url": "http://192.168.1.100:4000",
    "status": "active",
    "max_sessions": 3,
    "active_sessions": 1,  // Số session đang chạy
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### 3. Cập nhật Worker

**Endpoint:** `PATCH /admin/workers/{worker_id}`

**Body:**
```json
{
  "name": "Worker Updated",
  "base_url": "http://new-url:4000",
  "status": "active",        // "active" hoặc "disabled"
  "max_sessions": 5
}
```

### 4. Vô hiệu hóa Worker

**Endpoint:** `POST /admin/workers/{worker_id}/disable`

```bash
curl -X POST http://localhost:8000/admin/workers/{worker_id}/disable \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Admin: Quản lý VPS Products

### 1. Tạo VPS Product mới

**Endpoint:** `POST /admin/vps-products`

**Body:**
```json
{
  "name": "Windows VPS",
  "description": "Windows 10 VPS",
  "price_coins": 100,
  "provision_action": 2,     // 1=Linux, 2=Windows, 3=Test
  "is_active": true,
  "worker_ids": [            // Danh sách worker IDs
    "worker-uuid-1",
    "worker-uuid-2"
  ]
}
```

**Lưu ý:**
- Có thể gán nhiều workers cho 1 product
- Khi user tạo VPS, hệ thống sẽ chọn worker có ít session nhất

### 2. Cập nhật VPS Product

**Endpoint:** `PATCH /admin/vps-products/{product_id}`

**Body:** (Tất cả fields đều optional)
```json
{
  "name": "Updated name",
  "price_coins": 150,
  "worker_ids": ["new-worker-uuid"]
}
```

## User: Sử dụng VPS

### 1. Xem danh sách VPS Products

**Endpoint:** `GET /vps/products`

```bash
curl http://localhost:8000/vps/products
```

### 2. Tạo VPS mới

**Endpoint:** `POST /vps/purchase-and-create`

**Headers:**
```
Authorization: Bearer <user_token>
Idempotency-Key: unique-key-123
Content-Type: application/json
```

**Body:**
```json
{
  "product_id": "product-uuid"
}
```

**Flow:**
1. Hệ thống kiểm tra user có đủ coins
2. Trừ coins từ tài khoản user
3. Chọn worker có ít session nhất
4. Gọi API worker để tạo VM (server-side)
5. Lưu thông tin session và route
6. Trả về thông tin session

### 3. Xem danh sách VPS của user

**Endpoint:** `GET /vps/sessions`

```bash
curl http://localhost:8000/vps/sessions \
  -H "Authorization: Bearer USER_TOKEN"
```

### 4. Xem log VPS (bao gồm thông tin RDP)

**Endpoint:** `GET /vps/sessions/{session_id}/log`

```bash
curl http://localhost:8000/vps/sessions/{session_id}/log \
  -H "Authorization: Bearer USER_TOKEN"
```

**Response:** Plain text log chứa:
- Quá trình khởi tạo VM
- Thông tin RDP: host, port, username, password

### 5. Xóa VPS

**Endpoint:** `DELETE /vps/sessions/{session_id}`

```bash
curl -X DELETE http://localhost:8000/vps/sessions/{session_id} \
  -H "Authorization: Bearer USER_TOKEN"
```

**Flow:**
1. Kiểm tra session thuộc về user
2. Gọi API worker để dừng VM (server-side)
3. Đánh dấu session là deleted

### 6. Xem real-time updates

**Endpoint:** `GET /vps/sessions/{session_id}/events` (SSE)

```javascript
const eventSource = new EventSource(
  `/vps/sessions/${sessionId}/events`,
  { headers: { Authorization: `Bearer ${token}` } }
);

eventSource.addEventListener('status.update', (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status);
});

eventSource.addEventListener('checklist.update', (event) => {
  const data = JSON.parse(event.data);
  console.log('Checklist:', data.items);
});
```

## Bảo mật

✅ **TẤT CẢ các API call đến Worker đều được thực hiện từ SERVER**
- User KHÔNG BAO GIỜ gọi trực tiếp đến Worker
- Worker URLs không bao giờ bị lộ ra client
- Backend proxy tất cả requests đến Worker

## Worker API (Chỉ Backend gọi)

Backend tự động gọi các endpoint này:

### 1. Tạo VM
```
POST {worker_base_url}/vm-loso
Body: {"action": 1}  // 1=Linux, 2=Windows, 3=Test
Response: {"logUrl": "/log/quack_xxxxx"}
```

### 2. Dừng VM
```
POST {worker_base_url}/stop/{route}
Response: {"success": true, "message": "...", "tokenReset": "..."}
```

### 3. Lấy log
```
GET {worker_base_url}/log/{route}
Response: Plain text log
```

## Load Balancing

Hệ thống tự động:
1. Đếm số active sessions của mỗi worker
2. Chọn worker có ít sessions nhất
3. Kiểm tra worker chưa vượt quá max_sessions
4. Nếu tất cả workers đều full → trả lỗi 503

**Active session statuses:** pending, provisioning, ready
