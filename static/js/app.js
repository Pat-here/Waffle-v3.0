// Inicjalizacja aplikacji
document.addEventListener('DOMContentLoaded', function() {
    // Inicjalizacja tooltipów Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicjalizacja popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alertów po 5 sekundach
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

// Funkcja formatowania liczb
function formatCurrency(amount) {
    return new Intl.NumberFormat('pl-PL', {
        style: 'currency',
        currency: 'PLN'
    }).format(amount);
}

// Funkcja sprawdzania połączenia internetowego
function checkConnection() {
    if (!navigator.onLine) {
        showAlert('Brak połączenia z internetem', 'warning');
    }
}

// Funkcja wyświetlania alertów
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-hide po 5 sekundach
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Obsługa błędów fetch
function handleFetchError(error) {
    console.error('Błąd:', error);
    showAlert('Wystąpił błąd połączenia. Sprawdź połączenie internetowe.', 'danger');
}

// Sprawdzanie połączenia przy ładowaniu strony
window.addEventListener('load', checkConnection);
window.addEventListener('online', () => showAlert('Połączenie zostało przywrócone', 'success'));
window.addEventListener('offline', () => showAlert('Utracono połączenie z internetem', 'warning'));