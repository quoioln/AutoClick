
"""
Capture Button Tool
===================
Tiện ích để chụp ảnh nút Retry trên màn hình.
Chạy script này, di chuột đến nút Retry, nhấn Enter để chụp.

Usage:
    python capture_button.py
"""

import pyautogui
import os
import time
import sys


def capture_region():
    """Chụp một vùng nhỏ xung quanh vị trí chuột hiện tại."""
    images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    os.makedirs(images_dir, exist_ok=True)

    print("=" * 60)
    print("  ANTIGRAVITY RETRY BUTTON CAPTURE TOOL")
    print("=" * 60)
    print()
    print("Hướng dẫn:")
    print("  1. Di chuột đến GIỮA nút 'Retry' trên dialog lỗi")
    print("  2. Nhấn Enter để chụp")
    print("  3. Ảnh sẽ được lưu vào thư mục images/")
    print()
    print("Lưu ý: Đảm bảo dialog lỗi đang hiển thị trên màn hình!")
    print()

    input(">>> Nhấn Enter khi đã đặt chuột ở giữa nút Retry... ")

    # Lấy vị trí chuột
    x, y = pyautogui.position()
    print(f"\nVị trí chuột: ({x}, {y})")

    # Chụp vùng xung quanh nút (mở rộng để bao gồm cả nút)
    # Retry button thường khoảng 80x36 pixels
    width = 100
    height = 44
    left = x - width // 2
    top = y - height // 2

    # Đảm bảo không vượt quá màn hình
    screen_w, screen_h = pyautogui.size()
    left = max(0, left)
    top = max(0, top)

    region = (left, top, width, height)
    screenshot = pyautogui.screenshot(region=region)

    # Lưu file
    filename = "retry_button.png"
    filepath = os.path.join(images_dir, filename)
    screenshot.save(filepath)
    print(f"\n✅ Đã lưu: {filepath}")
    print(f"   Kích thước: {width}x{height} pixels")

    # Chụp thêm một bản lớn hơn cho fallback
    width2 = 140
    height2 = 56
    left2 = x - width2 // 2
    top2 = y - height2 // 2
    left2 = max(0, left2)
    top2 = max(0, top2)

    region2 = (left2, top2, width2, height2)
    screenshot2 = pyautogui.screenshot(region=region2)

    filename2 = "retry_button_large.png"
    filepath2 = os.path.join(images_dir, filename2)
    screenshot2.save(filepath2)
    print(f"✅ Đã lưu (bản lớn): {filepath2}")
    print(f"   Kích thước: {width2}x{height2} pixels")

    # Chụp cả dialog để tham khảo
    print()
    capture_dialog = input("Bạn có muốn chụp cả dialog lỗi không? (y/n): ").strip().lower()
    if capture_dialog == 'y':
        print("\n  Di chuột đến GÓC TRÊN BÊN TRÁI của dialog lỗi...")
        input("  Nhấn Enter khi sẵn sàng... ")
        x1, y1 = pyautogui.position()

        print("  Di chuột đến GÓC DƯỚI BÊN PHẢI của dialog lỗi...")
        input("  Nhấn Enter khi sẵn sàng... ")
        x2, y2 = pyautogui.position()

        dw = x2 - x1
        dh = y2 - y1
        if dw > 0 and dh > 0:
            dialog_screenshot = pyautogui.screenshot(region=(x1, y1, dw, dh))
            dialog_path = os.path.join(images_dir, "error_dialog.png")
            dialog_screenshot.save(dialog_path)
            print(f"\n✅ Đã lưu dialog: {dialog_path}")

    print()
    print("=" * 60)
    print("  Hoàn tất! Bây giờ bạn có thể chạy: python autoclick.py")
    print("=" * 60)


if __name__ == "__main__":
    capture_region()
