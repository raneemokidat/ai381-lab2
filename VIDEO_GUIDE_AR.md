# دليل فهم وعرض — حوالي 7 دقائق

هذا دليل نقاط للفهم، وليس شهادة أن الخطوات حصلت. استخدمي نتائجك وصوتك وتعبيرك، واذكري المساعدة حسب سياسة المساق. لا تخترعي مشكلة أو مراجعة لم تحدث.

| الوقت | العرض |
| --- | --- |
| 0:00–0:30 | Checkpoint 0: Profile خمس ثوانٍ، الوجه والهوية والتاريخ وأمر echo |
| 0:30–1:30 | Checkpoint 1: pytest ثم شرح ما تحميه الاختبارات |
| 1:30–3:30 | Checkpoint 2: Dockerfile سطرًا سطرًا ثم التشغيل والـendpoints |
| 3:30–4:40 | Checkpoint 3: PR checks، تشغيل main، Trivy، GHCR tag وdigest |
| 4:40–5:30 | Checkpoint 4: حماية main والـREADME والشارة |
| 5:30–6:50 | Checkpoint 5: فهمك، مشكلة حقيقية، ومفاضلة |

## الاختبارات

شغلي python -m pytest -q من جذر المشروع. في 21 حالة لأن بعض الدوال parameterized، وليس 21 دالة منفصلة. اشرحي: health يحمي عقد الاستجابة، model-load يكشف ملفًا تالفًا أو غير متوافق، schema يمنع إدخال ناقص أو خاطئ، edge case يضمن قبول الصفر الصحيح، deterministic يقارن تكرار الطلب مع الموديل نفسه. response contract يتحقق من اسم الحقل وحدود الاحتمال.

التكرار وحده لا يثبت صحة النموذج؛ لذلك نقارن أيضًا بما ينتجه pipeline. الاختبارات لا تثبت جودة تنبؤات الإنتاج.

## Dockerfile سطرًا سطرًا

| التعليمة | السبب |
| --- | --- |
| FROM ... AS builder | مرحلة بناء بـPython patch وDebian variant وdigest مثبتين |
| WORKDIR /build | مكان العمل للمرحلة الأولى |
| COPY requirements.txt . | نسخ الاعتماديات أولًا حتى نستفيد من cache |
| RUN pip wheel ... | تنزيل/تجهيز wheels للمرحلة النهائية |
| COPY src ./src | إضافة كود التدريب والخدمة |
| COPY data ./data | إدخال بيانات التدريب للـbuilder فقط |
| RUN pip install ... | تثبيت من wheels دون إعادة تنزيل |
| RUN python -m src.train.train | تدريب وحفظ pipeline كامل مع preprocessing |
| FROM ... AS runtime | بداية مرحلة تشغيل مستقلة |
| ENV ... | إيقاف pyc وتخزين stdout المؤقت لتظهر logs مباشرة |
| WORKDIR /app | مكان خدمة API |
| COPY requirements.txt . | ملف تثبيت التشغيل |
| RUN --mount ... pip install ... | وصول مؤقت لـwheels بدون تركها داخل image النهائية؛ يحتاج BuildKit المتاح في Docker الحديث |
| RUN groupadd ... useradd ... | إنشاء حساب برقم 10001 دون home |
| COPY --chown=app:app src/app ... | نسخ API بملكية المستخدم؛ مجلدات src بدون init تعمل كـnamespace packages |
| COPY --from=builder ... | أخذ الموديل الناتج من البناء؛ بدون بيانات التدريب |
| USER 10001:10001 | تشغيل الخدمة بدون root |
| EXPOSE 8000 | توثيق منفذ الخدمة؛ النشر الفعلي يتم عبر compose ports |
| HEALTHCHECK ... | اختبار HTTP داخلي دوري؛ timeout وإعادة محاولة وفترة سماح |
| CMD ... | تشغيل Uvicorn على كل واجهات الحاوية حتى يقدر port mapping الوصول إليه |

افتحي Dockerfile الفعلي أثناء الشرح. أظهري docker compose ps وفيه healthy، وdocker compose exec api id وفيه UID غير صفر. ثم /health و/predict من curl أو Swagger. في production قد نضيف readiness أعمق؛ health الحالي لا يكشف drift.

## CI وGitHub

PR يعمل lint-and-test دون نشر. الدمج يولّد push على main فيعمل الفحص ثم build-scan-push. Trivy قبل push حتى لا ننشر صورة تفشل بوابة الفحص. الصلاحية packages: write محصورة بجوب النشر. لا نستخدم pull_request_target أو أسرار في اختبارات PR.

commit SHA في tag يربط الصورة بالكود، بينما image digest يحدد بايتات الصورة. تثبيت action SHA يمنع تغير الإصدار خلف tag؛ لكنه يحتاج تحديثًا واعيًا مع الصيانة. تثبيت base digest يحافظ على نفس نقطة البداية لكنه يثبت الثغرات القديمة أيضًا إن لم نحدّثه.

أظهري PR الحقيقي ثم main run الناجح وTrivy ثم GHCR. لا تصفي build والنشر بأنهما يعملان على كل PR: النشر على main فقط كما طلب الدكتور.

## التفكير بصوتك

اختاري مشكلة واجهتك فعلًا: منفذ مشغول، dependency، صلاحية GHCR، أو فحص فشل. اشرحي الخطأ والدليل والإصلاح. إن لم تحدث مشكلة قولي ذلك وناقشي failure case بدل اختراع قصة.

أسئلة لازم تقدري تجاوبيها:

- لماذا يلزم حفظ preprocessing مع classifier؟ حتى تستعمل الخدمة نفس تحويلات التدريب.
- لماذا v2؟ لأنها نفس نسخة Lab 1 وتستخدم monthly_fee، بينما v1 فيها monthly_charges.
- لماذا نعيد التدريب بدل pickle قديم؟ لتوافق البيئة؛ المقابل أن البناء أبطأ ويتطلب بيانات التدريب.
- هل قبول input يعني prediction موثوق؟ لا، schema لا يكشف out-of-distribution.
- ماذا يمنع root؟ يقلل الصلاحيات عند حدوث اختراق؛ لا يغني عن الفحص والتحديث.
- ما مفاضلة ignore-unfixed؟ لا يوقف النشر على ثغرة دون إصلاح، لكنه يترك خطرًا يستحق المتابعة.
- ماذا لو فُقد الموديل؟ startup يفشل بدل خدمة تبدو سليمة ثم تفشل عند أول prediction.
- لماذا نستخدم PR؟ لعرض الفرق وتشغيل الفحوص قبل دمج main؛ الحماية تفرض المسار.
