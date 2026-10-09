دعوت به دیت (Django تک‌فایلی)
=============================

صفحه‌ی دعوت:  /
پنل ادمین:   /panel/   (فقط وقتی ADMIN_PASSWORD ست شده باشه کار می‌کنه)

متغیرهای محیطی
--------------
ADMIN_PASSWORD  الزامی. رمز پنل.
SECRET_KEY      پیشنهادی. یک رشته‌ی تصادفی بلند.
DATA_DIR        مسیر ذخیره‌ی answers.sqlite3 (پیش‌فرض: کنار app.py).
                روی سرویس‌های کانتینری/PaaS حتماً به یک دیسک پایدار اشاره کنه (مثلاً /data)،
                وگرنه با هر دیپلوی جدید جواب‌ها پاک می‌شن.
ALLOWED_HOSTS   اختیاری. مثلاً: example.ir,www.example.ir  (پیش‌فرض: همه)
HTTPS=1         اگه سایت با https سرو می‌شه ست کن تا کوکی پنل secure باشه.
PORT            پورتی که gunicorn روش گوش می‌ده (پیش‌فرض 8000).

اجرای محلی
----------
pip install -r requirements.txt
ADMIN_PASSWORD=رمزت python app.py runserver 0.0.0.0:8000

اجرا با Docker (برای هر سرویسی که Dockerfile بپذیره)
-----------------------------------------------------
docker build -t date-invite .
docker run -p 8000:8000 -v invite-data:/data -e ADMIN_PASSWORD=رمزت -e SECRET_KEY=یک-رشته-تصادفی date-invite

اجرا بدون Docker
----------------
pip install -r requirements.txt
ADMIN_PASSWORD=... SECRET_KEY=... DATA_DIR=/path/to/data gunicorn app:application -b 0.0.0.0:8000
(دستور start سرویس: gunicorn app:application -b 0.0.0.0:$PORT)

نکته‌ها
-------
- پوشه‌ی fonts باید کنار app.py بمونه؛ فونت‌ها از خود سرور سرو می‌شن و هیچ درخواست خارجی نداریم.
- پشت nginx/پروکسی همه‌ی مسیرها (از جمله /fonts/ و /api/answer/) باید به برنامه برسن.

چابکان (سرویس Django)
---------------------
- پلتفرم دنبال wsgi.py می‌گرده و collectstatic رو با manage.py اجرا می‌کنه؛ هر دو فایل توی پروژه هست
  (wsgi.py همون app.application رو بالا میاره و manage.py collectstatic رو بی‌خطر رد می‌کنه).
- توی تنظیمات متغیرهای محیطی سرویس حتماً ADMIN_PASSWORD رو ست کن. SECRET_KEY هم بهتره باشه.
- اگه با هر دیپلوی جدید جواب‌ها پاک شد، DATA_DIR رو روی مسیری بذار که روی سرویس پایداره.
- اگه باز هم wsgi پیدا نشد، WSGI_PATH رو دستی ست کن (فرمتش رو از مستندات چابکان ببین؛ احتمالاً wsgi:application).
