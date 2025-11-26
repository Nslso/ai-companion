from src.agents.learning_agent import LearningCompanionAgent
from src.utils.visualizer import GraphVisualizer
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_enhanced_learning_demo():
    """Демонстрационный сценарий обучения Python с решением задач"""
    
    print("ЗАПУСК ДЕМОНСТРАЦИОННОГО СЦЕНАРИЯ")
    print("Тема: Изучение Python с системой решения и оценки задач")
    print("=" * 70)
    
    # Инициализация агента
    agent = LearningCompanionAgent()
    
    # Демонстрационный диалог с акцентом на решение задач
    demo_dialog = [
        "Привет! Я хочу изучить Python и попрактиковаться в решении задач",
        "Объясни, что такое функции в Python",
        "Дай мне задачу на создание функции",
        "Вот моё решение: def multiply(a, b): return a * b",
        "Сгенерируй задачу посложнее на работу со списками",
        "Покажи похожие задачи, которые я уже решал",
        "Хочу задачу на обработку строк",
        "Моё решение: def count_vowels(text): return sum(1 for char in text if char in 'aeiou')",
        "Какой у меня прогресс в изучении Python?",
        "Давай углубимся в тему классов и ООП"
    ]
    
    user_id = "demo_user_enhanced"
    session_id = "python_course_with_problems"
    
    print("Начало обучения с системой решения задач...\n")
    
    for i, message in enumerate(demo_dialog, 1):
        print(f"Студент [Шаг {i}/10]: {message}")
        
        response = agent.process_message(
            user_message=message,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"Ассистент: {response}")
        
        # Получение текущего состояния для анализа
        state = agent.get_session_state(user_id, session_id)
        if state:
            mode_info = f"режим={state.learning_mode}"
            if state.current_problem:
                mode_info += f", задача={state.current_problem.get('problem_type', 'N/A')}"
            if state.problems_solved > 0:
                mode_info += f", решено={state.problems_solved}, средний балл={state.average_score:.1f}"
            
            print(f"   📊 Контекст: {mode_info}")
        
        print("-" * 80)
        time.sleep(2)
    
    # Расширенная аналитика прогресса
    analytics = agent.get_learning_analytics(user_id)
    print("\n РАСШИРЕННАЯ АНАЛИТИКА ОБУЧЕНИЯ:")
    print(f"Изученные темы: {', '.join(analytics.get('topics_covered', []))}")
    print(f"Всего взаимодействий: {analytics.get('total_interactions', 0)}")
    print(f"Решено задач: {analytics.get('problems_solved', 0)}")
    print(f"Средний балл за задачи: {analytics.get('average_score', 0):.1f}/100")
    print(f"Средний уровень понимания: {analytics.get('average_understanding', 0):.1f}/5.0")
    print(f"Выявленные пробелы: {', '.join(analytics.get('knowledge_gaps', []))}")
    
    # Визуализация графа
    print("\n Визуализация архитектуры...")
    GraphVisualizer.print_enhanced_graph_structure()
    
    return agent

if __name__ == "__main__":
    run_enhanced_learning_demo()