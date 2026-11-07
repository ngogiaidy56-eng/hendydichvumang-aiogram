# Hendy Dịch Vụ Mạng — Telegram Bot (aiogram v3)

Bot Telegram bất đồng bộ dùng **aiogram v3**, một luồng asyncio, JSON storage cho bản chạy một instance và HTTP health server để triển khai dưới dạng Render Web Service hoặc Docker container.

> **Tình trạng tích hợp HomeProxy Hub:** adapter HTTP đã có sẵn, nhưng route, schema dữ liệu và cách xác thực phụ thuộc vào bản cài HomeProxy Hub. Không bật chức năng route trong môi trường thật trước khi đối chiếu API contract của máy chủ.

## Tính năng

- /start, /help: menu chính và hướng dẫn.
- /proxy: menu điều khiển proxy.
- /status: lấy trạng thái HomeProxy Hub từ endpoint đã cấu hình.
- /credit: truy vấn credit theo Telegram user ID.
- Nút inline kết nối/ngắt kết nối; yêu cầu gửi tới adapter sau khi cấu hình route chính xác.
- /me, /id: xem hồ sơ Telegram và ID của chính người dùng.
- /admin: bảng quản trị chỉ dành cho ID trong ADMIN_IDS.
- /users, /user TELEGRAM_ID, /events: các lệnh quản trị chỉ đọc hồ sơ và lịch sử hoạt động.
- Callback quản trị được xác thực lại ở backend; không dựa vào việc ẩn nút giao diện.
- /health, /ready: health/readiness endpoints cho Render.
- JSON storage ghi bất đồng bộ, cập nhật qua file tạm và thay thế nguyên tử; giới hạn lịch sử ở 1.000 sự kiện.
- GitHub Actions kiểm tra Python 3.12/3.13, Ruff, compile và unit tests.

## Cấu trúc

~~~text
hendydichvumang_aiogram/
├── .github/
│   ├── dependabot.yml
│   └── workflows/ci.yml
├── bot/
│   ├── handlers/
│   │   ├── admin.py
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

## 1. Cài đặt và chạy local

Yêu cầu Python 3.12 hoặc 3.13.

~~~bash
python -m venv .venv

# Windows PowerShell
.\\.venv\\Scripts\\Activate.ps1
Copy-Item .env.example .env

# Linux/macOS
source .venv/bin/activate
cp .env.example .env

python -m pip install --upgrade pip
pip install -r requirements-dev.txt
~~~

Sửa .env và điền tối thiểu BOT_TOKEN. Lấy token từ BotFather; không đưa token thật vào GitHub, ảnh chụp màn hình hoặc tin nhắn công khai.

~~~bash
python main.py
~~~

Bot dùng **long polling**. Không bật webhook đồng thời bằng cùng một bot token. Nếu trước đây token đang chạy webhook, cần xóa webhook qua Telegram Bot API trước khi chạy polling.

## 2. Cấu hình môi trường

| Biến | Bắt buộc | Ý nghĩa |
|---|---:|---|
| BOT_TOKEN | Có | Token từ BotFather |
| ADMIN_IDS | Không | Telegram numeric user ID, phân tách dấu phẩy hoặc chấm phẩy |
| MINI_APP_URL | Không | URL HTTPS của Mini App; nút chỉ hiện khi có URL |
| DATABASE_PATH | Không | Mặc định database.json |
| HOME_PROXY_HUB_API_URL | Cho API | URL gốc HTTPS; HTTP chỉ được phép với localhost khi phát triển |
| HOME_PROXY_HUB_API_TOKEN | Cho API | Token API; không ghi vào mã nguồn |
| HOME_PROXY_AUTH_SCHEME | Không | Mặc định Bearer |
| HOME_PROXY_STATUS_PATH | Cho /status | Đường dẫn GET trạng thái |
| HOME_PROXY_CREDIT_PATH | Cho /credit | Đường dẫn GET credit |
| HOME_PROXY_ROUTE_PATH | Cho connect/disconnect | Đường dẫn POST thao tác route |
| HOME_PROXY_TIMEOUT_SECONDS | Không | Timeout HTTP, mặc định 15 giây |
| HOST / PORT | Không | Mặc định 0.0.0.0:10000; Render cung cấp PORT |
| LOG_LEVEL | Không | Mặc định INFO |

ADMIN_IDS chỉ chứa ID số, ví dụ 123456789,987654321. Có thể lấy ID bằng lệnh /id sau khi bot khởi động.

## 3. Kết nối HomeProxy Hub

