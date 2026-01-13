// Обновление времени на странице
function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('current-time').textContent = timeString;
}

// Обновление таймеров
function updateTimers() {
    // Обновляем таймеры жизни цветов
    document.querySelectorAll('.life-timer').forEach(timer => {
        const expiresAt = new Date(timer.dataset.expires);
        const now = new Date();

        if (now >= expiresAt) {
            timer.textContent = 'Цветы завяли';
            timer.parentElement.parentElement.parentElement.style.opacity = '0.5';
        } else {
            const diff = expiresAt - now;
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

            if (days > 0) {
                timer.textContent = `${days}д ${hours}ч`;
            } else {
                timer.textContent = `${hours}ч ${minutes}м`;
            }
        }
    });

    // Обновляем таймеры смены воды
    document.querySelectorAll('.water-timer').forEach(timer => {
        const vaseId = timer.id.split('-')[2];
        // Здесь можно добавить AJAX запрос для получения актуального времени
        // или использовать данные с сервера, если они уже есть на странице
    });
}

// Подрезка цветка
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация времени
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);

    // Обновление таймеров каждую минуту
    updateTimers();
    setInterval(updateTimers, 60000);

    // Обработка подрезки цветов
    document.querySelectorAll('.trim-btn').forEach(button => {
        button.addEventListener('click', function() {
            const flowerId = this.dataset.flowerId;
            const vaseId = this.dataset.vaseId;

            fetch('/trim_flower', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    flower_id: flowerId,
                    vase_id: vaseId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Цветок успешно подрезан и поставлен в вазу!');
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    showNotification('Ошибка при подрезке цветка', 'error');
                }
            })
            .catch(error => {
                showNotification('Ошибка соединения', 'error');
            });
        });
    });

    // Обработка смены воды
    document.querySelectorAll('.change-water-btn').forEach(button => {
        button.addEventListener('click', function() {
            const vaseId = this.dataset.vaseId;

            fetch('/change_water', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    vase_id: vaseId
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Вода успешно заменена!');
                    setTimeout(() => {
                        location.reload();
                    }, 1500);
                } else {
                    showNotification('Ошибка при смене воды', 'error');
                }
            })
            .catch(error => {
                showNotification('Ошибка соединения', 'error');
            });
        });
    });

    // Показ уведомлений
    window.showNotification = function(message, type = 'success') {
        const modal = new bootstrap.Modal(document.getElementById('notificationModal'));
        const messageElement = document.getElementById('notificationMessage');

        messageElement.textContent = message;
        messageElement.className = 'modal-body';
        if (type === 'error') {
            messageElement.classList.add('text-danger');
        } else {
            messageElement.classList.add('text-success');
        }

        modal.show();
    };
});