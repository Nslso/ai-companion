from typing import Dict, List, Any
import json
import re
import logging
from src.agents.state import ProblemType, ProblemDifficulty, ProblemSolution
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class ProblemSolver:
    """Система решения и оценки учебных задач с использованием LCEL"""
    
    def __init__(self, llm):
        self.llm = llm
        self._create_lcel_chains()
    
    def _create_lcel_chains(self):
        """Создание LCEL цепочек для решения задач"""
        
        # Цепочка для генерации задач
        self.problem_generation_chain = (
            ChatPromptTemplate.from_template("""
            Сгенерируй учебную задачу по теме "{topic}" для уровня {knowledge_level}.
            
            Тип задачи: {problem_type}
            Сложность: {difficulty}
            
            Требования к задаче:
            1. Должна соответствовать уровню знаний
            2. Должна проверять ключевые концепции темы
            3. Должна иметь четкое решение
            4. Должна развивать практические навыки
            
            Формат ответа:
            {{
                "problem_statement": "четкая формулировка задачи",
                "problem_type": "{problem_type}",
                "difficulty": "{difficulty}",
                "expected_skills": ["список", "проверяемых", "навыков"],
                "hints": ["подсказка 1", "подсказка 2"],
                "solution_steps": ["шаг 1", "шаг 2", "шаг 3"],
                "evaluation_criteria": {{
                    "критерий 1": "описание",
                    "критерий 2": "описание"
                }}
            }}
            """)
            | self.llm
            | StrOutputParser()
        )
        
        # Цепочка для оценки решений
        self.solution_evaluation_chain = (
            ChatPromptTemplate.from_template("""
            Оцени решение пользователя учебной задачи.
            
            Тема: {topic}
            Уровень знаний: {knowledge_level}
            
            ЗАДАЧА:
            {problem_statement}
            
            ТИП ЗАДАЧИ: {problem_type}
            КРИТЕРИИ ОЦЕНКИ: {evaluation_criteria}
            
            РЕШЕНИЕ ПОЛЬЗОВАТЕЛЯ:
            {user_solution}
            
            Проведи оценку по следующим аспектам:
            1. Правильность решения
            2. Полнота ответа
            3. Логичность изложения
            4. Соответствие критериям
            5. Качество примеров (если применимо)
            6. Техническая корректность (для кода)
            
            Сгенерируй:
            - Оценку от 0 до 100
            - Подробный фидбэк
            - Конкретные улучшения
            - Правильное решение (если нужно)
            
            Формат ответа:
            {{
                "score": число от 0 до 100,
                "feedback": "развернутый фидбэк",
                "improvements": ["улучшение 1", "улучшение 2"],
                "correct_solution": "правильное решение",
                "strengths": ["сильная сторона 1", "сильная сторона 2"],
                "weaknesses": ["слабая сторона 1", "слабая сторона 2"]
            }}
            """)
            | self.llm
            | StrOutputParser()
        )
        
        # Цепочка для подсказок
        self.hint_generation_chain = (
            ChatPromptTemplate.from_template("""
            Предоставь подсказку для решения задачи. Пользователь испытывает трудности: {user_stuck}
            
            Задача: {problem_statement}
            Доступные подсказки: {available_hints}
            
            Сгенерируй полезную подсказку, которая:
            - Не раскрывает решение полностью
            - Направляет мысль в правильное русло
            - Учитывает возможные трудности
            - Мотивирует продолжать решение
            
            Подсказка должна быть краткой и конкретной.
            """)
            | self.llm
            | StrOutputParser()
        )
    
    def generate_problem(self, topic: str, knowledge_level: str, 
                        problem_type: ProblemType, 
                        difficulty: ProblemDifficulty) -> Dict[str, Any]:
        """Генерация учебной задачи с использованием LCEL"""
        
        try:
            chain_input = {
                "topic": topic,
                "knowledge_level": knowledge_level,
                "problem_type": problem_type.value,
                "difficulty": difficulty.value
            }
            
            problem_result = self.problem_generation_chain.invoke(chain_input)
            
            # Парсинг JSON ответа
            json_match = re.search(r'\{.*\}', problem_result, re.DOTALL)
            if json_match:
                problem_data = json.loads(json_match.group())
                logger.info(f"Сгенерирована задача по теме: {topic}")
                return problem_data
            else:
                raise ValueError("Не удалось распарсить JSON ответ")
                
        except Exception as e:
            logger.error(f"Ошибка генерации задачи: {e}")
            return self._get_fallback_problem(topic, knowledge_level)
    
    def evaluate_solution(self, problem: Dict, user_solution: str, 
                         topic: str, knowledge_level: str) -> ProblemSolution:
        """Оценка решения пользователя с использованием LCEL"""
        
        try:
            chain_input = {
                "topic": topic,
                "knowledge_level": knowledge_level,
                "problem_statement": problem.get('problem_statement', ''),
                "problem_type": problem.get('problem_type', ''),
                "evaluation_criteria": problem.get('evaluation_criteria', {}),
                "user_solution": user_solution
            }
            
            evaluation_result = self.solution_evaluation_chain.invoke(chain_input)
            
            print("Оценка решения ...")
            print(evaluation_result)

            # Парсинг JSON ответа
            json_match = re.search(r'\{.*\}', evaluation_result, re.DOTALL)
            if json_match:
                evaluation_data = json.loads(json_match.group())
            else:
                evaluation_data = self._get_fallback_evaluation_data()
            
            solution = ProblemSolution(
                problem_statement=problem['problem_statement'],
                user_solution=user_solution,
                correct_solution=evaluation_data.get('correct_solution', ''),
                evaluation=evaluation_data,
                score=evaluation_data.get('score', 0),
                feedback=evaluation_data.get('feedback', ''),
                improvements=evaluation_data.get('improvements', [])
            )
            
            logger.info(f"Оценка решения: {solution.score}/100")
            return solution
            
        except Exception as e:
            logger.error(f"Ошибка оценки решения: {e}")
            return self._get_fallback_evaluation(problem, user_solution)
    
    def provide_hint(self, problem: Dict, user_stuck: bool = False) -> str:
        """Предоставление подсказки с использованием LCEL"""
        
        try:
            chain_input = {
                "user_stuck": user_stuck,
                "problem_statement": problem.get('problem_statement', ''),
                "available_hints": problem.get('hints', [])
            }
            
            hint = self.hint_generation_chain.invoke(chain_input)
            return hint
            
        except Exception as e:
            logger.error(f"!!! Ошибка генерации подсказки: {e}")
            return "Попробуйте разбить задачу на более мелкие шаги и решать их последовательно."
    
    def _get_fallback_problem(self, topic: str) -> Dict[str, Any]:
        """Резервная задача при ошибке генерации"""
        return {
            "problem_statement": f"Объясните основные концепции темы '{topic}' своими словами",
            "problem_type": "theoretical",
            "difficulty": "easy",
            "expected_skills": ["понимание", "объяснение"],
            "hints": ["Начните с определения ключевых терминов", "Приведите примеры"],
            "solution_steps": ["Определить ключевые понятия", "Объяснить взаимосвязи", "Привести примеры"],
            "evaluation_criteria": {
                "полнота": "раскрыты все основные аспекты",
                "ясность": "объяснение понятно и логично",
                "примеры": "приведены релевантные примеры"
            }
        }
    
    def _get_fallback_evaluation(self, problem: Dict, user_solution: str) -> ProblemSolution:
        """Резервная оценка при ошибке"""
        return ProblemSolution(
            problem_statement=problem['problem_statement'],
            user_solution=user_solution,
            correct_solution="Не удалось сгенерировать правильное решение",
            evaluation={},
            score=50,
            feedback="Не удалось провести полноценную оценку. Пожалуйста, попробуйте еще раз.",
            improvements=["Уточните формулировку решения", "Добавьте больше деталей"]
        )
    
    def _get_fallback_evaluation_data(self) -> Dict[str, Any]:
        """Резервные данные оценки"""
        return {
            "score": 50,
            "feedback": "Не удалось провести полноценную оценку",
            "improvements": ["Уточните решение", "Добавьте детали"],
            "correct_solution": "Решение недоступно",
            "strengths": [],
            "weaknesses": []
        }
    
    def analyze_knowledge_gaps(self, solutions: List[ProblemSolution]) -> List[str]:
        """Анализ пробелов в знаниях на основе решений"""
        
        if not solutions:
            return ["базовые концепции", "фундаментальные принципы"]
        
        # Анализируем решения с низким баллом
        low_score_solutions = [s for s in solutions if s.score < 60]
        
        if len(low_score_solutions) > len(solutions) * 0.5:
            return ["применение теории на практике", "глубокое понимание концепций"]
        else:
            return ["продвинутые аспекты темы", "связывание различных концепций"]