#!/usr/bin/env python
"""مثل manage.py استاندارد جنگو؛ collectstatic رو بی‌خطر رد می‌کنه (فایل استاتیک نداریم، فونت‌ها از خود برنامه سرو می‌شن)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "collectstatic":
        print("collectstatic: nothing to do (no static files).")
        sys.exit(0)
    import app  # noqa: F401  (تنظیمات جنگو رو configure می‌کنه)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
