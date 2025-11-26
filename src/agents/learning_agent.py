import os
from typing import Optional, Dict, Any
import logging
from langchain_gigachat import GigaChat

from src.agents.state import LearningState
from src.memory.vector_memory import VectorMemory
from src.graph.learning_graph import LearningGraph

logger = logging.getLogger(__name__)

class LearningCompanionAgent:
    """Персональный учебный ассистент с долгосрочной памятью"""
    
    def __init__(self, credentials: Optional[str] = None):
        self.credentials = credentials or os.getenv("GIGACHAT_CREDENTIALS")
        self.llm = self._initialize_llm()
        self.memory = VectorMemory()
        self.graph = LearningGraph(self.memory, self.llm)
        self.active_sessions: Dict[str, LearningState] = {}
    
    def _initialize_llm(self) -> GigaChat:
        """Инициализация GigaChat модели"""
        return GigaChat(
            credentials=self.credentials,
            scope=os.getenv("GIGACHAT_SCOPE"),
            verify_ssl_certs=False,
            temperature=0.7,
            model=os.getenv("GIGACHAT_MODEL")
        )
    
    def process_message(self, user_message: str, user_id: str = None, 
                       session_id: str = None) -> str:
        """Обработка сообщения пользователя"""
        
        # Получение или создание состояния сессии
        state = self._get_or_create_state(user_id, session_id)
        
        # Добавление сообщения пользователя
        from langchain_core.messages import HumanMessage
        state.messages.append(HumanMessage(content=user_message))
        
        try:
            # Обработка через граф
            final_state = self.graph.process(state)
            
            # Сохранение обновленного состояния
            session_key = f"{final_state.user_id}_{final_state.session_id}"
            self.active_sessions[session_key] = final_state
            
            logger.info(f"Диалог обработан. Режим: {final_state.learning_mode}")
            return final_state.current_response
            
        except Exception as e:
            logger.error(f"!!! Ошибка обработки диалога: {e}")
            return "Извините, произошла ошибка. Пожалуйста, попробуйте еще раз."
    
    def _get_or_create_state(self, user_id: str = None, session_id: str = None) -> LearningState:
        """Получение или создание состояния сессии"""
        if user_id and session_id:
            session_key = f"{user_id}_{session_id}"
            if session_key in self.active_sessions:
                return self.active_sessions[session_key]
        
        # Создание нового состояния
        return LearningState(
            user_id=user_id or f"user_{len(self.active_sessions) + 1}",
            session_id=session_id or f"session_{len(self.active_sessions) + 1}"
        )
    
    def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Получение аналитики обучения"""
        return self.memory.get_learning_progress(user_id)
    
    def get_session_state(self, user_id: str, session_id: str) -> Optional[LearningState]:
        """Получение состояния сессии"""
        session_key = f"{user_id}_{session_id}"
        return self.active_sessions.get(session_key)