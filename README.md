# Hendy Dịch Vụ Mạng — Telegram Bot (aiogram v3)

Bot Telegram bất đồng bộ dùng **aiogram v3**, một luồng asyncio, JSON storage cho bản chạy một instance và HTTP health server để triển khai dưới dạng Render Web Service hoặc Docker container.

## Menu chính và ảnh trang chủ

Lệnh `/start` hiển thị 11 nút inline theo thứ tự dịch vụ:

1. 🚀 MINIGAME LIVE
2. 📲 OTP & PROXY
3. 💠 TRUNG TÂM KHÁCH HÀNG
4. 👑 DỊCH VỤ SẮP TRIỂN KHAI
5. 👑 KHO CÔNG CỤ TOOLS ĐỘC QUYỀN
6. 💳 NẠP TIỀN
7. 🗣️ NHÓM CHAT
8. 🧑🏻‍💻 LIÊN HỆ CSKH
9. 🎁 CODE MÀN - CODE TELE
10. 👑 TRUNG TÂM VIP
11. 🎟️ NHẬP GIFTCODE

Khi đã cấu hình `BOT_HOME_PHOTO`, bot gửi ảnh và menu cùng một tin nhắn. Có thể đặt biến này thành:
- Telegram `file_id` (khuyến nghị trên Render);
- URL HTTPS của ảnh;
- đường dẫn file ảnh tồn tại trong filesystem của dịch vụ.

### Lấy Telegram photo file_id

1. Khởi động bot và bảo đảm Telegram ID của bạn nằm trong `ADMIN_IDS`.
2. Gửi ảnh banner trực tiếp cho bot.
3. Dùng chức năng Reply vào ảnh đó và gửi `/photoid`.
4. Bot trả về `BOT_HOME_PHOTO=...`; sao chép giá trị đó vào Render → Environment → `BOT_HOME_PHOTO`.
5. Lưu biến và redeploy/restart dịch vụ.

Nếu ảnh không tải được, bot ghi log loại lỗi và tự gửi menu dạng văn bản để người dùng vẫn truy cập được chức năng.

Một số menu có thể cấu hình liên kết bằng `BOT_MINIGAME_URL`, `BOT_GROUP_CHAT_URL`, `BOT_SUPPORT_URL`; nút Trung tâm khách hàng mở Mini App khi có `MINI_APP_URL`. Các module nạp tiền, code, VIP và giftcode hiện hiển thị trạng thái chờ tích hợp, không giả lập giao dịch.

## Tính năng bot

- /start, /help: menu chính và hướng dẫn.
- /proxy: menu điều khiển proxy.
- /status: lấy trạng thái HomeProxy Hub từ endpoint đã cấu hình.
- /credit: truy vấn credit theo Telegram user ID.
- Nút inline kết nối/ngắt kết nối; yêu cầu gửi tới adapter sau khi cấu hình route chính xác.
- /me, /id: xem hồ sơ Telegram và ID của chính người dùng.
- /admin: bảng quản trị chỉ dành cho ID trong ADMIN_IDS.
- /photoid: lấy file_id ảnh, chỉ admin sử dụng.
- /users, /user TELEGRAM_ID, /events: lệnh quản trị chỉ đọc hồ sơ và lịch sử hoạt động.
- /health, /ready: health/readiness endpoints cho Render.
- JSON storage ghi bất đồng bộ, cập nhật qua file tạm và thay thế nguyên tử; giới hạn lịch sử ở 1.000 sự kiện.
- GitHub Actions kiểm tra Python 3.12/3.13, Ruff, compile và unit tests.

> **Tình trạng tích hợp HomeProxy Hub:** adapter HTTP đã có sẵn, nhưng route, schema dữ liệu và cách xác thực phụ thuộc vào bản cài HomeProxy Hub. Không bật chức năng route trong môi trường thật trước khi đối chiếu API contract của máy chủ.

## Cấu trúc

~~~text
hendydichvumang_aiogram/
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── bot/
│   ├── handlers/
│   │   ├── admin.py
│   │   ├── menu.py
│   │   └── proxy.py
│   ├── keyboards/inline.py
│   └── loader.py
├── services/
│   ├── proxy_service.py
│   └── sanitize.py
├── tests/
├── scripts/
├── config.py
├── database.py
├── main.py
├── requirements.txt
├── requirements-dev.txt
├── render.yaml
└── Dockerfile
~~~

## Cài đặt và chạy local

Yêu cầu Python 3.12 hoặc 3.13.

~~~bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env

# Linux/macOS
source .venv/bin/activate
cp .env.example .env

python -m pip install --upgrade pip
pip install -r requirements-dev.txt
~~~

