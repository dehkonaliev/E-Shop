E-SHOP API

Django REST Framework asosida email-confirmation va JWT autentifikatsiyali onlayn magazin APIsi.

TEXNOLOGIYALAR
- Python / Django / Django REST Framework
- SQLite (productionda PostgreSQL tavsiya etiladi)
- SimpleJWT va token blacklist
- django-filter, DRF search va ordering
- drf-spectacular Swagger/ReDoc
- django-cors-headers

LOYIHANI ISHLAB CHIQISH
1. python -m venv venv
2. Windows: venv\Scripts\activate
   Linux/macOS: source venv/bin/activate
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py runserver

Swagger UI: http://127.0.0.1:8000/api/docs/
OpenAPI schema: http://127.0.0.1:8000/api/schema/
ReDoc: http://127.0.0.1:8000/api/redoc/
Postman Collection: ../postman_collection.json

AUTENTIFIKATSIYA OQIMI
1. POST /api/auth/register/ orqali email yuboriladi va TempUser yaratiladi.
2. POST /api/auth/email-confirm/ orqali 6 xonali kod tasdiqlanadi.
3. Bir martalik activation token qaytariladi va emailga yuboriladi.
4. POST /api/auth/user-activation/ orqali username va password yuboriladi.
5. CustomUser yaratiladi hamda access/refresh JWTlar qaytariladi.
6. Himoyalangan endpointlarda header: Authorization: Bearer <access_token>
7. POST /api/auth/token/refresh/ orqali access token yangilanadi.
8. POST /api/auth/logout/ orqali refresh token blacklistga qo'shiladi.

Eski /api/auth/temp-create va /api/auth/email-confirm marshrutlar ham saqlangan.

ASOSIY ENDPOINTLAR
- GET/POST /api/categories/
- GET/POST /api/products/
- GET/PATCH/DELETE /api/products/{id}/
- POST /api/products/{id}/like/
- GET /api/likes/
- GET/POST /api/products/{id}/comments/
- GET /api/cart/
- POST /api/cart/add/
- POST /api/cart/remove/
- POST /api/orders/checkout/
- GET /api/orders/
- GET/PATCH /api/orders/{id}/

Mahsulotlar uchun category (slug), category_id (ID), min_price, max_price, search, ordering, page va page_size query parametrlari qo'llab-quvvatlanadi.

ROLLAR
- Anonim: katalog, kategoriyalar va sharhlarni o'qish.
- Customer: profil, like, savat, checkout va o'z buyurtmalari.
- Admin: kategoriya/mahsulot CRUD va barcha buyurtma holatlarini boshqarish.

TESTLAR
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run

ADMIN PANEL
Manzil: http://127.0.0.1:8000/admin/
Admin rol: is_staff=True va is_superuser=True bo'lishi kerak.

  python manage.py createsuperuser
Dashboard quyidagilarni ko'rsatadi:
- Mahsulotlar soni, zaxira qiymati va ombordagi birliklar
- Kategoriyalar, mijozlar va sharhlar soni
- Buyurtmalar soni, tumanlar bo'yicha holatlar va tushum
- Eng ko'p buyurtma qilgan mijozlar (order/item soni va sarflangan summa)
- So'nggi buyurtmalar va kam qolgan mahsulotlar ro'yxati

Admin imkoniyatlari:
- Products: qo'shish, tahrirlash, o'chirish, narx/zaxira, rasm, "sold out" va
  "restock" amallari, mahsulot bo'yicha like va sharh statistikasi.
- Categories: qo'shish, tahrirlash, o'chirish, subkategoriya va mahsulot soni.
  Mahsuloti yoki subkategoriyasi bor kategoriyani o'chirish bloklanadi (PROTECT).
- Orders: buyurtma holatini admin panelidan ham boshqarish mumkin
  (shipping / completed / cancelled), bekor qilinganda zaxira qaytariladi.
- Customers: ro'yxatda buyurtma soni, sarflangan summa va sharhlar soni ko'rinadi.
- Cart va CartItem, Like, Comment, TempUser/SingUpCode/TempToken: ko'rish va
  tozalash uchun.

FRONTEND (React + TypeScript + Vite)
  cd frontend
  npm install
  npm run dev        # http://localhost:5173
  npm run build      # production build (dist/)
  npm run lint

Frontend /api va /media so'rovlarini Vite proxy orqali 127.0.0.1:8000 ga
yo'naltiradi, shuning uchun backend va frontend alohida ishlashi yetarli.
Boshqa API manzili kerak bo'lsa: VITE_API_BASE_URL (frontend/.env.example).

Frontend sahifalari:
- /            bosh sahifa, kategoriyalar va yangi mahsulotlar
- /shop        katalog: qidiruv, kategoriya, narx, zaxira, saralash, pagination
- /product/:id mahsulot tafsilotlari, like, savatga qo'shish, sharhlar
- /cart        savat, miqdor, yetkazib berish manzili va checkout
- /orders      buyurtma tarixi va holatlari
- /likes       saqlangan mahsulotlar
- /account     profil ma'lumotlari
- /signin, /register  kirish va 3 bosqichli ro'yxatdan o'tish

FRONTEND ADMIN PANEL (/admin)
Kirish uchun role=admin yoki is_staff=True bo'lgan akkaunt kerak
(singin qilgandan keyin "Admin panel" tugmasi paydo bo'ladi).

- /admin              Dashboard: tushum, buyurtmalar, sotilgan birliklar, ombor
  qiymati, mahsulot va mijozlar soni, 14 kunlik savdo grafigi, bestsellerlar,
  top mijozlar, so'nggi buyurtmalar, kam qolgan mahsulotlar, kategoriya
  tushumi.
- /admin/products     Mahsulotlar: qo'shish, tahrirlash, o'chirish, rasm
  yuklash, narx/zaxira, qidiruv va saralash; sotilgan birlik va tushum
  ustunlari. Mahsuloti buyurtma yoki savatda ishlatilgan bo'lsa o'chirish
  bloklanadi.
- /admin/categories   Kategoriyalar: yaratish, tahrirlash, o'chirish, ichki
  kategoriyalar. Mahsuloti yoki subkategoriyasi bo'lsa o'chirish bloklanadi.
- /admin/orders       Barcha buyurtmalar, status bo'yicha filtr, pending ->
  shipping -> completed/cancelled o'tishlari.
- /admin/customers    Mijozlarning ro'yxati (buyurtma soni, sarflangan summa,
  statuslar aralashuvi) va "View" orqali profil ma'lumotlari (ism, email,
  telefon, yosh, holat, ro'yxatdan o'tgan sanasi) va barcha buyurtmalari.

Administratorlar savat va checkout'dan foydalanmaydi: ular mahsulot
qo'shadi/tahrirlaydi va savdo va mijozlarni kuzatadi.

HISOBOT API'SI (faqat admin)
- GET /api/reports/dashboard/     barchagicha statistika bir joyda
- GET /api/reports/sales/         har bir mahsulot bo'yicha sotuvlar
                                  (search, ordering, pagination)
- GET /api/reports/customers/     mijozlarning buyurtma statistikasi
- GET /api/reports/customers/{id}/       mijoz profili
- GET /api/reports/customers/{id}/orders/  mijoz buyurtmalari
