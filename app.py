"""
دعوت به دیت + پنل ادمین (Django تک‌فایلی)

اجرا:
    pip install -r requirements.txt
    ADMIN_PASSWORD=رمز-خودت python app.py runserver 0.0.0.0:8000

صفحه‌ی دعوت:  /
پنل ادمین:    /panel/
پروداکشن:     gunicorn app:application -b 0.0.0.0:$PORT
متغیرها:      ADMIN_PASSWORD (الزامی)، SECRET_KEY، DATA_DIR، ALLOWED_HOSTS، HTTPS=1
"""
import os, sys, json, time, sqlite3, html, hashlib
from django.conf import settings

PASSWORD = os.environ.get("ADMIN_PASSWORD", "")  # بدون ست‌شدن، پنل قفل می‌مونه
SECRET = os.environ.get("SECRET_KEY") or hashlib.sha256(("invite|" + PASSWORD).encode()).hexdigest()

if not settings.configured:
    settings.configure(
        DEBUG=os.environ.get("DEBUG") == "1",
        SECRET_KEY=SECRET,
        ROOT_URLCONF="app",
        ALLOWED_HOSTS=[h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h.strip()],
        MIDDLEWARE=[],
        INSTALLED_APPS=[],
    )

from django.urls import path
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core import signing
from django.core.wsgi import get_wsgi_application

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", BASE)  # روی سرویس‌های کانتینری این رو روی یک دیسک پایدار بذار
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "answers.sqlite3")

if not PASSWORD:
    print("WARNING: ADMIN_PASSWORD تنظیم نشده؛ پنل /panel/ غیرفعاله.", file=sys.stderr)


def db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY, sid TEXT, k TEXT, v TEXT, ts REAL)")
    return c


db().close()

# ---------- فونت‌ها (روی همین سرور سرو می‌شن، بدون هیچ اتصال خارجی) ----------
FONTS_DIR = os.path.join(BASE, "fonts")
_RANGE = {
    "arabic": "U+0600-06FF,U+200C-200E,U+2010-2011,U+204F,U+2E41,U+FB50-FDFF,U+FE80-FEFC",
    "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-200B,U+200F-206F,U+2074,U+20AC,U+2122,U+2212,U+FEFF",
}
_FACES = [("Vazirmatn", "vazirmatn", 400), ("Vazirmatn", "vazirmatn", 700)]
FONT_FILES = set()
FONTFACE = ""
for _fam, _slug, _w in _FACES:
    for _sub in ("arabic", "latin"):
        _f = f"{_slug}-{_sub}-{_w}-normal.woff2"
        FONT_FILES.add(_f)
        FONTFACE += (f"@font-face{{font-family:'{_fam}';font-weight:{_w};font-display:swap;"
                     f"src:url(/fonts/{_f}) format('woff2');unicode-range:{_RANGE[_sub]}}}")


def font(request, name):
    if name not in FONT_FILES:
        return HttpResponse(status=404)
    with open(os.path.join(FONTS_DIR, name), "rb") as fh:
        r = HttpResponse(fh.read(), content_type="font/woff2")
    r["Cache-Control"] = "public, max-age=31536000, immutable"
    return r


QUESTIONS = {
    "accept": "افتخار می‌دی؟",
    "love": "می‌دونی دوستت دارم؟",
    "food": "غذا",
    "time": "ساعت",
    "no_attempts": "تلاش برای زدن «نه»",
    "opened": "باز کردن صفحه",
}

