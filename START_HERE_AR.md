# ابدئي من هون

المشروع مجهز للتجربة والفهم، وليس إثباتًا أن GitHub وDocker نجحا على جهازك. راعي تعليمات الدكتور بخصوص أصالة العمل والمساعدة، وافهمي وعدلي الشغل قبل التسليم. ما في علامة مضمونة أو نتائج نشر مختلقة.

## التشغيل المحلي

تحتاجي Python 3.12 وGit وDocker Desktop شغال. على Windows استخدمي WSL2 Ubuntu. افتحي terminal داخل مجلد lab2، وبدلي YOUR_USERNAME باسم حساب GitHub:

```bash
python3 scripts/configure.py YOUR_USERNAME
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q
docker compose up --build -d
```

انتظري بدء الخدمة ثم:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/predict -H 'Content-Type: application/json' --data @sample_request.json
docker compose ps
docker compose exec api id
```

افتحي http://localhost:8000/docs وجربي قيمة سالبة لتري 422. إذا المنفذ مشغول أوقفي خدمتك القديمة. لإيقاف هذا المشروع: docker compose down.

## إنشاء GitHub وPR

اعملي حساب GitHub وسجلي الدخول بنفسك. ثبتي GitHub CLI حتى تشتغل أوامر gh. الأوامر التالية تنشئ مستودعًا عامًا جديدًا باسم ai381-lab2؛ نفذيها داخل مجلد المشروع فقط. بدلي اسمك وبريدك بقيم حسابك:

```bash
gh auth login
git config --global user.name "YOUR_NAME"
git config --global user.email "YOUR_GITHUB_EMAIL"
git init -b main
git add README.md
git commit -m "Initialize Lab 2 repository"
gh repo create ai381-lab2 --public --source=. --remote=origin --push
git switch -c lab2-container-ci
git add .
git commit -m "Add tested churn API, Docker and CI"
git push -u origin lab2-container-ci
gh pr create --base main --head lab2-container-ci --title "Package churn model with Docker and CI" --body-file PR_BODY.md
```

main يبدأ بـREADME فقط حتى يدخل التطبيق من PR حقيقي. راقبي فحص lint-and-test على PR حتى ينجح.

## حماية main قبل الدمج

GitHub → المستودع → Settings → Branches → Add classic branch protection rule. النمط main. فعلي:

- Require a pull request before merging.
- Require status checks to pass before merging، واختاري lint-and-test بعد ظهوره من أول PR.
- Require branches to be up to date before merging.
- Do not allow bypassing the above settings، إن ظهر.
- اتركي force pushes والحذف غير مسموحين.

لمشروع فردي لا تشترطي موافقة reviewer آخر إذا ما عندك شخص يراجع، لأنك لا تستطيعين اعتماد PR تبعك. لا تدعي أن مراجعة شخص آخر حصلت. إذا تستخدمين Rulesets فعلي الشروط نفسها على main مع الحالة Active. احفظي ثم ادمجي PR من موقع GitHub بعد نجاح الفحص.

## النشر والأدلة

Actions → تشغيل CI الناتج عن الدمج إلى main. انتظري lint-and-test ثم build-scan-push. سيبني الحاوية ويشغلها ويفحصها بـTrivy ثم ينشرها. إذا فشل افتحي أول خطوة حمراء. لا تضيفي continue-on-error ولا تغيري exit-code لإخفاء الفشل.

إذا رفض GHCR الصلاحيات افحصي Settings → Actions → General وسياسة المؤسسة إن وجدت. الـworkflow يطلب packages: write ويستعمل GITHUB_TOKEN التلقائي. لا تضعي tokens أو كلمات مرور في الملفات.

من Summary للتشغيل الناجح انسخي tag وdigest الحقيقيين. افتحي حسابك → Packages → الصورة وأظهري SHA tag. إذا تحتاجي سحبًا بدون دخول اجعلي package عامة من إعداداتها؛ علنية repository لا تكفي دائمًا. افتحي README وأظهري badge الخضراء.

ما يجب إثباته بنفسك: اختبارات محلية، Docker شغال وhealthy، PR ناجح، حماية main، تشغيل main ناجح، GHCR image وdigest. قبل التسليم افتحي رابط المستودع من نافذة خاصة للتأكد أن المقيّم يقدر يفتحه.

## التسليم

فيديو واحد MP4 بدقة 720p ومدته 5–8 دقائق، وخط terminal على الأقل 14. ابدئي من صفحة Profile في elearn.just.edu.jo، الاسم والرقم ظاهرين 5 ثوانٍ، ثم وجهك وصوتك واسمك ورقمك ورقم اللاب والتاريخ. نفذي، بعد استبدال StudentID:

```bash
echo "AI381 StudentID $(date)"
```

خلي وجهك ظاهرًا picture-in-picture خلال التسجيل. قولي اسم كل checkpoint، واتركي كل نتيجة 5 ثوانٍ على الأقل. اسم الملف StudentID_FirstName_LastName_Lab2.mp4 بدون فراغات وبالأسماء الرسمية. Teams → Assignments → Lab 2 → Add work، أضيفي الفيديو ورابط GitHub ثم Turn in. الموعد 31 أكتوبر 2026، 11:59 مساءً بتوقيت الأردن.
