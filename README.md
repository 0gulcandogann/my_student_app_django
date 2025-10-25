# my_student_app_django
a student tracking system with django

# 🧩 my_student_app_django

Django + PostgreSQL tabanlı bir öğrenci yönetim uygulaması.  
Docker ile kolayca çalıştırabilirsiniz.

---

## 🚀 Kurulum

```bash
# .env dosyasını oluştur
cp .env.example .env

# Docker servislerini başlat
docker compose up --build
```

Uygulama:
👉 http://localhost:8000

---

## ⚙️ Servisler

- **web:** Django + Gunicorn  
- **db:** PostgreSQL  

---

## 🧰 Faydalı Komutlar

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose logs -f
```

---

## 🐳 Hızlı Not

İlk çalıştırmada migration hatası alırsanız:
```bash
docker compose exec web python manage.py migrate
```

---

MIT © 2025