PAGE = """<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#18040e" id="tc">
<title>یک پیام برای تو</title>
<link rel="preload" href="/fonts/vazirmatn-arabic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>
/*FONTFACE*/
:root{--r1:#ffd0e0;--r2:#ff7aa8;--r3:#e91e63;--r4:#b0124f;--bg:#fff1f6;--card:#fffafc;
--txt:#5a1230;--mute:#a8627f;--ease:cubic-bezier(.22,1,.36,1)}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{height:100%}
body{margin:0;min-height:100dvh;display:flex;overflow-x:hidden;
padding:max(18px,env(safe-area-inset-top)) 18px max(18px,env(safe-area-inset-bottom));
background:radial-gradient(ellipse 90% 55% at 50% -8%,#ffd0e0 0%,transparent 70%),
radial-gradient(ellipse 70% 45% at 50% 108%,#ffbfd4 0%,transparent 70%),var(--bg);
color:var(--txt);font-family:"Vazirmatn",Tahoma,sans-serif;font-size:16px}
.rose{background:linear-gradient(110deg,var(--r4) 0%,#ff5c8d 28%,var(--r3) 52%,#ff5c8d 76%,var(--r4) 100%);
background-size:220% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shine 7s linear infinite}
.title{font-weight:700}
.petals{position:fixed;inset:0;pointer-events:none;overflow:hidden}
.petals i{position:absolute;bottom:-40px;font-style:normal;color:var(--r2);opacity:0;animation:float linear infinite}

.card{position:relative;margin:auto;width:100%;max-width:430px;min-height:440px;display:none;flex-direction:column;align-items:center;text-align:center;
padding:30px 24px 28px;border-radius:28px;border:1.5px solid transparent;
background:linear-gradient(var(--card),var(--card)) padding-box,linear-gradient(160deg,#ffb3cf,var(--r3) 45%,#ffc2d6 80%,var(--r2)) border-box;
box-shadow:0 26px 60px rgba(176,18,79,.18),0 4px 14px rgba(233,30,99,.08)}
.card::before{content:"";position:absolute;inset:8px;border:1px solid rgba(233,30,99,.14);border-radius:21px;pointer-events:none}
.card::after{content:"♥";position:absolute;top:-15px;left:50%;transform:translateX(-50%);padding:0 10px;font-size:20px;line-height:1;
color:var(--r3);background:var(--bg);border-radius:20px}
.card.on{display:flex;animation:rise .9s var(--ease)}
.bar{display:flex;gap:6px;width:100%;margin-top:4px}
.bar i{flex:1;height:3px;border-radius:3px;background:rgba(233,30,99,.14);overflow:hidden;position:relative}
.bar i::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,var(--r2),var(--r3));transform:translateX(100%);transition:transform .7s var(--ease)}
.bar i.on::after{transform:none}
.count{font-size:12px;color:var(--mute);margin:12px 0 0;min-height:18px}

.stage{flex:1;width:100%;display:flex;flex-direction:column;justify-content:center;padding:18px 0 4px}
.step{display:none;flex-direction:column;align-items:center}
.step.on{display:flex;animation:slide .6s var(--ease)}
.hello{font-size:clamp(26px,7.6vw,32px);line-height:1.7;margin:0}
.line{margin:2px 0;line-height:2.15;font-size:16px}
.line b{color:var(--r3);font-weight:700}
h2{margin:6px 0 0;font-size:clamp(22px,6.4vw,28px);line-height:1.8}
.note{font-size:13px;color:var(--mute);margin-top:6px}
.orn{display:flex;align-items:center;gap:10px;margin:12px 0;width:64%;color:var(--r3);font-size:13px}
.orn::before,.orn::after{content:"";flex:1;height:1px;background:linear-gradient(90deg,transparent,var(--r2))}
.orn::after{transform:scaleX(-1)}

.btns{display:grid;grid-template-columns:1fr 1fr;gap:12px;width:100%;margin-top:28px;position:relative}
@media(max-width:360px){.btns{grid-template-columns:1fr}}
button{font:inherit;font-size:16px;font-weight:700;border-radius:16px;padding:0 12px;min-height:54px;cursor:pointer;
border:1.5px solid rgba(233,30,99,.35);position:relative;overflow:hidden;transition:transform .2s var(--ease),box-shadow .3s,background .3s}
button:active{transform:scale(.96)}
.pri{background:linear-gradient(135deg,#ff8db3,var(--r3) 75%);color:#fff;border:0;box-shadow:0 10px 24px rgba(233,30,99,.32)}
.pri::after{content:"";position:absolute;top:0;bottom:0;width:40%;left:-60%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.5),transparent);
transform:skewX(-20deg);animation:sweep 3.6s ease-in-out infinite}
.alt{background:rgba(255,255,255,.7);color:var(--r4)}
@media(hover:hover){.pri:hover{box-shadow:0 12px 30px rgba(233,30,99,.46);transform:translateY(-2px)}.alt:hover{background:#ffe3ec}}
#no{transition:transform .35s cubic-bezier(.3,1.7,.5,1)}

.overlay{position:fixed;inset:0;z-index:20;display:flex;align-items:center;justify-content:center;padding:20px;
background:rgba(24,4,14,.97);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);cursor:pointer;transition:opacity .9s ease,visibility .9s}
.overlay.off{opacity:0;visibility:hidden}
.modal{width:100%;max-width:370px;text-align:center;padding:30px 24px;border-radius:26px;border:1.5px solid transparent;outline:none;
background:linear-gradient(180deg,#2c0b1c,#17050e) padding-box,linear-gradient(160deg,#ffb3cf,#e91e63 50%,#ff7aa8) border-box;
box-shadow:0 0 80px rgba(255,122,168,.2);animation:pop .8s var(--ease),glow 2.6s ease-in-out .8s infinite}
.modal h3{margin:0;font-size:clamp(21px,6vw,26px);line-height:2;
background:linear-gradient(110deg,#ffd0e0,#ff7aa8 40%,#ffd0e0 70%,#ff9cbd);background-size:220% 100%;
-webkit-background-clip:text;background-clip:text;color:transparent;animation:shine 7s linear infinite}

.heart{width:88px;height:88px;filter:drop-shadow(0 8px 16px rgba(233,30,99,.4));animation:beat 1.8s ease-in-out infinite}
.sp{position:fixed;bottom:-30px;animation:up 5.5s linear forwards;pointer-events:none;z-index:5}

@keyframes shine{to{background-position:-220% 0}}
@keyframes sweep{0%,55%{left:-60%}100%{left:130%}}
@keyframes rise{from{opacity:0;transform:translateY(26px) scale(.97)}to{opacity:1;transform:none}}
@keyframes slide{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.9) translateY(24px)}to{opacity:1;transform:none}}
@keyframes glow{0%,100%{box-shadow:0 0 50px rgba(255,122,168,.14)}50%{box-shadow:0 0 95px rgba(255,122,168,.38)}}
@keyframes beat{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
@keyframes up{to{transform:translateY(-112vh) rotate(40deg);opacity:0}}
@keyframes float{0%{transform:translateY(0) rotate(0);opacity:0}12%{opacity:.55}100%{transform:translateY(-108vh) rotate(35deg);opacity:0}}
@media(prefers-reduced-motion:reduce){*{animation-duration:.01s!important;animation-iteration-count:1!important}}
</style></head><body>
<div class="petals" id="petals"></div>

<div class="overlay" id="ov" onclick="openMsg()">
 <div class="modal" role="button" tabindex="0" onkeydown="if(event.key==='Enter'||event.key===' ')openMsg()">
  <h3 class="title">این پیام از طرفِ خرسه<br>(میعاد)</h3>
 </div>
</div>

<main class="card" id="card">
 <div class="bar" id="bar"><i></i><i></i><i></i><i></i></div>
 <div class="count" id="count"></div>
 <div class="stage">

  <section class="step on">
   <p class="hello title rose">سلام قشنگم</p>
   <div class="orn">♥</div>
   <p class="line">روز <b>۱۹ مهرماه</b>، روزِ توئه</p>
   <p class="line">می‌خوام لطفاً کنارم باشی و بریم بیرون</p>
   <h2 class="title rose" style="margin-top:14px">افتخاری بهم می‌دی؟</h2>
   <div class="btns">
    <button class="pri" onclick="ans('accept','بله',1)">بله</button>
    <button class="alt" id="no">نه</button>
   </div>
  </section>

  <section class="step">
   <h2 class="title rose">می‌دونی دوستت دارم<br>یا نه؟</h2>
   <div class="btns">
    <button class="pri" onclick="ans('love','می‌دونم',2)">آره، می‌دونم</button>
    <button class="alt" onclick="ans('love','نمی‌دونم',2)">نه، نمی‌دونم</button>
   </div>
  </section>

  <section class="step">
   <h2 class="title rose">سنتی یا فست‌فود؟</h2>
   <div class="btns">
    <button class="pri" onclick="ans('food','سنتی',3)">سنتی</button>
    <button class="pri" onclick="ans('food','فست‌فود',3)">فست‌فود</button>
   </div>
  </section>

  <section class="step">
   <h2 class="title rose">ساعت ۸ یا ۹؟</h2>
   <div class="note">البته قبلش باید بهت بگم، حتماً</div>
   <div class="btns">
    <button class="pri" onclick="ans('time','۸',4)">ساعت ۸</button>
    <button class="pri" onclick="ans('time','۹',4)">ساعت ۹</button>
   </div>
  </section>

  <section class="step">
   <svg class="heart" viewBox="0 0 64 64" aria-hidden="true">
    <defs><linearGradient id="hg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff9cbd"/><stop offset=".6" stop-color="#e91e63"/><stop offset="1" stop-color="#b0124f"/></linearGradient></defs>
    <path d="M32 56S6 40 6 22a13 13 0 0 1 26-4 13 13 0 0 1 26 4c0 18-26 34-26 34z" fill="url(#hg)"/>
   </svg>
   <h2 class="title rose" style="margin-top:14px">عالی شد</h2>
   <div class="orn">♥</div>
   <p class="line">منتظرتم، قشنگم.</p>
   <p class="note">ــ خرسه</p>
  </section>

 </div>
</main>

<script>
const sid = Math.random().toString(36).slice(2) + Date.now().toString(36);
const send = (k, v) => fetch("/api/answer/", {method: "POST", keepalive: true,
  headers: {"Content-Type": "application/json"}, body: JSON.stringify({sid, k, v})}).catch(() => {});
const steps = document.querySelectorAll(".step"), segs = document.querySelectorAll("#bar i");
const fa = n => String(n).replace(/[0-9]/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);
const PINKS = ["#ff7aa8", "#e91e63", "#ff9cbd", "#f06292"];
function show(n){
  steps.forEach((e, i) => e.classList.toggle("on", i === n));
  segs.forEach((d, i) => d.classList.toggle("on", i <= n));
  document.getElementById("count").textContent = n < 4 ? "سؤال " + fa(n + 1) + " از " + fa(4) : "";
  if (n === 4) sparkle();
}
function openMsg(){
  document.getElementById("ov").classList.add("off");
  document.getElementById("card").classList.add("on");
  document.getElementById("tc").setAttribute("content", "#fff1f6");
  show(0); send("opened", "1");
}
function ans(k, v, next){ send(k, v); show(next); }
function sparkle(){
  for (let i = 0; i < 26; i++) {
    const s = document.createElement("div"); s.className = "sp"; s.textContent = "♥";
    s.style.color = PINKS[i % PINKS.length];
    s.style.left = Math.random() * 100 + "vw"; s.style.fontSize = (14 + Math.random() * 22) + "px";
    s.style.animationDelay = Math.random() * 2 + "s"; document.body.appendChild(s);
    setTimeout(() => s.remove(), 9000);
  }
}
(function petals(){
  const d = document.getElementById("petals");
  for (let i = 0; i < 16; i++) {
    const p = document.createElement("i"); p.textContent = "♥";
    p.style.left = Math.random() * 100 + "%"; p.style.fontSize = (10 + Math.random() * 14) + "px";
    p.style.animationDuration = (10 + Math.random() * 10) + "s"; p.style.animationDelay = (-Math.random() * 16) + "s";
    d.appendChild(p);
  }
})();
let tries = 0;
const no = document.getElementById("no");
function dodge(e){
  e.preventDefault(); tries++; send("no_attempts", String(tries));
  const r = Math.min(110, window.innerWidth * 0.26);
  no.style.transform = "translate(" + ((Math.random() - .5) * 2 * r) + "px," + ((Math.random() - .5) * 2 * 60) + "px) scale(" + Math.max(.55, 1 - tries * .07) + ")";
}
no.addEventListener("mouseenter", dodge);
no.addEventListener("touchstart", dodge, {passive: false});
no.addEventListener("click", dodge);
</script></body></html>"""


