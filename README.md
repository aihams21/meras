<div align="center">

# ميراس · Meras

**تطبيق سطح مكتب لتحرير المساحة — لويندوز ولينكس**

[English](#english-summary) · [التحميل](#التحميل) · [الأمان](#الأمان-أولا)

[![CI](https://github.com/aihams21/meras/actions/workflows/ci.yml/badge.svg)](https://github.com/aihams21/meras/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Version](https://img.shields.io/badge/version-1.0.2-blue.svg)

</div>

---

## شو هو ميراس

<div align="center">

### هاد **تطبيق**، مش موقع.

</div>

**كيف بتعرف إنه تطبيق مش موقع؟**

| | تطبيق سطح مكتب (ميراس) | موقع |
|---|---|---|
| شو بتضغط | ملف على جهازك | رابط بالمتصفح |
| شو بتستخدم | نافذة مستقلة | تبويب المتصفح |
| في شريط عنوان المتصفح؟ | **لا** | نعم |
| في متصفح بيشتغل بيه؟ | **لا** | نعم |
| كيف بتقفله؟ | زر ✕ بالشباك | بتقفل المتصفح كله |

بتنصّب الملف عالجهاز وبتحط عليه نقرتين، فتفتحلك **شباك مستقل** على الشاشة،
فوق باقى النوافذ، إلو أزرار تصغير وتكبير وسكّر بإيده. لما سكّر الشباك
بيروح البرنامج كله. **ما في عنوان موقع، ما في شريط أدوات، ما في تبويبات.**

ليش الواجهة مكتوبة بتقنية webpages؟ لأنها أسهل بكتير نطلع فيها تصميم
حلو. بس هاد **مش معناه إنو موقع** — المتصفح متخبّى جوّا الشباك، والفحص
والحماية ونقل الملفات كلّها شغلة بايثون شغّالة ورا الكواليس.

**شو بيعمل البرنامج:**

1. **خريطة مساحتك.** زر ثاني بيفتح خريطة لكل قرص عندك فيها المساحة
   المستعملة والمتبقية، مع ترميز لوني: أخضر للراحة، برتقالي للانتباه، **أحمر
   للخطر**. كل مربع ينقلك إلى الملفات المسؤولة عنه.
2. **تنظيف آمن.** بيفحص الجهاز وبيطلعلك الملفات الكبيرة والمكررة والقديمة
   والمؤقتة، **وبما فيك إلا اللي بتختاره انت**.

**كيف بتستخدمه من أول ما تفتحه:** بتشوف شاشة فيها زر «فحص الجهاز».
بتضغطه، بيفحص وبيطلعلك شريط بيتملا، ولما يخلص بتقدر تتنقل بين خمس شاشات
من الشريط الجانبي: الرئيسية، خريطة المساحة، التنظيف الآمن، السلة، الإعدادات.
وبتلاقي زر اللغة فوق لتبديل عربي/إنجليزي، وزر المظهر للداكن/الفاتح.

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
| مشاريعك البرمجية | **أي شيء داخل مجلد فيه `.git` أو `.hg` أو `.svn`**، حتى مجلد `build` |
| بيانات الألعاب | `Saved Games` `steamapps` ملفات `.sav` |
| ملفات شخصية | `.wallet` `.key` `.sqlite` `.db` |
| الملفات الطازجة | أي ملف معدّل خلال آخر ٢٤ ساعة |

القاعدة: **إذا ما تعرف شو هو، ما بتلمسه.**

---

## التحميل

### ويندوز

| الملف | الشرح |
|---|---|
| [`meras-1.0.2-windows.exe`](https://github.com/aihams21/meras/releases/download/v1.0.2/meras-1.0.2-windows.exe) | ملف واحد مستقل، ما بيحتاج تنصيب |

**التثبيت:** نزّل الملف ← انقر عليه مرتين ← بتشتغل النافذة.

> إذا ظهر تحذير من SmartScreen: اختر **More info** ثم **Run anyway**.
> يظهر لأن الملف غير موقّع رقمياً.

### لينكس

| الملف | الشرح |
|---|---|
| [`meras_1.0.2_amd64.deb`](https://github.com/aihams21/meras/releases/download/v1.0.2/meras_1.0.2_amd64.deb) | لأوبونتو وديبيان وزي-os |
| [`meras-1.0.2-linux.tar.gz`](https://github.com/aihams21/meras/releases/download/v1.0.2/meras-1.0.2-linux.tar.gz) | نسخة محمولة بدون تنصيب |

**الطريقة المنصوح بها — تثبيت الحزمة:**

```bash
sudo apt install ./meras_1.0.2_amd64.deb
```

بعدها بيظهر ميراس في قائمة التطبيقات، وبتفتحه بنقرة وحدة. أو اكتب في
الطرفية:

```bash
meras
```

**النسخة المحمولة — إذا ما بدك تنصيب شي:**

```bash
tar -xzf meras-1.0.2-linux.tar.gz
cd meras
python3 run.py
```

هالأمر بيشغّل الشباك فوراً وبيقعد مفتوح لحد ما سكّره بنفسك. ما بينصّب
ولا شي عالنظام، وكل المكتبات اللي بيشتغلها جاية جوّا المجلد.

> **لو ما عندك `python3` أصلاً:** النسخة المحمولة بتحتاج بايثون 3.9 أو
> أحدث. على أغلب التوزيعات بايثون موجود. الحزمة `.deb` أسهل لأنها بتجيب
> كل شي لحالها.

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

اختبارات المنطق والحماية (٢٢ حالة) بتغطي الماسح، العزل، وحماية المشاريع:
أي مجلد فيه `.git` أو `.hg` أو `.svn` بيصير محمي بالكامل، حتى مجلد `build`
بتاعه، لأن المشروع شغل المستخدم.

وفحص الواجهة بمتصفح حقيقي بيتأكد من: إقلاع التطبيق، التنقل بين الشاشات
الخمسة، تبديل اللغة والمظهر، شريط تقدّم الفحص الحقيقي، التحديد والنقل مع
نافذة التأكيد، مرشّح الخطورة، السلة، وأزرار النافذة.

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

**Meras is a desktop application, not a website.** You install the file on
your machine and double click it, and a native window opens on your screen:
its own minimise, maximise and close buttons, no browser, no address bar, no
tabs, no URL. Close the window and the whole program exits. The web view is
hidden inside the window on purpose; all scanning, safety checking and file
moving happens in Python behind the scenes.

### How to run it

**Windows** — download `meras-1.0.2-windows.exe`, double click it. Done.

**Linux** — either install the package:

```bash
sudo apt install ./meras_1.0.2_amd64.deb
```

then find *Meras* in your applications, or run `meras` in a terminal; or use
the portable build with nothing installed at all:

```bash
tar -xzf meras-1.0.2-linux.tar.gz
cd meras
python3 run.py
```

### What it does

1. **Maps your space.** A second button opens a colour coded map of every
   drive: green for comfortable, amber for caution, red for danger. Each tile
   takes you to the files behind it.
2. **Cleans safely.** It finds duplicate, oversized, old, temporary and build
   leftovers, and cleans only what you select.

Five screens, reachable from the sidebar: Dashboard, Space Map, Safe Cleanup,
Quarantine and Settings. Language (Arabic/English) and theme (dark/light)
buttons sit at the top.

**Nothing is ever deleted permanently.** Selected items move to a quarantine
folder inside your home directory, recorded in a manifest, and can be restored
with one click. System paths, home directories, settings, keys, game saves,
personal files, **anything inside a project folder** (a directory containing
`.git`, `.hg` or `.svn`, including its `build` folder) and anything modified
in the last 24 hours are refused by a dedicated safety layer.

Downloads, installation instructions and checksums are in the
[Releases](https://github.com/aihams21/meras/releases) page.

---

## الرخصة

[MIT](LICENSE) © 2026 Meras Project