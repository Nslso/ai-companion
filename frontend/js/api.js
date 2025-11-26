// Конфигурация API
const API_BASE_URL = 'http://localhost:8000';

class LearningCompanionAPI {
    constructor() {
        this.userId = this.getOrCreateUserId();
        this.sessionId = this.generateSessionId();
    }

    // Генерация ID пользователя и сессии
    getOrCreateUserId() {
        let userId = localStorage.getItem('learning_assistant_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('learning_assistant_user_id', userId);
        }
        return userId;
    }

    generateSessionId() {
        return 'session_' + Date.now();
    }

    // Базовый метод для API запросов
    async makeRequest(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            mode: 'cors', // Добавляем режим CORS
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            
            // Более информативное сообщение об ошибке
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                throw new Error('Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен на localhost:8000');
            }
            
            throw error;
        }
    }

    // Отправка сообщения ассистенту
    async sendMessage(message) {
        return this.makeRequest('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                user_id: this.userId,
                session_id: this.sessionId
            })
        });
    }

    // Получение аналитики обучения
    async getAnalytics() {
        return this.makeRequest(`/analytics/${this.userId}`);
    }

    // Генерация задачи
    async generateProblem(topic, problemType = 'theoretical', difficulty = 'easy') {
        return this.makeRequest('/generate_problem', {
            method: 'POST',
            body: JSON.stringify({
                topic: topic,
                problem_type: problemType,
                difficulty: difficulty
            })
        });
    }

    // Проверка здоровья сервиса
    async healthCheck() {
        return this.makeRequest('/health');
    }

    // Обновление ID пользователя
    setUserId(newUserId) {
        this.userId = newUserId;
        localStorage.setItem('learning_assistant_user_id', newUserId);
    }

    // Получение текущего ID пользователя
    getUserId() {
        return this.userId;
    }
}

// Создаем глобальный экземпляр API
const api = new LearningCompanionAPI();