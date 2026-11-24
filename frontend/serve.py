"""
Script đơn giản khởi chạy Local Web Server cho phân hệ Frontend AI Interview.
Chạy: python serve.py (mặc định cổng 3000)
"""

import http.server
import socketserver
import os
import webbrowser

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"✨ Frontend AI Interview đang chạy tại: {url}")
        print("💡 Nhấn Ctrl+C để dừng server.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nĐã dừng Frontend Server.")
