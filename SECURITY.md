# سياسة الأمان | Security Policy

## نسخ مدعومة | Supported Versions

| الإصدار | مدعوم |
|---|---|
| 1.0.x | نعم |

## كيف نبلّغ عن ثغرة | Reporting a Vulnerability

إذا لقيت مشكلة أمنية، بلّغ عنها بالطريقة هذي بدل ما تفتح بلاغ عام:

1. افتح تبويب **Security** في صفحة المشروع على جيتهاب
2. اكتب وصف واضح: شو المشكلة، شو الأثر، كيف نعيد إنتاجها
3. ردّ خلال ٧ أيام، ونتواصل معك على الإصلاح قبل أي نشر عام

**Bilingual:** If you prefer English, write your report in English. Both are welcome.

## ما الذي يمسّه التطبيق | What the app touches

ميراس أداة تنظيف مساحة. تصميمه قائم على مبدأ **عدم الحذف النهائي أبدا**:

- ما في أي مسار حذف نهائي في الكود. العملية الوحيدة هي النقل إلى سلة.
- كل نقل يمر على طبقة حماية مستقلة تتحقق من المسار مرتين.
- المسارات المحمية (النظام، المنزل، إعدادات، مفاتيح، بيانات ألعاب، ملفات
  شخصية) مرفوضة حتى لو ظهرت في نتائج الفحص.
- الملفات معدّلة خلال آخر ٢٤ ساعة لا تُقترح للتنظيف.

إذا لاحظت أي حالة يستطيع فيها التطبيق تجاوز أحد هذه القواعد، فهي ثغرة
وتستحق التقرير فورا.

## خصوصية الفحص | Scanner privacy

الفحص يقرأ أسماء الملفات وأحجامها وتواريخ تعديلها. **لا يقرأ محتوى الملفات**
إلا عند احتساب بصمة التكرار للملفات المكرّرة فقط، ولا تغادر هذه
البصمة الجهاز.

**English:** Meras never performs a permanent delete. It only moves files into
a quarantine folder inside your home directory, and every move is validated by
a dedicated safety layer. File contents are read only to compute a hash for
duplicate detection; nothing is uploaded anywhere.