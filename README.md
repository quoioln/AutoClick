# 🔄 Antigravity Auto-Retry Clicker

Tự động nhấn nút **Retry** khi Antigravity gặp lỗi:
- "Our servers are experiencing high traffic"
- "Agent terminated due to error"

## 📦 Cài đặt

```bash
# Di chuyển đến thư mục project
cd c:\Working\Projects\autoclick\SourceCode\autoclick

# Cài đặt dependencies
pip install -r requirements.txt

# (Tuỳ chọn) Cho chế độ Win32 - không cần ảnh reference
pip install pywinauto
```

## 📦 Đóng gói thành File Chạy Trực Tiếp (.EXE / .APP)

Nếu bạn không muốn quan tâm đến Python hay Terminal, bạn có thể đóng gói Tool thành file thực thi chạy thẳng.

### 1. Dành cho Windows (.EXE)
Tool đã được đóng gói sẵn thành file EXE chạy thẳng. Bạn có thể tìm thấy tại:
👉 `dist/autoclick_win32.exe`
Bạn chỉ cần copy file `autoclick_win32.exe` này ra Desktop hoặc bất kỳ đâu và bấm đúp để chạy, không cần cài Python nữa!

*(Nếu muốn tự đóng gói lại, bạn chạy lệnh: `uv pip install pyinstaller` và chạy `pyinstaller --onefile --clean autoclick_win32.py`)*

### 2. Dành cho macOS (.APP / Unix Executable)
⚠️ **Lưu ý:** Bạn không thể build ứng dụng Mac từ máy Windows. Bạn **bắt buộc** phải copy toàn bộ thư mục code này sang máy Mac của bạn.

Hơn nữa, chế độ Win32 UI Automation không hoạt động trên MacOS, bạn sẽ sử dụng chế độ gốc là **Image Matching** (`autoclick.py`).

**Các bước build trên Mac:**
1. Copy thư mục project sang máy Mac.
2. Mở Terminal trên Mac và cd vào thư mục project.
3. Chạy file script tự động build:
   ```bash
   chmod +x build_mac.sh
   ./build_mac.sh
   ```
4. Tool sẽ được build thành file thực thi tại `dist/autoclick`.
5. Đừng quên chạy `python3 capture_button.py` để chụp ảnh nút Retry trên giao diện của Mac trước khi bật chạy! Đồng thời bạn cần cấp quyền "Accessibility" và "Screen Recording" cho Terminal/App trong máy Mac.

---

## 🚀 Sử dụng

### Cách 1: Win32 Mode (Khuyến nghị - không cần ảnh reference)

```bash
python autoclick_win32.py
```

**Ưu điểm:**
- ✅ Không cần chụp ảnh nút trước
- ✅ Hoạt động ở mọi theme, zoom level, resolution
- ✅ Chính xác hơn (dùng UI Automation API)

### Cách 2: Image Matching Mode

**Bước 1:** Chụp ảnh nút Retry
```bash
# Khi dialog lỗi đang hiển thị trên màn hình
python capture_button.py
```

**Bước 2:** Chạy auto-clicker
```bash
python autoclick.py
```

## ⌨️ Phím tắt

| Phím | Chức năng |
|------|-----------|
| `F6` | Bật/Tắt quét |
| `F7` | Thoát chương trình |

## 💻 Lệnh Console

| Lệnh | Chức năng |
|-------|-----------|
| `start` / `s` | Bắt đầu quét |
| `stop` / `p` | Dừng quét |
| `toggle` / `t` | Bật/Tắt |
| `stats` / `i` | Xem thống kê |
| `quit` / `q` | Thoát |

## ⚙️ Cấu hình

Chỉnh sửa file `config.json`:

```json
{
  "scan_interval_seconds": 3,      // Thời gian giữa mỗi lần quét (giây)
  "confidence": 0.8,                // Độ chính xác image matching (0.0-1.0)
  "click_delay_seconds": 0.5,       // Delay trước khi click
  "max_retries_per_session": 0,     // Giới hạn retry (0 = unlimited)
  "hotkey_toggle": "F6",            // Phím bật/tắt
  "hotkey_quit": "F7",              // Phím thoát
  "sound_enabled": true             // Âm thanh thông báo
}
```

## 📂 Cấu trúc

```
autoclick/
├── autoclick.py           # Main - Image matching mode
├── autoclick_win32.py     # Main - Win32 UI Automation mode
├── capture_button.py      # Tool chụp ảnh nút Retry
├── config.json            # Cấu hình
├── requirements.txt       # Dependencies
├── images/                # Ảnh reference (tạo bởi capture_button.py)
│   ├── retry_button.png
│   └── retry_button_large.png
└── README.md
```

## 🔧 Troubleshooting

### Không tìm thấy nút Retry (Image Mode)
1. Đảm bảo dialog lỗi đang hiển thị
2. Chạy lại `capture_button.py` để chụp ảnh mới
3. Giảm `confidence` trong config.json (vd: 0.7)

### Không tìm thấy nút Retry (Win32 Mode)
1. Đảm bảo VS Code không bị minimize
2. Kiểm tra VS Code đang chạy trên primary monitor

### Hotkey không hoạt động
- Chạy script với quyền Administrator
- Hoặc cài module keyboard: `pip install keyboard`

## ⚠️ Lưu ý

- Tool chỉ hoạt động khi VS Code đang visible trên màn hình
- Di chuột vào góc màn hình để kích hoạt fail-safe (dừng PyAutoGUI)
- Logs được lưu tại `autoclick.log` hoặc `autoclick_win32.log`
