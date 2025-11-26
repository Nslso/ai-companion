// Управление пользовательским интерфейсом
class UIManager {
    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendMessageBtn = document.getElementById('sendMessageBtn');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.analyticsModal = document.getElementById('analyticsModal');
        
        this.initializeEventListeners();
        this.autoResizeTextarea();
    }

    // Инициализация обработчиков событий
    initializeEventListeners() {
        // Отправка сообщения
        this.sendMessageBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Быстрые действия
        document.getElementById('generateProblemBtn').addEventListener('click', () => this.generateProblem());
        document.getElementById('showAnalyticsBtn').addEventListener('click', () => this.showAnalytics());
        document.getElementById('clearChatBtn').addEventListener('click', () => this.clearChat());

        // Модальное окно
        document.querySelector('.close-modal').addEventListener('click', () => this.hideAnalytics());
        this.analyticsModal.addEventListener('click', (e) => {
            if (e.target === this.analyticsModal) {
                this.hideAnalytics();
            }
        });

        // Копирование ID пользователя
        document.getElementById('copyUserId').addEventListener('click', () => this.copyUserId());

        // Быстрые предложения
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const message = e.target.getAttribute('data-message');
                this.messageInput.value = message;
                this.sendMessage();
            });
        });
    }

    // Автоматическое изменение размера текстового поля
    autoResizeTextarea() {
        this.messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // Обработка нажатия клавиш
    handleKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    // Отправка сообщения
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Очищаем поле ввода
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';

        // Добавляем сообщение пользователя в чат
        this.addMessage(message, 'user');

        // Показываем индикатор загрузки
        this.showLoading();

        try {
            // Отправляем сообщение на сервер
            const response = await api.sendMessage(message);
            
            // Добавляем ответ ассистента
            this.addMessage(response.response, 'ai', {
                learning_mode: response.learning_mode,
                current_topic: response.current_topic,
                problems_solved: response.problems_solved,
                average_score: response.average_score
            });

            // Обновляем UI с новыми данными
            this.updateUI(response);

        } catch (error) {
            this.addMessage('Извините, произошла ошибка при обработке вашего сообщения. Пожалуйста, попробуйте еще раз.', 'ai');
            console.error('Error sending message:', error);
        } finally {
            this.hideLoading();
        }
    }

    // Добавление сообщения в чат
    addMessage(content, type, metadata = {}) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}-message`;

        const avatarIcon = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon}"></i>
            </div>
            <div class="message-content">
                ${this.formatMessageContent(content, type, metadata)}
            </div>
        `;

        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();

        // Убираем welcome сообщение если оно есть
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }

    // Форматирование содержимого сообщения
    formatMessageContent(content, type, metadata) {
        let formattedContent = content;

        // Форматируем код если он есть
        formattedContent = formattedContent.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        formattedContent = formattedContent.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Добавляем метаданные для AI сообщений
        if (type === 'ai' && metadata.learning_mode) {
            const modeIcons = {
                'explanation': '📚',
                'problem_solving': '🎯',
                'assessment': '📊',
                'feedback': '💡',
                'guidance': '🛠️'
            };

            const icon = modeIcons[metadata.learning_mode] || '🤖';
            
            formattedContent += `
                <div class="message-metadata">
                    <small>Режим: ${icon} ${this.formatLearningMode(metadata.learning_mode)}</small>
                    ${metadata.current_topic ? `<small>Тема: ${metadata.current_topic}</small>` : ''}
                </div>
            `;
        }

        return formattedContent;
    }

    // Форматирование режима обучения
    formatLearningMode(mode) {
        const modeNames = {
            'explanation': 'Объяснение',
            'problem_solving': 'Решение задач',
            'assessment': 'Оценка',
            'feedback': 'Обратная связь',
            'guidance': 'Руководство'
        };
        return modeNames[mode] || mode;
    }

    // Генерация задачи
    async generateProblem() {
        const currentTopic = document.getElementById('currentTopic').textContent;
        const topic = currentTopic !== 'Не выбрана' ? currentTopic : 'программирование';
        
        this.addMessage(`Сгенерируйте задачу по теме: ${topic}`, 'user');
        this.showLoading();

        try {
            const response = await api.generateProblem(topic, 'practical', 'medium');
            this.addMessage(response.problem.problem_statement, 'ai', {
                learning_mode: 'problem_solving',
                current_topic: topic
            });
        } catch (error) {
            this.addMessage('Не удалось сгенерировать задачу. Пожалуйста, попробуйте еще раз.', 'ai');
            console.error('Error generating problem:', error);
        } finally {
            this.hideLoading();
        }
    }

    // Показать аналитику
    async showAnalytics() {
        try {
            const analytics = await api.getAnalytics();
            this.updateAnalyticsModal(analytics);
            this.analyticsModal.style.display = 'block';
        } catch (error) {
            console.error('Error fetching analytics:', error);
            alert('Не удалось загрузить аналитику. Пожалуйста, попробуйте позже.');
        }
    }

    // Скрыть аналитику
    hideAnalytics() {
        this.analyticsModal.style.display = 'none';
    }

    // Обновление модального окна аналитики
    updateAnalyticsModal(analytics) {
        // Общие статистики
        document.getElementById('generalStats').innerHTML = `
            <div class="stat-item">
                <span class="stat-label">Всего взаимодействий:</span>
                <span class="stat-value">${analytics.total_interactions}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Решено задач:</span>
                <span class="stat-value">${analytics.problems_solved}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Средний балл:</span>
                <span class="stat-value">${analytics.average_score.toFixed(1)}%</span>
            </div>
        `;

        // Изученные темы
        const topicsHtml = analytics.topics_covered.length > 0 
            ? analytics.topics_covered.map(topic => 
                `<div class="topic-item">${topic}</div>`
              ).join('')
            : '<p>Темы еще не изучены</p>';

        document.getElementById('topicsList').innerHTML = topicsHtml;

        // Пробелы в знаниях
        const gapsHtml = analytics.knowledge_gaps.length > 0
            ? analytics.knowledge_gaps.map(gap =>
                `<div class="gap-item">${gap}</div>`
              ).join('')
            : '<p>Пробелы не выявлены</p>';

        document.getElementById('knowledgeGaps').innerHTML = gapsHtml;

        // История решений
        const solutions = analytics.progress.skill_progression || [];
        const solutionsHtml = solutions.length > 0
            ? solutions.map((solution, index) => 
                `<div class="solution-item">
                    <strong>Задача ${index + 1}:</strong> ${solution.topic || 'Неизвестно'}
                    <br><small>Оценка: ${solution.score}%</small>
                </div>`
              ).join('')
            : '<p>Решения задач отсутствуют</p>';

        document.getElementById('solutionsHistory').innerHTML = solutionsHtml;
    }

    // Обновление UI
    updateUI(data) {
        // Обновляем ID пользователя
        document.getElementById('userId').textContent = `ID: ${api.getUserId()}`;

        // Обновляем статистики
        if (data.problems_solved !== undefined) {
            document.getElementById('problemsSolved').textContent = data.problems_solved;
        }
        if (data.average_score !== undefined) {
            document.getElementById('averageScore').textContent = data.average_score.toFixed(1);
        }

        // Обновляем контекст
        if (data.current_topic) {
            document.getElementById('currentTopic').textContent = data.current_topic;
        }
        if (data.learning_mode) {
            document.getElementById('learningMode').textContent = this.formatLearningMode(data.learning_mode);
        }
    }

    // Очистка чата
    clearChat() {
        if (confirm('Вы уверены, что хотите очистить историю чата?')) {
            this.messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="message ai-message">
                        <div class="message-avatar">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div class="message-content">
                            <h3>👋 Чат очищен!</h3>
                            <p>Чем могу помочь?</p>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    // Копирование ID пользователя
    copyUserId() {
        navigator.clipboard.writeText(api.getUserId()).then(() => {
            const btn = document.getElementById('copyUserId');
            const originalHtml = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                btn.innerHTML = originalHtml;
            }, 2000);
        });
    }

    // Прокрутка вниз
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    // Показать индикатор загрузки
    showLoading() {
        this.sendMessageBtn.disabled = true;
        this.loadingSpinner.classList.remove('hidden');
    }

    // Скрыть индикатор загрузки
    hideLoading() {
        this.sendMessageBtn.disabled = false;
        this.loadingSpinner.classList.add('hidden');
    }
}