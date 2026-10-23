# FlowDiff

[English](README.md)

يقارن البنية بين تدفقين HTTP مسجلين: الحالات، أسماء الترويسات، حقول JSON وأنواعها. يعرض مسارات JSON Pointer لتحديد الفرق بدقة. لا يقارن القيم نفسها، ولذلك تغيير قيمة isAdmin من false إلى true لن يظهر كفرق.

## التشغيل السريع

يتطلب Python 3.10 أو أحدث. من مجلد المشروع:

```bash
python -m flowdiff examples/before.har examples/after.har -o reports/diff.html
```

مثال إضافي:

```bash
python -m flowdiff examples/before.har examples/after.har --pair-by-index -o reports/diff.json
```

## على Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/khdertaysh1.git
cd khdertaysh1/projects/flowdiff
python -m flowdiff --help
```

التحليل محلي ولا يحتاج حسابًا أو اتصالًا بالشبكة. تثبيت Python وGit يتطلب اتصالًا. صُممت الأداة لتناسب Termux ولم تختبر على هاتف فعلي خلال هذا الإصدار.

## التثبيت كأمر مستقل

```bash
python -m pip install .
flowdiff --help
```

المكتبات المستخدمة في التشغيل من مكتبة Python القياسية. قد يحتاج التثبيت إلى تنزيل أدوات بناء الحزمة. يمكن تشغيلها مباشرة من المصدر دون تثبيت.

## قراءة النتائج

الأمثلة مصطنعة بالكامل. النتائج تساعد على التحليل ولا تثبت وجود ثغرة أو اختراق تلقائيًا. راجع قسم Evidence limits and privacy في التوثيق الإنكليزي لحدود التحليل التفصيلية.

التقارير بصيغتي JSON وHTML. عند عدم تحديد مسار إخراج تظهر النتيجة بصيغة JSON في الطرفية. رمز الخروج 0 يعني اكتمال التحليل، و2 يعني خطأ في المدخلات أو التشغيل. قد يستبدل الأمر ملف الإخراج الموجود؛ لا تسمح الأداة باستبدال ملف مدخل محدد.

## الخصوصية

تخفي الأداة قيمًا شائعة حساسة، لكن لا تضمن إزالة كل معلومة شخصية. قد تبقى أسماء الحقول ومسارات URL وأسماء الملفات وعناوين IP. راجع النتائج يدويًا، ولا ترفع ملفات HAR أو سجلات حقيقية إلى مستودع عام.

## الاختبارات

```bash
python -m unittest discover -s tests -v
```

المصدر بترخيص MIT باسم Khedr Tayshoori. اقتراحات التحسين مرحب بها مع مثال مصطنع واختبار يثبت السلوك المطلوب.
