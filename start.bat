@echo off
title Budka z Goframi - Dashboard
color 0A

echo ========================================
echo    BUDKA Z GOFRAMI - DASHBOARD
echo         Uruchamianie aplikacji...
echo ========================================
echo.

:: Sprawdzenie czy Python jest zainstalowany
python --version >nul 2>&1
if errorlevel 1 (
    echo [BŁĄD] Python nie został znaleziony w systemie!
    echo Proszę zainstalować Python z https://python.org
    pause
    exit /b 1
)

echo [OK] Python znaleziony
echo.

:: Tworzenie wirtualnego środowiska jeśli nie istnieje
if not exist "venv" (
    echo [INFO] Tworzenie wirtualnego środowiska...
    python -m venv venv
    if errorlevel 1 (
        echo [BŁĄD] Nie można utworzyć wirtualnego środowiska!
        pause
        exit /b 1
    )
    echo [OK] Wirtualne środowisko utworzone
) else (
    echo [OK] Wirtualne środowisko już istnieje
)
echo.

:: Aktywacja wirtualnego środowiska
echo [INFO] Aktywacja wirtualnego środowiska...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [BŁĄD] Nie można aktywować wirtualnego środowiska!
    pause
    exit /b 1
)

:: Instalacja zależności
echo [INFO] Instalacja/aktualizacja zależności...
pip install -r requirements.txt
if errorlevel 1 (
    echo [BŁĄD] Nie można zainstalować zależności!
    pause
    exit /b 1
)
echo [OK] Zależności zainstalowane
echo.

:: Inicjalizacja bazy danych jeśli nie istnieje
if not exist "instance\database.db" (
    echo [INFO] Inicjalizacja bazy danych...
    python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Baza danych zainicjalizowana')"
    echo [OK] Baza danych utworzona
) else (
    echo [OK] Baza danych już istnieje
)
echo.

:: Ustawienie zmiennych środowiskowych
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo [INFO] Uruchamianie aplikacji Flask...
echo.
echo ========================================
echo  Aplikacja uruchomiona na:
echo  http://localhost:5000
echo  
echo  Dane logowania:
echo  Login: admin
echo  Hasło: admin123
echo ========================================
echo.
echo Naciśnij Ctrl+C aby zatrzymać serwer
echo.

:: Uruchomienie aplikacji
python app.py

:: Pauza po zakończeniu
echo.
echo [INFO] Aplikacja została zatrzymana
pause