def index(request):
    return HttpResponse(PAGE.replace("/*FONTFACE*/", FONTFACE))


@csrf_exempt
def api_answer(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)
    try:
        d = json.loads(request.body)
        sid, k, v = str(d["sid"])[:40], str(d["k"])[:30], str(d["v"])[:100]
    except Exception:
        return JsonResponse({"ok": False}, status=400)
    if k not in QUESTIONS:
        return JsonResponse({"ok": False}, status=400)
    c = db()
    c.execute("INSERT INTO answers(sid,k,v,ts) VALUES(?,?,?,?)", (sid, k, v, time.time()))
    c.commit(); c.close()
    return JsonResponse({"ok": True})


def authed(request):
    try:
        return signing.loads(request.COOKIES.get("adm", ""), salt="adm", max_age=86400 * 30) == "ok"
    except Exception:
        return False


STYLE = "<style>" + FONTFACE + """
*{box-sizing:border-box}
body{font-family:Vazirmatn,Tahoma,sans-serif;background:radial-gradient(ellipse 90% 40% at 50% -5%,#ffd0e0,transparent 70%),#fff1f6;
color:#5a1230;margin:0;padding:max(16px,env(safe-area-inset-top)) 16px 28px;min-height:100vh}
.wrap{max-width:980px;margin:0 auto}
.top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:16px}
h1{font-size:clamp(18px,5vw,22px);color:#c2185b;margin:0}
.live{font-size:12px;color:#a8627f;white-space:nowrap}.live::before{content:"";display:inline-block;width:7px;height:7px;border-radius:50%;
background:#e91e63;margin-left:6px;animation:p 1.6s infinite}
@keyframes p{50%{opacity:.25}}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px}
.stat{background:#fffafc;border:1px solid rgba(233,30,99,.25);border-radius:16px;padding:14px 10px;text-align:center;box-shadow:0 6px 18px rgba(176,18,79,.07)}
.stat b{display:block;font-size:clamp(22px,6vw,28px);color:#e91e63}.stat span{font-size:12px;color:#a8627f}
table{width:100%;border-collapse:collapse;background:#fffafc;border:1px solid rgba(233,30,99,.25);border-radius:16px;overflow:hidden;box-shadow:0 6px 18px rgba(176,18,79,.07)}
th,td{padding:13px 12px;border-bottom:1px solid rgba(233,30,99,.1);text-align:right;font-size:14px}
th{background:#ffe3ec;color:#b0124f;font-weight:700;font-size:13px}
tr:last-child td{border-bottom:0}
.yes{color:#e91e63;font-weight:700}.muted{color:#c9a0b2}
.login{max-width:360px;margin:12vh auto 0;background:#fffafc;border:1px solid rgba(233,30,99,.3);border-radius:20px;padding:26px 20px;text-align:center;box-shadow:0 14px 40px rgba(176,18,79,.14)}
.login h1{margin-bottom:16px}
input,button{font:inherit;width:100%;padding:14px;border-radius:12px;border:1px solid rgba(233,30,99,.35);background:#fff;color:#5a1230;font-size:16px}
button{background:linear-gradient(135deg,#ff8db3,#e91e63);color:#fff;border:0;font-weight:700;margin-top:12px;cursor:pointer}
@media(max-width:700px){
 thead{display:none}
 table,tbody,tr,td{display:block;width:100%}
 table{background:none;border:0;border-radius:0;box-shadow:none}
 tr{background:#fffafc;border:1px solid rgba(233,30,99,.25);border-radius:16px;margin-bottom:12px;padding:6px 14px;box-shadow:0 6px 18px rgba(176,18,79,.07)}
 td{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid rgba(233,30,99,.08)}
 td:last-child{border-bottom:0}
 td::before{content:attr(data-label);color:#a8627f;font-size:12px;flex-shrink:0}
 td.when{font-size:12px;color:#a8627f}
 td.empty{display:block;text-align:center}td.empty::before{content:none}
}
</style>"""

