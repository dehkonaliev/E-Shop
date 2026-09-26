# E-Shop frontend

React 19 + TypeScript + Vite. Dizayn warm, editorial uslubda (Anthropic illyustratsiyasiga yaqin): serif sarlavhalar, ivory fon, clay accent, ingichka chegaralar.

## Ishga tushirish

```bash
npm install
npm run dev
```

Frontend `http://localhost:5173` da ishlaydi va `/api` hamda `/media` so'rovlarini
`http://127.0.0.1:8000` ga proxy qiladi, shuning uchun Django backend alohida
ishlayotgan bo'lishi kerak.

Boshqa API manzilini ulash uchun `frontend/.env.example` asosida `.env` fayl
yaratib `VITE_API_BASE_URL` ni to'ldiring.

## Buyruqlar

```bash
npm run dev       # ishlab chiqish serveri (port 5173)
npm run build     # typecheck + production build (dist/)
npm run preview   # build natijasini ko'rish
npm run lint      # oxlint
```

## Tuzilma

```
src/
  api/         endpointlar (lib/api.ts), tiplar (types.ts)
  context/     AuthProvider va CartProvider (JWT holati, savat holati)
  components/  Layout (header/footer), ProductCard, himoyalangan route, UI primitivlari
  components/admin/  admin layout, route guard, umumiy admin UI (panel, modal, jadval)
  pages/       Home, Shop, Product, Cart, Orders, Likes, Account, SignIn, Register
  pages/admin/ Dashboard, Products, Categories, Orders, Customers
  index.css    dizayn tokenlari (rang, tipografiya, radius)
  App.css      komponent va sahifa uslublari
  admin.css    admin panel uslublari
```

## Admin panel

`role=admin` yoki `is_staff=true` bo'lgan akkaunt uchun `/admin`:

- **Dashboard** — tushum, buyurtmalar, sotilgan birliklar, ombor qiymati,
  mahsulot/mijozlar soni, 14 kunlik savdo grafigi, bestsellerlar, top
  mijozlar, kam qolgan mahsulotlar, kategoriya tushumi.
- **Products** — mahsulot qo'shish, tahrirlash, o'chirish, rasm yuklash,
  qidiruv va saralash; sotilgan birlik va tushum ustunlari.
- **Categories** — kategoriya yaratish, tahrirlash, o'chirish, ichki
  kategoriyalar.
- **Orders** — barcha buyurtmalar, status bo'yicha filtr, holat
  o'tishlari (ship / complete / cancel).
- **Customers** — mijozlarning buyurtma statistikasi va "View" orqali
  profil ma'lumotlari hamda barcha buyurtmalari.

Administratorlar uchun savat va checkout yashiriladi: ular mahsulot
qo'shadi va savdo/mijozlarni kuzatadi. Oddiy mijozlar `/admin` ga
kirsa, "Administrator access only" oynasi ko'rinadi.

## Autentifikatsiya

1. `/register` — email yuboriladi, 6 xonali kod so'raladi
2. Kod tasdiqlanadi, activation token beriladi
3. Username/password bilan akkaunt yaratiladi, JWT juftligi saqlanadi

Tokenlar `localStorage` da, `Authorization: Bearer <access>` headeri bilan
yuboriladi. Access token muddati tugaganda refresh token avtomatik
ishlatiladi, sessiya tugasa foydalanuvchi `/signin` ga qaytariladi.
