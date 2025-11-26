from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from enum import Enum
import uuid

class ProblemSolution(BaseModel):
    """Решение задачи пользователя"""
    problem_statement: str
    user_solution: str
    correct_solution: str
    evaluation: Dict[str, Any]
    score: float
    feedback: str
    improvements: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
    
class ProblemType(str, Enum):
    THEORETICAL = "theoretical"
    PRACTICAL = "practical"
    CODE = "code"
    QUIZ = "quiz"
    PROJECT = "project"

class ProblemDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class LearningState(BaseModel):
    """Состояние диалога обучения с системой решения задач"""
    
    # Основные поля диалога
    messages: List[BaseMessage] = Field(default_factory=list)
    current_response: str = Field(default="")
    
    # Идентификация пользователя
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Контекст обучения
    current_topic: str = Field(default="")
    learning_goals: List[str] = Field(default_factory=list)
    knowledge_level: str = Field(default="beginner")
    learning_style: str = Field(default="balanced")
    
    # Академический контекст
    subject_area: str = Field(default="")
    difficulty_level: int = Field(default=1, ge=1, le=10)
    conversation_depth: int = Field(default=0)
    
    # Система памяти
    memory_context: Dict[str, Any] = Field(default_factory=dict)
    relevant_memories: List[Dict] = Field(default_factory=list)
    
    # Режимы обучения
    learning_mode: str = Field(default="explanation")
    teaching_strategy: str = Field(default="scaffolding")
    
    # Система решения задач
    current_problem: Optional[Dict] = Field(default=None)
    problem_solutions: List[Dict] = Field(default_factory=list)
    problem_history: List[Dict] = Field(default_factory=list)
    assessment_results: List[Dict] = Field(default_factory=list)
    
    # Прогресс обучения
    skill_matrix: Dict[str, float] = Field(default_factory=dict)
    knowledge_gaps: List[str] = Field(default_factory=list)
    learning_path: List[str] = Field(default_factory=list)
    
    # Флаги состояния
    needs_memory_update: bool = Field(default=False)
    requires_clarification: bool = Field(default=False)
    is_solving_problem: bool = Field(default=False)
    needs_assessment: bool = Field(default=False)
    
    # Метаданные
    timestamp: datetime = Field(default_factory=datetime.now)
    interaction_count: int = Field(default=0)
    problems_solved: int = Field(default=0)
    average_score: float = Field(default=0.0)