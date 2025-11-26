// Главный файл приложения
class LearningCompanionApp {
    constructor() {
        this.uiManager = new UIManager();
        this.initializeApp();
    }

    // Инициализация приложения
    async initializeApp() {
        try {
            // Проверяем доступность API
            await api.healthCheck();
            
            // Обновляем UI с начальными данными
            this.updateInitialUI();
            
            // Загружаем начальную аналитику
            await this.loadInitialAnalytics();
            
            console.log('Learning Companion App initialized successfully');
        } catch (error) {
            console.error('Failed to initialize app:', error);
            this.showError('Не удалось подключиться к серверу. Пожалуйста, проверьте, запущен ли бэкенд.');
        }
    }

    // Обновление начального UI
    updateInitialUI() {
        // Устанавливаем ID пользователя
        document.getElementById('userId').textContent = `ID: ${api.getUserId()}`;
        
        // Увеличиваем счетчик взаимодействий
        const interactionsCount = parseInt(localStorage.getItem('interactions_count') || '0');
        document.getElementById('interactionsCount').textContent = interactionsCount;
    }

    // Загрузка начальной аналитики
    async loadInitialAnalytics() {
        try {
            const analytics = await api.getAnalytics();
            
            // Обновляем статистики
            document.getElementById('interactionsCount').textContent = analytics.total_interactions;
            document.getElementById('problemsSolved').textContent = analytics.problems_solved;
            document.getElementById('averageScore').textContent = analytics.average_score.toFixed(1);
            
            // Сохраняем количество взаимодействий
            localStorage.setItem('interactions_count', analytics.total_interactions);
            
        } catch (error) {
            console.error('Error loading initial analytics:', error);
        }
    }

    // Показать ошибку
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-width: 400px;
        `;
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new LearningCompanionApp();
});

// Глобальные функции для отладки
window.debugAPI = api;
window.debugUI = () => app.uiManager;