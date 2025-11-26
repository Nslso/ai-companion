from langgraph.graph import StateGraph, END
from typing import Dict, Any, List
import logging
from src.agents.state import LearningState
from src.memory.vector_memory import VectorMemory
from src.agents.problem_solver import ProblemSolver
import json
import re

logger = logging.getLogger(__name__)

class LearningGraph:
    """Граф обработки диалога обучения"""
    
    def __init__(self, memory: VectorMemory, llm):
        self.memory = memory
        self.llm = llm
        self.problem_solver = ProblemSolver(llm)
        self.graph = self._build_graph()
        
        # Создаем LCEL цепочки
        self._create_lcel_chains()
    
    def _create_lcel_chains(self):
        """Создание LCEL цепочек для различных задач"""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
        
        # Парсер для JSON ответов
        self.json_parser = JsonOutputParser()
        
        # 1. Цепочка для анализа контекста
        self.analysis_chain = (
            ChatPromptTemplate.from_template("""
            Ты - опытный преподаватель-аналитик. Проанализируй сообщение студента и определи:

            1. ОСНОВНАЯ ТЕМА: Какая учебная тема обсуждается?
            2. УРОВЕНЬ ЗНАНИЙ: beginner (новичок), intermediate (средний), advanced (продвинутый)
            3. СТИЛЬ ОБУЧЕНИЯ: visual, auditory, reading_writing, kinesthetic, balanced
            4. ЦЕЛЬ ЗАПРОСА: explanation, example, practice, deep_dive, assessment, connection
            5. СЛОЖНОСТЬ: число от 1 до 10
            6. ЭМОЦИОНАЛЬНЫЙ ТОН: confused, curious, confident, frustrated

            Если параметры невозможно определить из контекста, предлоджи наименьшие.
                                             
            Сообщение: "{message}"

            Ответ в формате JSON:
            {{
                "topic": "конкретная тема",
                "knowledge_level": "beginner/intermediate/advanced",
                "learning_style": "visual/auditory/reading_writing/kinesthetic/balanced",
                "learning_goal": "explanation/example/practice/deep_dive/assessment/connection",
                "difficulty_level": 1,
                "emotional_tone": "confused/curious/confident/frustrated",
                "requires_clarification": true/false
            }}
            """)
            | self.llm
            | StrOutputParser()
        )
        
        # 2. Цепочка для выбора режима обучения
        self.mode_selection_chain = (
            ChatPromptTemplate.from_template("""
            На основе контекста выбери оптимальный режим обучения:

            Тема: {topic}
            Уровень знаний: {knowledge_level}
            Стиль обучения: {learning_style}
            Глубина обсуждения: {conversation_depth}
            Релевантные воспоминания: {relevant_memories}

            Доступные режимы:
            - explanation: Объяснение концепций с нуля
            - deepen: Углубленное изучение темы  
            - practice: Практические примеры и упражнения
            - review: Повторение и закрепление
            - challenge: Сложные задачи и вызовы
            - connect: Связывание с предыдущими знаниями

            Выбери один режим и кратко обоснуй выбор.
            Формат: Режим: [режим]
            """)
            | self.llm
            | StrOutputParser()
        )
        
        # 3. Цепочка для генерации ответа
        self.response_generation_chain = (
            ChatPromptTemplate.from_template("""
            Ты - персональный учебный ассистент. Сгенерируй ответ, используя контекст:

            СООБЩЕНИЕ СТУДЕНТА: {message}

            КОНТЕКСТ ОБУЧЕНИЯ:
            - Тема: {topic}
            - Уровень студента: {knowledge_level}
            - Стиль обучения: {learning_style}
            - Режим обучения: {learning_mode}
            - Сложность: {difficulty_level}

            РЕЛЕВАНТНАЯ ИСТОРИЯ:
            {relevant_memories}

            ПРОГРЕСС ОБУЧЕНИЯ:
            {learning_progress}

            СГЕНЕРИРУЙ ОТВЕТ, КОТОРЫЙ:
            - Соответствует уровню знаний студента ({knowledge_level})
            - Использует выбранный режим обучения ({learning_mode})
            - Учитывает стиль обучения ({learning_style})
            - Связывает с предыдущими знаниями при наличии
            - Поддерживает и мотивирует студента
            - Предлагает следующий шаг в обучении

            Будь точным, поддерживающим и педагогически эффективным.
            Ответ должен быть на русском языке.
            """)
            | self.llm
            | StrOutputParser()
        )
    
    def _build_graph(self) -> StateGraph:
        """Построение графа обработки"""
        workflow = StateGraph(LearningState)
        
        # Добавление узлов
        workflow.add_node("analyze_context", self.analyze_context)
        workflow.add_node("retrieve_memory", self.retrieve_memory)
        workflow.add_node("select_mode", self.select_mode)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("update_memory", self.update_memory)
        
        # Определение потока выполнения
        workflow.set_entry_point("analyze_context")
        workflow.add_edge("analyze_context", "retrieve_memory")
        workflow.add_edge("retrieve_memory", "select_mode")
        workflow.add_edge("select_mode", "generate_response")
        workflow.add_edge("generate_response", "update_memory")
        workflow.add_edge("update_memory", END)

        app = workflow.compile()

        mermaid_syntax = app.get_graph().draw_mermaid()

        print("--------- mermaid_syntax --------")
        print(mermaid_syntax)

        return app
    
    def analyze_context(self, state: LearningState) -> Dict[str, Any]:
        """Анализ контекста диалога"""
        logger.info("Анализирую контекст обучения...")
        
        if not state.messages:
            return state.model_dump()
        
        last_message = state.messages[-1]
        
        try:
            # Используем LCEL цепочку для анализа
            analysis_result = self.analysis_chain.invoke({
                "message": last_message.content
            })

            print("-----analysis_result-------")
            print(analysis_result)
            
            # Парсинг JSON ответа
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)

            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                analysis_data = self._parse_analysis_fallback(analysis_result)
            

            updates = {
                "current_topic": analysis_data.get("topic", ""),
                "knowledge_level": analysis_data.get("knowledge_level", "beginner"),
                "learning_style": analysis_data.get("learning_style", "balanced"),
                "difficulty_level": analysis_data.get("difficulty_level", 3),
                "requires_clarification": analysis_data.get("requires_clarification", False)
            }
            
            logger.info(f"Результат анализа: {updates}")
            return {**state.model_dump(), **updates}
            
        except Exception as e:
            logger.error(f"Ошибка анализа контекста: {e}")
            return state.model_dump()
    
    def _parse_analysis_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback парсинг анализа контекста"""
        result = {}
        lines = text.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip().lower()
                
                if 'topic' in key:
                    result['topic'] = value
                elif 'level' in key:
                    result['knowledge_level'] = value
                elif 'style' in key:
                    result['learning_style'] = value
                elif 'goal' in key:
                    result['learning_goal'] = value
                elif 'difficulty' in key:
                    try:
                        result['difficulty_level'] = int(value)
                    except:
                        result['difficulty_level'] = 3
        
        return result
    
    def retrieve_memory(self, state: LearningState) -> Dict[str, Any]:
        """Поиск релевантных воспоминаний с RAG"""
        logger.info("Ищем релевантные воспоминания...")
        
        if not state.messages:
            return state.model_dump()
        
        last_message = state.messages[-1].content
        user_id = state.user_id
        
        print("------last_message--------")
        print(last_message)

        try:
            # Поиск в долгосрочной памяти
            relevant_memories = self.memory.retrieve_relevant_memories(
                user_id=user_id,
                query=last_message,
                n_results=15
            )

            # Получение прогресса обучения
            learning_progress = self.memory.get_learning_progress(user_id)
            
            memory_context = {
                "relevant_memories": relevant_memories,
                "learning_progress": learning_progress,
                "previous_topics": learning_progress.get("topics_covered", [])
            }
            
            # print("-------memory_context---------")
            # print(memory_context)

            logger.info(f"📚 Найдено воспоминаний: {len(relevant_memories)}")
            return {**state.model_dump(), "memory_context": memory_context}
            
        except Exception as e:
            logger.error(f"Ошибка поиска в памяти: {e}")
            return state.model_dump()
    
    def select_mode(self, state: LearningState) -> Dict[str, Any]:
        """Выбор режима обучения на основе контекста с использованием LCEL"""
        logger.info("Выбираю режим обучения...")
        
        try:
            # Подготавливаем данные для цепочки
            chain_input = {
                "topic": state.current_topic,
                "knowledge_level": state.knowledge_level,
                "learning_style": state.learning_style,
                "conversation_depth": state.conversation_depth,
                "relevant_memories": self._format_memories_for_prompt(
                    state.memory_context.get("relevant_memories", [])
                )
            }
            
            # Используем LCEL цепочку для выбора режима
            mode_result = self.mode_selection_chain.invoke(chain_input)
            
            # Определение режима обучения
            learning_mode = "explanation"  # режим по умолчанию
            if "Режим:" in mode_result:
                learning_mode = mode_result.split("Режим:")[1].strip().split()[0].lower()
            
            logger.info(f"Выбран режим: {learning_mode}")
            return {**state.model_dump(), "learning_mode": learning_mode}
            
        except Exception as e:
            logger.error(f"Ошибка выбора режима: {e}")
            return {**state.model_dump(), "learning_mode": "explanation"}
    
    def generate_response(self, state: LearningState) -> Dict[str, Any]:
        """Генерация адаптированного ответа с использованием LCEL"""
        logger.info("Генерирую обучающий ответ...")
        
        if not state.messages:
            return {
                **state.model_dump(), 
                "current_response": "Привет! Я ваш персональный учебный ассистент. Готов помочь с обучением и решением задач!"
            }
        
        last_message = state.messages[-1]
        
        try:
            # Подготавливаем данные для цепочки генерации ответа
            chain_input = {
                "message": last_message.content,
                "topic": state.current_topic,
                "knowledge_level": state.knowledge_level,
                "learning_style": state.learning_style,
                "learning_mode": getattr(state, 'learning_mode', 'explanation'),
                "difficulty_level": getattr(state, 'difficulty_level', 3),
                "relevant_memories": self._format_memories_for_prompt(
                    state.memory_context.get("relevant_memories", [])
                ),
                "learning_progress": self._format_progress_for_prompt(
                    state.memory_context.get("learning_progress", {})
                )
            }
            
            # Используем LCEL цепочку для генерации ответа
            response = self.response_generation_chain.invoke(chain_input)
            
            logger.info("Ответ сгенерирован успешно")
            return {
                **state.model_dump(), 
                "current_response": response,
                "needs_memory_update": True,
                "interaction_count": state.interaction_count + 1
            }
            
        except Exception as e:
            logger.error(f"Ошибка генерации ответа: {e}")
            return {
                **state.model_dump(),
                "current_response": "Извините, возникла ошибка обработки. Можете переформулировать вопрос?",
                "needs_memory_update": False
            }
    
    def update_memory(self, state: LearningState) -> Dict[str, Any]:
        """Обновление долгосрочной памяти"""
        logger.info("Обновляю память...")
        
        if state.needs_memory_update and state.messages:
            try:
                last_message = state.messages[-1]
                
                # Сохранение взаимодействия
                self.memory.store_interaction(
                    user_id=state.user_id,
                    session_id=state.session_id,
                    message=last_message,
                    topic=state.current_topic,
                    knowledge_level=state.knowledge_level,
                    learning_style=state.learning_style,
                    metadata={
                        "learning_mode": state.learning_mode,
                        "difficulty_level": state.difficulty_level,
                        "interaction_count": state.interaction_count,
                        "teaching_strategy": getattr(state, 'teaching_strategy', '')
                    }
                )
                
                logger.info("Память успешно обновлена")
                
            except Exception as e:
                logger.error(f"Ошибка обновления памяти: {e}")
        
        return {**state.model_dump(), "needs_memory_update": False}
    
    def _format_memories_for_prompt(self, memories: List[Dict]) -> str:
        """Форматирование воспоминаний для промпта"""
        if not memories:
            return "Нет релевантных воспоминаний"
        
        print("Воспоминания ...")
        print(memories)

        formatted = []
        for i, memory in enumerate(memories[:5], 1):  # Берем только 5 самых релевантных
            content = memory.get('content', '')[:300]  # Обрезаем длинный текст
            score = memory.get('relevance_score', 0)
            formatted.append(f"{i}. {content} (релевантность: {score:.2f})")
        
        return "\n".join(formatted)
    
    def _format_progress_for_prompt(self, progress: Dict) -> str:
        """Форматирование прогресса для промпта"""
        if not progress:
            return "Прогресс обучения отсутствует"
        
        topics = progress.get("topics_covered", [])
        interactions = progress.get("total_interactions", 0)
        problems_solved = progress.get("problems_solved", 0)
        avg_score = progress.get("average_score", 0)
        
        print("--------progress--------")
        print(progress)

        return f"""
        Изученные темы: {', '.join(topics[:5])}{'...' if len(topics) > 5 else ''}
        Всего взаимодействий: {interactions}
        Решено задач: {problems_solved}
        Средний балл: {avg_score}
        """
    
    def process(self, state: LearningState) -> LearningState:
        """Обработка состояния через граф"""
        result = self.graph.invoke(state)
        return LearningState(**result)