"""نقطه‌ی ورود WSGI (برای پلتفرم‌هایی که دنبال wsgi.py می‌گردن، مثل چابکان)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import application  # noqa: E402,F401
