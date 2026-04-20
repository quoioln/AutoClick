#!/bin/bash

echo "================================================="
echo "   ANTIGRAVITY AUTO-RETRY MAC OS BUILDER"
echo "================================================="
echo "Tool này sẽ đóng gói autoclick.py thành file thực thi độc lập cho macOS."
echo "Lưu ý: Bạn phải chạy script này TRỰC TIẾP TRÊN MÁY MAC."
echo ""

if [ "$(uname -s)" != "Darwin" ]; then
    echo "❌ LỖI: Bạn đang chạy script này trên $(uname -s)."
    echo "Script này CHỈ có thể chạy trên máy tính Mac (macOS)."
    echo "Xin vui lòng copy toàn bộ thư mục sang máy Mac và chạy lại."
    exit 1
fi

# Kiểm tra python3
if ! command -v python3 &> /dev/null
then
    echo "❌ Không tìm thấy python3! Vui lòng cài đặt Python (https://www.python.org/downloads/macos/)."
    exit 1
fi

echo "📦 Đang cài đặt môi trường ảo (virtual environment)..."
python3 -m venv .venv_mac
source .venv_mac/bin/activate

echo "📦 Đang cài đặt dependencies..."
pip install --upgrade pip
pip install pyautogui opencv-python Pillow pyinstaller

echo "🔨 Đang đóng gói Auto-Retry (Image Matching Mode)..."
# macOS không hỗ trợ pywinauto, nên chúng ta đóng gói bản autoclick.py (image matching)
pyinstaller --onefile --windowed --clean autoclick.py

if [ -f "dist/autoclick" ] || [ -d "dist/autoclick.app" ]; then
    echo ""
    echo "✅ XONG! Tool đã được đóng gói thành công."
    echo "Bạn có thể tìm thấy ứng dụng tại thư mục:"
    echo "   📍 dist/autoclick"
    echo "   📍 hoặc dist/autoclick.app"
    echo ""
    echo "💡 LƯU Ý KHI CHẠY TRÊN MAC:"
    echo "1. Chế độ Win32 (pywinauto) không hỗ trợ trên macOS nên tool sử dụng Image Matching."
    echo "2. Bạn cần chụp lại ảnh nút Retry trên màn hình Mac trước (chạy: python3 capture_button.py)."
    echo "3. Cấp quyền 'Accessibility' & 'Screen Recording' cho Terminal/App trong System Settings."
else
    echo "❌ Có lỗi xảy ra trong quá trình đóng gói!"
fi
