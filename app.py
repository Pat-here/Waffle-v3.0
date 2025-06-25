import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import func
import secrets


app = Flask(__name__)

# KONFIGURACJA BAZY DANYCH
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///waffle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')

db = SQLAlchemy(app)

# Konfiguracja Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Musisz się zalogować, aby uzyskać dostęp do tej strony.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Modele
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Kategoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), nullable=False)
    opis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produkty = db.relationship('Product', backref='kategoria', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), nullable=False)
    cena_sprzedazy = db.Column(db.Float, nullable=False)
    koszt_wykonania = db.Column(db.Float, nullable=False)
    kategoria_id = db.Column(db.Integer, db.ForeignKey('kategoria.id'), nullable=True)
    dostepny = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def marza(self):
        if self.cena_sprzedazy == 0:
            return 0
        return ((self.cena_sprzedazy - self.koszt_wykonania) / self.cena_sprzedazy) * 100

class Dodatek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), nullable=False)
    cena_sprzedazy = db.Column(db.Float, nullable=False)
    koszt_produkcji = db.Column(db.Float, nullable=False, default=0.0)  # Nowe pole
    kategoria = db.Column(db.String(50), default="standard")
    dostepny = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def marza(self):
        if self.cena_sprzedazy == 0:
            return 0
        return ((self.cena_sprzedazy - self.koszt_produkcji) / self.cena_sprzedazy) * 100

class Napoj(db.Model):  # Nowy model
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), nullable=False)
    cena_kupna = db.Column(db.Float, nullable=False)
    cena_sprzedazy = db.Column(db.Float, nullable=False)
    kategoria = db.Column(db.String(50), default="napój")
    dostepny = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def marza(self):
        if self.cena_sprzedazy == 0:
            return 0
        return ((self.cena_sprzedazy - self.cena_kupna) / self.cena_sprzedazy) * 100

class Kompozycja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), nullable=False)
    opis = db.Column(db.Text)
    cena_sprzedazy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skladniki = db.relationship('KomponujacaKompoycja', backref='kompozycja', lazy=True, cascade='all, delete-orphan')

    @property
    def koszt_calkowity(self):
        koszt = 0
        for skladnik in self.skladniki:
            if skladnik.typ == 'produkt':
                produkt = Product.query.get(skladnik.item_id)
                if produkt:
                    koszt += produkt.koszt_wykonania * skladnik.ilosc
            elif skladnik.typ == 'dodatek':
                dodatek = Dodatek.query.get(skladnik.item_id)
                if dodatek:
                    koszt += dodatek.koszt_produkcji * skladnik.ilosc
        return koszt

    @property
    def marza(self):
        if self.cena_sprzedazy == 0:
            return 0
        return ((self.cena_sprzedazy - self.koszt_calkowity) / self.cena_sprzedazy) * 100

class KomponujacaKompoycja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kompozycja_id = db.Column(db.Integer, db.ForeignKey('kompozycja.id'), nullable=False)
    typ = db.Column(db.String(20), nullable=False)  # 'produkt' lub 'dodatek'
    item_id = db.Column(db.Integer, nullable=False)
    ilosc = db.Column(db.Float, default=1.0)

class Notatka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tytul = db.Column(db.String(200), nullable=False)
    tresc = db.Column(db.Text, nullable=False)
    priorytet = db.Column(db.String(20), default='normalny')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Pracownik(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(120))
    stanowisko = db.Column(db.String(100))
    stawka_godzinowa = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    godziny_pracy = db.relationship('GodzinasPracy', backref='pracownik', lazy=True)

