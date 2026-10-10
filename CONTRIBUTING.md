# المساهمة في ميراس | Contributing to Meras

أهلاً فيك. التطبيق بيحمي ملفات الناس، فأي مساهمة بتمر على معيار واحد:
**ما في أي مسار يقدر يوصل لملف ما المفروض يوصل له.**

---

## قبل ما تبدأ | Before you start

```bash
git clone https://github.com/aihams21/meras.git
cd meras
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install pywebview pyinstaller
```

العدّاد `--system-site-packages` مهم على لينكس لأن جسر النافذة يعتمد على
مكتبة GTK المثبتة مع النظام.

## شغّل الحمايات | Run the guards

```bash
python3 tests/guard_text.py          # يمنع المحارف الممنوعة في كل الملفات
python3 -m unittest discover tests    # اختبارات المنطق والحماية
```

كل منهما لازم ينجح قبل أي عملية حفظ.

## قواعد السلامة | Safety rules

أي مساهمة جديدة لازم تلتزم بها:

1. **ما في حذف نهائي.** استخدم `quarantine` فقط. أي دالة تحذف ملفاً للأبد
   مرفوضة حتى لو كانت في ملف `safety.py`.
2. **كل مسار يمر على `safety.quarantine_allowed` قبل أي نقل.**
3. **أي مسار نظامي أو محمي يُضاف إلى `safety.SENSITIVE_NAMES` أو
   `SYSTEM_PREFIXES_*`.** لا تستثني حماية قائمة لاختصار.
4. **كل سلوك جديد يحتاج اختباراً.** ملف `tests/test_meras.py` فيه اختبار لكل
   قاعدة حماية. أضف اختبارك بجانبه.

## لغة الكود | Code style

- تعليقات ونصوص المستخدم بالعربية أو الإنجليزية، بدون خلط بينهما في نفس الجملة.
- الدوال قصيرة، والاسم يقول الفكرة كاملة.
- لا تضيف اعتمادية جديدة إلا مع سبب مقنع؛ التطبيق يعتمد على مكتبة بايثون
  القياسية في جوهره.

## البناء | Building

```bash
python3 tools/make_icons.py    # يولّد الأيقونات من ملف واحد بصيغة SVG
python3 tools/build_deb.py     # يبني حزمة لينكس
python3 tools/build_app.py     # يبني ملفا تنفيذيا مستقلا
```

## الإرسال | Sending a pull request

1. اعمل نسخة خاصة من المستودع واصنع فرعاً باسم واضح.
2. اكتب بالعربي أو الإنجليزي شو تغيّر وليش.
3. تأكد أن الحمايات كلها تمر.
4. افتح طلب الدمج.

**English version:** Never introduce a permanent delete, always route paths
through `safety.quarantine_allowed`, add a test for every new safety rule, and
make sure both guards pass before opening a pull request.