Sửa `.env` và điền tối thiểu `BOT_TOKEN`. Lấy token từ BotFather; không đưa token thật vào GitHub, ảnh chụp màn hình hoặc tin nhắn công khai.

~~~bash
python main.py
~~~

Bot dùng **long polling**. Không bật webhook đồng thời bằng cùng một bot token. Nếu trước đây token đang chạy webhook, cần xóa webhook qua Telegram Bot API trước khi chạy polling.

## Biến môi trường

| Biến | Ý nghĩa |
|---|---|
| `BOT_TOKEN` | Token từ BotFather (bắt buộc) |
| `ADMIN_IDS` | Telegram numeric user ID, phân tách dấu phẩy hoặc chấm phẩy |
| `BOT_HOME_PHOTO` | Telegram file_id, URL HTTPS hoặc đường dẫn file ảnh |
| `MINI_APP_URL` | URL HTTPS Telegram Mini App; nút Trung tâm khách hàng mở Mini App khi đã cấu hình |
| `BOT_MINIGAME_URL` | URL HTTPS cho nút MINIGAME LIVE |
| `BOT_GROUP_CHAT_URL` | URL HTTPS cho nút NHÓM CHAT |
| `BOT_SUPPORT_URL` | URL HTTPS cho nút LIÊN HỆ CSKH |
| `DATABASE_PATH` | Mặc định database.json; Render Persistent Disk nên dùng /var/data/database.json |
| `HOME_PROXY_HUB_API_URL` | URL gốc HTTPS của HomeProxy Hub |
| `HOME_PROXY_HUB_API_TOKEN` | Token API; không ghi vào mã nguồn |
| `HOME_PROXY_AUTH_SCHEME` | Mặc định Bearer |
| `HOME_PROXY_STATUS_PATH` | Đường dẫn GET trạng thái |
| `HOME_PROXY_CREDIT_PATH` | Đường dẫn GET credit |
| `HOME_PROXY_ROUTE_PATH` | Đường dẫn POST thao tác route |
| `HOME_PROXY_TIMEOUT_SECONDS` | Timeout HTTP, mặc định 15 giây |
| `HOST` / `PORT` | Mặc định 0.0.0.0:10000; Render cung cấp PORT |
| `LOG_LEVEL` | Mặc định INFO |

`ADMIN_IDS` chỉ chứa ID số, ví dụ `123456789,987654321`. Có thể lấy ID bằng lệnh `/id`.

## Kết nối HomeProxy Hub

Tên “HomeProxy Hub” chưa xác định duy nhất một API công khai. Mỗi bản triển khai có thể có route, schema, auth header và payload khác nhau. Hãy lấy thông tin từ tài liệu/API explorer hoặc quản trị máy chủ đang chạy, sau đó khai báo chính xác các biến `HOME_PROXY_*`.

Adapter hiện thực hiện GET status, GET credit theo Telegram ID và POST connect/disconnect với payload adapter hiện tại. Đây không phải khẳng định rằng server HomeProxy Hub của bạn đã hỗ trợ sẵn schema đó. Nếu API thực tế khác, chỉnh `ProxyService` theo tài liệu chính thức trước khi bật thao tác.

## Kiểm thử

~~~bash
python -m compileall -q .
python -m unittest discover -s tests -v
ruff check .
~~~

Unit tests dùng HTTP server localhost giả lập, không cần token Telegram thật hoặc máy chủ HomeProxy Hub thật.

## Triển khai Render

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Health check path: `/health`
- Environment: thêm BOT_TOKEN, ADMIN_IDS, BOT_HOME_PHOTO và những URL/API bạn thực sự sử dụng.

Render injects `PORT`; ứng dụng bind `0.0.0.0:$PORT`. Web Service chạy một tiến trình bot polling. Không chạy nhiều instance chia sẻ cùng token polling.

Để giữ JSON database qua deploy/restart, gắn Persistent Disk tại `/var/data` và đặt `DATABASE_PATH=/var/data/database.json`. JSON storage chỉ phù hợp một instance; khi mở rộng hoặc quản lý số dư/giao dịch, chuyển sang PostgreSQL có transaction và idempotency.

## Giới hạn triển khai

- Mini App frontend và xác thực Telegram `initData` chưa nằm trong repository.
- Nạp tiền, VIP, kho tools, code và giftcode hiện là menu trạng thái chờ tích hợp, không xử lý giao dịch thật.
- Chưa xác minh kết nối thật tới HomeProxy Hub cho đến khi có API URL, token và schema được nhà cung cấp xác nhận.
- Không commit `.env`, token, API secret, `database.json` hoặc log cá nhân.
