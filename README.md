# Budka Gofrowa Dashboard

Aplikacja webowa do zarządzania budką z goframi - kompletny system sprzedaży, inwentaryzacji i raportowania.

## Funkcjonalności

- 🔐 **Logowanie** - bezpieczny dostęp administratora
- 📊 **Dashboard** - przegląd kluczowych wskaźników
- 🧇 **Produkty** - zarządzanie goframi i ich cenami
- ➕ **Dodatki** - obsługa dodatków z kosztami produkcji
- ☕ **Napoje** - pełne zarządzanie napojami (cena kupna/sprzedaży)
- 🎯 **Kompozycje** - tworzenie zestawów produktów
- 📝 **Notatki** - organizacja pracy zespołu
- 👥 **Pracownicy** - ewidencja zespołu i czasu pracy
- 📈 **Raporty** - dzienne i miesięczne podsumowania
- 🛒 **Zamówienia** - zarządzanie dostawami

## Instalacja lokalna

1. Sklonuj repozytorium
2. Zainstaluj zależności: `pip install -r requirements.txt`
3. Uruchom aplikację: `python app.py`
4. Otwórz w przeglądarce: `http://localhost:5000`

## Logowanie

- **Użytkownik:** admin
- **Hasło:** admin123

## Wdrożenie na Render

1. Utwórz konto na [render.com](https://render.com)
2. Połącz z repozytorium GitHub
3. Wybierz "Web Service"
4. Ustaw:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Wdróż aplikację

## Technologie

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Frontend:** Bootstrap 5, HTML5, JavaScript
- **Baza danych:** SQLite
- **Hosting:** Render (darmowy)

## Struktura projektu

```
budka-gofrowa-dashboard/
├── app.py                 # Główna aplikacja
├── requirements.txt       # Zależności Python
├── templates/            # Szablony HTML
├── static/              # Pliki CSS/JS
├── render.yaml          # Konfiguracja Render
└── README.md           # Ta dokumentacja
```

## Autor

Aplikacja stworzona dla lokalnej budki z goframi z myślą o łatwym zarządzaniu biznesem.