Tên “HomeProxy Hub” chưa xác định duy nhất một API công khai. Mỗi bản triển khai có thể có route, schema, auth header và payload khác nhau. Hãy lấy thông tin từ tài liệu/API explorer hoặc quản trị máy chủ đang chạy, sau đó khai báo chính xác các biến HOME_PROXY_*.

Adapter hiện thực hiện:

- GET HOME_PROXY_STATUS_PATH để lấy trạng thái.
- GET HOME_PROXY_CREDIT_PATH?telegram_user_id=<Telegram ID> để lấy credit.
- POST HOME_PROXY_ROUTE_PATH với JSON mặc định:

~~~json
{
  "telegram_user_id": 123456789,
  "username": "telegram_username",
  "action": "connect"
}
~~~

Khi ngắt kết nối, action là disconnect. Đây là **payload adapter hiện tại**, không phải khẳng định rằng server HomeProxy Hub của bạn đã hỗ trợ sẵn schema này. Nếu API thực tế khác, chỉnh ProxyService.get_credit() hoặc ProxyService.set_route() theo tài liệu chính thức trước khi bật thao tác.

Bảo vệ trong adapter: chỉ nhận URL gốc HTTPS (hoặc localhost HTTP khi dev), chỉ nhận path tương đối, chặn URL tuyệt đối/path traversal/query, tắt redirect cho request có Authorization, giới hạn response 64 KB và không chuyển nguyên văn response lỗi/dữ liệu text tùy ý vào Telegram. Các trường có tên giống token/secret/password cũng được che trước khi hiển thị.

## 4. Kiểm thử

~~~bash
python -m compileall -q .
python -m unittest discover -s tests -v
ruff check .
~~~

Unit tests dùng HTTP server localhost giả lập, không cần token Telegram thật hoặc máy chủ HomeProxy Hub thật.

## 5. GitHub — repository đã được tạo

Repository đích: https://github.com/ngogiaidy56-eng/hendydichvumang-aiogram (nhánh main).

Cài Git và GitHub CLI, đăng nhập đúng tài khoản có quyền push:

~~~bash
gh auth login

# Linux/macOS
bash scripts/publish_to_github.sh

# Windows PowerShell
.\\scripts\\publish_to_github.ps1
~~~

Script kiểm tra repository và remote origin, commit các file thay đổi và push lên main. Script sẽ dừng nếu remote hiện tại trỏ sang repository khác.

GitHub Actions chạy khi push main/master/develop, khi mở Pull Request và khi chạy thủ công. Theo dõi tại tab **Actions** của repository.

## 6. Triển khai Render Web Service

Có thể tạo Web Service bằng Blueprint render.yaml, hoặc cấu hình thủ công:

- Runtime: Python
- Build command: pip install -r requirements.txt
- Start command: python main.py
- Health check path: /health
- Environment variables: thêm BOT_TOKEN, ADMIN_IDS, và các HOME_PROXY_* sau khi xác minh API contract.

Render injects PORT; ứng dụng bind 0.0.0.0:$PORT. Web Service chạy một tiến trình bot polling. Không chạy nhiều instance chia sẻ cùng token polling.

### Lưu database bền vững

Filesystem thông thường của Web Service không bảo đảm giữ dữ liệu qua mọi lần deploy/restart. Để giữ JSON database, gắn Persistent Disk trong Render tại /var/data, rồi đặt:

~~~text
DATABASE_PATH=/var/data/database.json
~~~

Persistent Disk có thể phát sinh chi phí theo gói/dung lượng của Render; hãy xem giá trong Dashboard trước khi xác nhận. JSON storage chỉ phù hợp một instance. Khi cần nhiều instance, giao dịch tài chính, số dư hoặc xử lý đồng thời phức tạp, chuyển sang PostgreSQL với transaction và idempotency.

## 7. Telegram Mini App

MINI_APP_URL chỉ thêm nút mở Mini App trong Telegram. Repository này chưa chứa frontend Mini App và chưa triển khai xác thực Telegram initData cho backend web. Cần xây dựng frontend/API riêng và kiểm tra chữ ký initData ở server trước khi dùng dữ liệu người dùng cho thao tác nhạy cảm.

## 8. Bảo mật và giới hạn vận hành

- Không commit .env, token, API secret, database.json hoặc log cá nhân.
- Chỉ ID trong ADMIN_IDS dùng được lệnh/callback quản trị.
- Không ghi header Authorization vào log.
- Không dùng JSON file làm sổ cái tài chính hoặc cơ sở dữ liệu nhiều instance.
- Chưa xác minh kết nối thật tới HomeProxy Hub cho đến khi có API URL, token và schema được nhà cung cấp xác nhận.
- Chưa thể kiểm thử Telegram end-to-end nếu chưa khai báo token trong Environment Variables của môi trường triển khai.
