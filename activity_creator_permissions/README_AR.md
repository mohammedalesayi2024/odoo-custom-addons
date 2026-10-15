# Activity Creator Permissions — Odoo 19

## الإصدار 19.0.1.0.2
هذا الإصدار يجمع صلاحيات المنشئ مع الاحتفاظ بسجل التنبيهات الملغاة.

- منشئ النشاط أو مدير النظام يستطيع تعديل النشاط وإعادة إسناده وإلغاءه.
- المستخدم المسند إليه يستطيع إكمال النشاط المسند إليه فقط.
- زر Cancel يؤرشف النشاط ويسجل `Activity Status = Cancelled` بدلًا من حذفه.
- عند إكمال النشاط يسجل `Activity Status = Done`.
- الحقل `Activity Status` مخزن وقابل للاستخدام في Custom Filter.

## تحديث Odoo.sh
1. استبدل مجلد `activity_creator_permissions` القديم بهذا المجلد.
2. نفّذ Commit ثم Push إلى الفرع المطلوب.
3. انتظر اكتمال البناء.
4. من Apps حدّث قائمة التطبيقات ثم اضغط Upgrade للموديول.
5. افتح My Activities، فعّل Include archived، ثم أنشئ Custom Filter على `Activity Status` واختر `Cancelled`.

ملاحظات:
- يعتمد على `mail` ويستهدف Odoo 19.
- السجلات المحذوفة قبل التحديث لا يمكن استرجاعها.
- `Activity Status` حقل مخصص منفصل عن `State` الافتراضي.
- تم فحص صياغة Python؛ اختبره على قاعدة تجريبية قبل الإنتاج.