class GodzinasPracy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pracownik_id = db.Column(db.Integer, db.ForeignKey('pracownik.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    godzina_rozpoczecia = db.Column(db.Time, nullable=False)
    godzina_zakonczenia = db.Column(db.Time, nullable=False)
    uwagi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RaportDzienny(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, unique=True)
    obroty = db.Column(db.Float, nullable=False)
    koszty = db.Column(db.Float, default=0.0)
    liczba_klientow = db.Column(db.Integer, default=0)
    pogoda = db.Column(db.String(50))
    uwagi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def zysk(self):
        return self.obroty - self.koszty

class Zamowienie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa_dostawcy = db.Column(db.String(200), nullable=False)
    data_zamowienia = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='oczekujące')
    koszt_calkowity = db.Column(db.Float, default=0.0)
    uwagi = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pozycje = db.relationship('PozycjaZamowienia', backref='zamowienie', lazy=True, cascade='all, delete-orphan')

class PozycjaZamowienia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zamowienie_id = db.Column(db.Integer, db.ForeignKey('zamowienie.id'), nullable=False)
    nazwa_produktu = db.Column(db.String(200), nullable=False)
    ilosc = db.Column(db.Float, nullable=False)
    jednostka = db.Column(db.String(20), default='szt')
    cena_jednostkowa = db.Column(db.Float, default=0.0)

    @property
    def koszt_calkowity(self):
        return self.ilosc * self.cena_jednostkowa

# Trasy aplikacji
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło', 'danger')

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Statystyki
    liczba_produktow = Product.query.count()
    liczba_dodatkow = Dodatek.query.count()
    liczba_napojow = Napoj.query.count()
    liczba_kompozycji = Kompozycja.query.count()
    liczba_pracownikow = Pracownik.query.count()
    liczba_notatek = Notatka.query.count()

    # Ostatnie raporty
    ostatnie_raporty = RaportDzienny.query.order_by(RaportDzienny.data.desc()).limit(5).all()

    # Średnia marża produktów
    produkty = Product.query.all()
    if produkty:
        srednia_marza_produktow = sum([p.marza for p in produkty]) / len(produkty)
    else:
        srednia_marza_produktow = 0

    # Średnia marża dodatków
    dodatki = Dodatek.query.all()
    if dodatki:
        srednia_marza_dodatkow = sum([d.marza for d in dodatki]) / len(dodatki)
    else:
        srednia_marza_dodatkow = 0

    # Średnia marża napojów
    napoje = Napoj.query.all()
    if napoje:
        srednia_marza_napojow = sum([n.marza for n in napoje]) / len(napoje)
    else:
        srednia_marza_napojow = 0

    return render_template('dashboard/main.html',
                         liczba_produktow=liczba_produktow,
                         liczba_dodatkow=liczba_dodatkow,
                         liczba_napojow=liczba_napojow,
                         liczba_kompozycji=liczba_kompozycji,
                         liczba_pracownikow=liczba_pracownikow,
                         liczba_notatek=liczba_notatek,
                         ostatnie_raporty=ostatnie_raporty,
                         srednia_marza_produktow=round(srednia_marza_produktow, 2),
                         srednia_marza_dodatkow=round(srednia_marza_dodatkow, 2),
                         srednia_marza_napojow=round(srednia_marza_napojow, 2))

# PRODUKTY
@app.route('/produkty')
@login_required
def lista_produktow():
    produkty = Product.query.all()
    kategorie = Kategoria.query.all()
    return render_template('produkty/lista.html', produkty=produkty, kategorie=kategorie)

@app.route('/produkty/dodaj', methods=['POST'])
@login_required
def dodaj_produkt():
    try:
        nazwa = request.form['nazwa']
        cena_sprzedazy = float(request.form['cena_sprzedazy'])
        koszt_wykonania = float(request.form['koszt_wykonania'])
        kategoria_id = request.form.get('kategoria_id')

        if kategoria_id:
            kategoria_id = int(kategoria_id)
        else:
            kategoria_id = None

        produkt = Product(
            nazwa=nazwa,
            cena_sprzedazy=cena_sprzedazy,
            koszt_wykonania=koszt_wykonania,
            kategoria_id=kategoria_id
        )

        db.session.add(produkt)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Produkt dodany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/produkty/edytuj/<int:id>', methods=['POST'])
@login_required
def edytuj_produkt(id):
    try:
        produkt = Product.query.get_or_404(id)

        produkt.nazwa = request.form['nazwa']
        produkt.cena_sprzedazy = float(request.form['cena_sprzedazy'])
        produkt.koszt_wykonania = float(request.form['koszt_wykonania'])

        kategoria_id = request.form.get('kategoria_id')
        if kategoria_id:
            produkt.kategoria_id = int(kategoria_id)
        else:
            produkt.kategoria_id = None

        db.session.commit()

        return jsonify({'success': True, 'message': 'Produkt zaktualizowany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/produkty/usun/<int:id>', methods=['POST'])
@login_required
def usun_produkt(id):
    try:
        produkt = Product.query.get_or_404(id)
        db.session.delete(produkt)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Produkt usunięty pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# DODATKI
@app.route('/dodatki')
@login_required
def lista_dodatkow():
    dodatki = Dodatek.query.all()
    return render_template('dodatki/lista.html', dodatki=dodatki)

@app.route('/dodatki/dodaj', methods=['POST'])
@login_required
def dodaj_dodatek():
    try:
        nazwa = request.form['nazwa']
        cena_sprzedazy = float(request.form['cena_sprzedazy'])
        koszt_produkcji = float(request.form['koszt_produkcji'])
        kategoria = request.form['kategoria']

        dodatek = Dodatek(
            nazwa=nazwa,
            cena_sprzedazy=cena_sprzedazy,
            koszt_produkcji=koszt_produkcji,
            kategoria=kategoria
        )

        db.session.add(dodatek)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Dodatek dodany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/dodatki/edytuj/<int:id>', methods=['POST'])
@login_required
def edytuj_dodatek(id):
    try:
        dodatek = Dodatek.query.get_or_404(id)

        dodatek.nazwa = request.form['nazwa']
        dodatek.cena_sprzedazy = float(request.form['cena_sprzedazy'])
        dodatek.koszt_produkcji = float(request.form['koszt_produkcji'])
        dodatek.kategoria = request.form['kategoria']

        db.session.commit()

        return jsonify({'success': True, 'message': 'Dodatek zaktualizowany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/dodatki/usun/<int:id>', methods=['POST'])
@login_required
def usun_dodatek(id):
    try:
        dodatek = Dodatek.query.get_or_404(id)
        db.session.delete(dodatek)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Dodatek usunięty pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# NAPOJE
@app.route('/napoje')
@login_required
def lista_napojow():
    napoje = Napoj.query.all()
    return render_template('napoje/lista.html', napoje=napoje)

@app.route('/napoje/dodaj', methods=['POST'])
@login_required
def dodaj_napoj():
    try:
        nazwa = request.form['nazwa']
        cena_kupna = float(request.form['cena_kupna'])
        cena_sprzedazy = float(request.form['cena_sprzedazy'])
        kategoria = request.form['kategoria']

        napoj = Napoj(
            nazwa=nazwa,
            cena_kupna=cena_kupna,
            cena_sprzedazy=cena_sprzedazy,
            kategoria=kategoria
        )

        db.session.add(napoj)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Napój dodany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/napoje/edytuj/<int:id>', methods=['POST'])
@login_required
def edytuj_napoj(id):
    try:
        napoj = Napoj.query.get_or_404(id)

        napoj.nazwa = request.form['nazwa']
        napoj.cena_kupna = float(request.form['cena_kupna'])
        napoj.cena_sprzedazy = float(request.form['cena_sprzedazy'])
        napoj.kategoria = request.form['kategoria']

        db.session.commit()

        return jsonify({'success': True, 'message': 'Napój zaktualizowany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/napoje/usun/<int:id>', methods=['POST'])
@login_required
def usun_napoj(id):
    try:
        napoj = Napoj.query.get_or_404(id)
        db.session.delete(napoj)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Napój usunięty pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# KOMPOZYCJE
@app.route('/kompozycje')
@login_required
def lista_kompozycji():
    kompozycje = Kompozycja.query.all()
    produkty = Product.query.all()
    dodatki = Dodatek.query.all()
    return render_template('kompozycje/lista.html', kompozycje=kompozycje, produkty=produkty, dodatki=dodatki)

# NOTATKI
@app.route('/notatki')
@login_required
def lista_notatek():
    notatki = Notatka.query.order_by(Notatka.created_at.desc()).all()
    return render_template('notatki/lista.html', notatki=notatki)

@app.route('/notatki/dodaj', methods=['POST'])
@login_required
def dodaj_notatke():
    try:
        tytul = request.form['tytul']
        tresc = request.form['tresc']
        priorytet = request.form['priorytet']

        notatka = Notatka(
            tytul=tytul,
            tresc=tresc,
            priorytet=priorytet
        )

        db.session.add(notatka)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Notatka dodana pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# PRACOWNICY
@app.route('/pracownicy')
@login_required
def lista_pracownikow():
    pracownicy = Pracownik.query.all()
    return render_template('pracownicy/lista.html', pracownicy=pracownicy)

@app.route('/pracownicy/dodaj', methods=['POST'])
@login_required
def dodaj_pracownika():
    try:
        imie = request.form['imie']
        nazwisko = request.form['nazwisko']
        telefon = request.form.get('telefon', '')
        email = request.form.get('email', '')
        stanowisko = request.form.get('stanowisko', '')
        stawka_godzinowa = float(request.form.get('stawka_godzinowa', 0))

        pracownik = Pracownik(
            imie=imie,
            nazwisko=nazwisko,
            telefon=telefon,
            email=email,
            stanowisko=stanowisko,
            stawka_godzinowa=stawka_godzinowa
        )

        db.session.add(pracownik)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Pracownik dodany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# RAPORTY
@app.route('/raporty')
@login_required
def lista_raportow():
    raporty = RaportDzienny.query.order_by(RaportDzienny.data.desc()).all()
    return render_template('raporty/lista.html', raporty=raporty)

@app.route('/raporty/dodaj', methods=['POST'])
@login_required
def dodaj_raport():
    try:
        data = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        obroty = float(request.form['obroty'])
        koszty = float(request.form.get('koszty', 0))
        liczba_klientow = int(request.form.get('liczba_klientow', 0))
        pogoda = request.form.get('pogoda', '')
        uwagi = request.form.get('uwagi', '')

        raport = RaportDzienny(
            data=data,
            obroty=obroty,
            koszty=koszty,
            liczba_klientow=liczba_klientow,
            pogoda=pogoda,
            uwagi=uwagi
        )

        db.session.add(raport)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Raport dodany pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# ZAMÓWIENIA
@app.route('/zamowienia')
@login_required
def lista_zamowien():
    zamowienia = Zamowienie.query.order_by(Zamowienie.data_zamowienia.desc()).all()
    return render_template('zamowienia/lista.html', zamowienia=zamowienia)

@app.route('/zamowienia/dodaj', methods=['POST'])
@login_required
def dodaj_zamowienie():
    try:
        nazwa_dostawcy = request.form['nazwa_dostawcy']
        data_zamowienia = datetime.strptime(request.form['data_zamowienia'], '%Y-%m-%d').date()
        uwagi = request.form.get('uwagi', '')

        zamowienie = Zamowienie(
            nazwa_dostawcy=nazwa_dostawcy,
            data_zamowienia=data_zamowienia,
            uwagi=uwagi
        )

        db.session.add(zamowienie)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Zamówienie dodane pomyślnie!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

def init_db():
    """Inicjalizacja bazy danych z domyślnymi danymi"""
    with app.app_context():
        db.create_all()

        # Sprawdź czy istnieje użytkownik admin
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)

        # Dodaj przykładowe kategorie
        if not Kategoria.query.first():
            kategorie = [
                Kategoria(nazwa='Gofry słodkie', opis='Gofry z dodatkami słodkimi'),
                Kategoria(nazwa='Gofry wytrawne', opis='Gofry z dodatkami wytrawnymi'),
                Kategoria(nazwa='Gofry specjalne', opis='Gofry specjalne i sezonowe')
            ]
            for kategoria in kategorie:
                db.session.add(kategoria)

        # Dodaj przykładowe produkty
        if not Product.query.first():
            produkty = [
                Product(nazwa='Gofr klasyczny', cena_sprzedazy=8.0, koszt_wykonania=3.5, kategoria_id=1),
                Product(nazwa='Gofr belgijski', cena_sprzedazy=12.0, koszt_wykonania=5.0, kategoria_id=1),
                Product(nazwa='Gofr wytrawny', cena_sprzedazy=10.0, koszt_wykonania=4.0, kategoria_id=2)
            ]
            for produkt in produkty:
                db.session.add(produkt)

        # Dodaj przykładowe dodatki
        if not Dodatek.query.first():
            dodatki = [
                Dodatek(nazwa='Nutella', cena_sprzedazy=3.0, koszt_produkcji=1.2, kategoria='słodki'),
                Dodatek(nazwa='Owoce sezonowe', cena_sprzedazy=4.0, koszt_produkcji=2.0, kategoria='słodki'),
                Dodatek(nazwa='Ser żółty', cena_sprzedazy=2.5, koszt_produkcji=1.0, kategoria='wytrawny'),
                Dodatek(nazwa='Szynka', cena_sprzedazy=3.5, koszt_produkcji=1.8, kategoria='wytrawny')
            ]
            for dodatek in dodatki:
                db.session.add(dodatek)

        # Dodaj przykładowe napoje
        if not Napoj.query.first():
            napoje = [
                Napoj(nazwa='Kawa czarna', cena_kupna=1.5, cena_sprzedazy=5.0, kategoria='gorące'),
                Napoj(nazwa='Kawa z mlekiem', cena_kupna=2.0, cena_sprzedazy=6.0, kategoria='gorące'),
                Napoj(nazwa='Herbata', cena_kupna=1.0, cena_sprzedazy=4.0, kategoria='gorące'),
                Napoj(nazwa='Coca-Cola 0.33L', cena_kupna=2.5, cena_sprzedazy=5.0, kategoria='zimne'),
                Napoj(nazwa='Woda mineralna 0.5L', cena_kupna=1.0, cena_sprzedazy=3.0, kategoria='zimne'),
                Napoj(nazwa='Sok pomarańczowy', cena_kupna=2.0, cena_sprzedazy=4.5, kategoria='zimne')
            ]
            for napoj in napoje:
                db.session.add(napoj)

        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