HEAD = ('<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="theme-color" content="#fff1f6">')


@csrf_exempt
def panel(request):
    if not PASSWORD:
        return HttpResponse(f"{HEAD}<title>پنل</title>{STYLE}<div class=\"login\"><h1>پنل غیرفعاله</h1><p>متغیر ADMIN_PASSWORD روی سرور ست نشده.</p></div></html>", status=503)
    if request.method == "POST" and request.POST.get("password") == PASSWORD:
        r = HttpResponseRedirect("/panel/")
        r.set_cookie("adm", signing.dumps("ok", salt="adm"), httponly=True, samesite="Lax", secure=os.environ.get("HTTPS") == "1", max_age=86400 * 30)
        return r
    if not authed(request):
        return HttpResponse(f"""{HEAD}<title>ورود</title>{STYLE}
<form class="login" method="post"><h1>ورود به پنل</h1>
<input type="password" name="password" placeholder="رمز عبور" autofocus><button>ورود</button></form></html>""")

    c = db()
    rows = c.execute("SELECT sid,k,v,ts FROM answers ORDER BY ts").fetchall()
    c.close()
    visits = {}
    for sid, k, v, ts in rows:
        s = visits.setdefault(sid, {"last": ts})
        s["last"] = ts
        s[k] = v  # آخرین مقدار هر سؤال
    out, accepted, tries_total = [], 0, 0
    for sid, s in sorted(visits.items(), key=lambda x: -x[1]["last"]):
        def cell(k):
            val = s.get(k)
            return html.escape(val) if val else '<span class="muted">—</span>'
        if s.get("accept"):
            accepted += 1
        try:
            tries_total += int(s.get("no_attempts", 0))
        except ValueError:
            pass
        acc = '<span class="yes">بله</span>' if s.get("accept") else '<span class="muted">هنوز نه</span>'
        when = time.strftime("%Y-%m-%d  %H:%M", time.localtime(s["last"]))
        out.append(f'<tr><td class="when" data-label="آخرین فعالیت">{when}</td>'
                   f'<td data-label="افتخار می‌دی؟">{acc}</td>'
                   f'<td data-label="می‌دونی دوستت دارم؟">{cell("love")}</td>'
                   f'<td data-label="غذا">{cell("food")}</td>'
                   f'<td data-label="ساعت">{cell("time")}</td>'
                   f'<td data-label="تلاش برای «نه»">{cell("no_attempts")}</td></tr>')
    body = "".join(out) or '<tr><td class="empty muted" colspan="6">هنوز کسی صفحه رو باز نکرده</td></tr>'
    return HttpResponse(f"""{HEAD}<meta http-equiv="refresh" content="10"><title>پنل جواب‌ها</title>{STYLE}
<div class="wrap">
<div class="top"><h1>پنل جواب‌ها</h1><span class="live">به‌روزرسانی خودکار</span></div>
<div class="stats">
<div class="stat"><b>{len(visits)}</b><span>بازدید</span></div>
<div class="stat"><b>{accepted}</b><span>گفته بله</span></div>
<div class="stat"><b>{tries_total}</b><span>تلاش برای «نه»</span></div>
</div>
<table><thead><tr><th>آخرین فعالیت</th><th>افتخار می‌دی؟</th><th>می‌دونی دوستت دارم؟</th>
<th>غذا</th><th>ساعت</th><th>تلاش برای «نه»</th></tr></thead><tbody>{body}</tbody></table>
</div></html>""")


urlpatterns = [path("", index), path("fonts/<str:name>", font), path("api/answer/", api_answer), path("panel/", panel)]
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
