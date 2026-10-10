<div align="center">

# ميراس · Meras

**تطبيق سطح مكتب لتحرير المساحة — لويندوز ولينكس**

[English](#english-summary) · [التحميل](#التحميل) · [الأمان](#الأمان-أولا)

[![CI](https://github.com/aihams21/meras/actions/workflows/ci.yml/badge.svg)](https://github.com/aihams21/meras/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)

</div>

---

## شو هو ميراس

ميراس تطبيق حقيقي بتنقر عليه مرتين، بتفتحلك نافذة. **ما في متصفح، ما في
شريط عنوان، ما في رابط.** كل شي بيشتغل خلف الكواليس.

بيعمل شيئين:

1. **خريطة مساحتك.** زر ثاني بيفتح خريطة لكل قرص عندك فيها المساحة
   المستعملة والمتبقية، مع ترميز لوني: أخضر للراحة، برتقالي للانتباه، **أحمر
   للخطر**. كل مربع ينقلك إلى الملفات المسؤولة عنه.
2. **تنظيف آمن.** بيفحص الجهاز وبيطلعلك الملفات الكبيرة والمكررة والقديمة
   والمؤقتة، **وبما فيك إلا اللي بتختاره انت**.

---

## المبدأ الذي لا يُخترق

<div align="center">

### ما في حذف نهائي. أبداً.

</div>

العملية الوحيدة اللي بتنفّذها هي **النقل إلى سلة داخل بيتك**، ومع كل نقل
سجلّ فيه الحجم والوقت والمسار الأصلي. بتقدر ترجّع كل شي بضغطة واحدة.

أي ملف ما تعرفش شو هو، ما بتلمسه. الملف بيطلعلك باسمه وحجمه وسبب
الاقتراح، وأنت اللي بتقرر.

---

## شو اللي ما بيمسّه التطبيق أبداً

| محمي | أمثلة |
|---|---|
| نظام التشغيل | `/usr` `/etc` `/bin`، `C:\Windows` `C:\Program Files` |
| مجلد المنزل | جذر المجلد و `home` |
| إعدادات ومفاتيح | `.ssh` `.git` `.env` `.gnupg` `id_rsa` |
| بيانات الألعاب | `Saved Games` `steamapps` ملفات `.sav` |
| ملفات شخصية | `.wallet` `.key` `.sqlite` `.db` |
| الملفات الطازجة | أي ملف معدّل خلال آخر ٢٤ ساعة |

القاعدة: **إذا ما تعرف شو هو، ما بتلمسه.**

---

## التحميل

### ويندوز

| الملف | الشرح |
|---|---|
| [`meras-1.0.1-windows.exe`](https://github.com/aihams21/meras/releases/download/v1.0.1/meras-1.0.1-windows.exe) | ملف واحد مستقل، ما بيحتاج تنصيب |

**التثبيت:** نزّل الملف ← انقر عليه مرتين ← بتشتغل النافذة.

> إذا ظهر تحذير من SmartScreen: اختر **More info** ثم **Run anyway**.
> يظهر لأن الملف غير موقّع رقمياً.

### لينكس

| الملف | الشرح |
|---|---|
| [`meras_1.0.1_amd64.deb`](https://github.com/aihams21/meras/releases/download/v1.0.1/meras_1.0.1_amd64.deb) | لأوبونتو وديبيان وزي-os |
| [`meras-1.0.1-linux.tar.gz`](https://github.com/aihams21/meras/releases/download/v1.0.1/meras-1.0.1-linux.tar.gz) | نسخة محمولة بدون تنصيب |

**تثبيت الحزمة:**

```bash
sudo apt install ./meras_1.0.1_amd64.deb
```

بعدها بيظهر ميراس في قائمة التطبيقات، أو اكتب في الطرفية:

```bash
meras
```

**تشغيل النسخة المحمولة بدون تنصيب:**

```bash
tar -xzf meras-1.0.1-linux.tar.gz
cd meras
python3 run.py
```

> على لينكس، الحزمة بتطلب `python3-gi` و `gir1.2-webkit2-4.1` وهي موجودة
> أصلا على أي توزيعة حديثة. لو ناقصك شي، مدير الحزم رح يخبرك بالاسم.

### التحقق من سلامة الملف

كل إصدار بيحتوي ملف بصمات `SHA256SUMS.txt`:

```bash
sha256sum -c SHA256SUMS.txt
```

---

## الواجهة

عندك خمس شاشات، بتنتقل بينها من الشريط الجانبي:

| الشاشة | شو فيها |
|---|---|
| **الرئيسية** | مؤشر دائري للقرص، قدّيش ممكن تسترجع، وأرقام آخر فحص |
| **خريطة المساحة** | كل قرص عندك، مستخدَم ومتاح، ومعه مجلداتك بأحجامها الحقيقية |
| **التنظيف الآمن** | الفئات مقسّمة حسب الخطورة، كل وحدة منها تفتح وتختار منها |
| **السلة** | كل شي نقلته، مع زر استرجاع لكل عنصر أو للكل |
| **الإعدادات** | اللغة، المظهر، وقائمة المسارات اللي التطبيق ما بيمسّها أبداً |

شريط النافذة فوق (تصغير، تكبير، سكّر) موجود دايماً، واللون بيتغيّر حسب
خطر العنصر: أخضر آمن، أصفر حذر، أحمر خطر.

**زر المسح** بيطلع لك شريط تقدّم حقيقي بيبيّن المرحلة والمجلد اللي عم
يقرأه، مش رقم عشوائي.

**حماية مضاعفة:** بتختار ← بتشوف النتيجة ← بتكتب كلمة التأكيد ← وقتها بس بينقل.

---

## بناء التطبيق من المصدر

```bash
git clone https://github.com/aihams21/meras.git
cd meras

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install pywebview pyinstaller

python3 run.py            # نافذة التطبيق
python3 run.py --web      # وضع المتصفح للتطوير فقط
```

**البناء:**

```bash
python3 tools/make_icons.py    # يولّد كل الأيقونات من ملف SVG واحد
python3 tools/build_deb.py     # حزمة لينكس + نسخة محمولة
python3 tools/build_app.py     # ملف تنفيذي مستقل
```

---

## الاختبارات والحمايات

```bash
python3 tests/guard_text.py                  # يمنع المحارف الممنوعة في كل الملفات
python3 -m unittest discover tests           # اختبارات المنطق والحماية
```

اختبار الواجهة الكامل (يتطلب تنصيب `jsdom`) يتحقق من ٨٠ حالة: إقلاع
التطبيق، التنقل بين الشاشات الخمس، تبديل اللغة والمظهر، شريط تقدّم الفحص
الحقيقي، التحديد والنقل مع نافذة التأكيد، مرشّح الخطورة، السلة، وظهور شريط
النافذة عند وصول جسر سطح المكتب.

---

## بنية المشروع

```
meras/
├── meras/
│   ├── platform_info.py   الأقراص والمجلدات الشخصية
│   ├── safety.py          طبقة الحماية — أهم ملف بالتطبيق
│   ├── scanner.py         محرّك الفحص
│   ├── quarantine.py      السلة والاسترجاع
│   ├── server.py          الخادم المحلي
│   └── desktop.py         نافذة التطبيق الأصلية
├── web/                   الواجهة: html, css, js، والترجمة
├── tools/                 بناء الحزم والأيقونات
├── tests/                 الاختبارات والحارس النصي
└── run.py                 نقطة التشغيل
```

---

## الخصوصية

الفحص يقرأ **أسماء الملفات وأحجامها وتواريخ تعديلها فقط**. محتوى الملفات
ما بينقرأ إلا لحساب بصمة التكرار للملفات المكرّرة، وهالبصمة ما بتطلع من
جهازك.

- ما في إنترنت، ولا اتصال بأي خادم.
- ما في إحصائيات، ولا تتبّع، ولاعلانات.
- السلة بمكان `~/.meras_quarantine` وسجلّها `manifest.json`.

---

<a name="english-summary"></a>

## English summary

Meras is a real desktop application for Windows and Linux. Double click it and
a native window opens. There is no browser, no address bar, and no URL: the
local server runs entirely behind the scenes.

It does two things:

1. **Maps your space.** A second button opens a colour coded map of every
   drive: green for comfortable, amber for caution, red for danger. Each tile
   takes you to the files behind it.
2. **Cleans safely.** It finds duplicate, oversized, old, temporary and build
   leftovers, and cleans only what you select.

**Nothing is ever deleted permanently.** Selected items move to a quarantine
folder inside your home directory, recorded in a manifest, and can be restored
with one click. System paths, home directories, settings, keys, game saves,
personal files and anything modified in the last 24 hours are refused by a
dedicated safety layer.

Downloads, installation instructions and checksums are in the
[Releases](https://github.com/aihams21/meras/releases) page.

---

## الرخصة

[MIT](LICENSE) © 2026 Meras Project