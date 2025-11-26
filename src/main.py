from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

from src.agents.learning_agent import LearningCompanionAgent
from src.utils.visualizer import GraphVisualizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent API",
    description="Персональный учебный ассистент",
    version="1.0.0"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins (в продакшене заменить на конкретные домены)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Глобальный инстанс агента
agent = None

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    learning_mode: str
    current_topic: str
    problems_solved: int = 0
    average_score: float = 0.0

class AnalyticsResponse(BaseModel):
    progress: dict
    topics_covered: List[str]
    total_interactions: int
    problems_solved: int
    average_score: float
    knowledge_gaps: List[str]

class ProblemRequest(BaseModel):
    topic: str
    problem_type: str = "theoretical"
    difficulty: str = "easy"

@app.on_event("startup") # DEPRECATED, надо исправить
async def startup_event():
    """Инициализация агента при запуске"""
    global agent
    try:
        agent = LearningCompanionAgent()
        logger.info("Agent инициализирован")
        
        # Создание визуализации графа при запуске
        from src.graph.learning_graph import LearningGraph
        from src.memory.vector_memory import VectorMemory
        memory = VectorMemory()
        graph = LearningGraph(memory, agent.llm)
        GraphVisualizer.visualize_learning_graph(graph.graph)
        
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Agent API",
        "version": "2.0.0",
        "status": "active",
        "features": [
            "personalized_learning",
            "problem_solving",
            "solution_assessment", 
            "progress_tracking",
            "long_term_memory"
        ]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Эндпоинт для диалога с ассистентом"""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        response = agent.process_message(
            user_message=request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Получение состояния для дополнительной информации
        state = None
        if request.user_id and request.session_id:
            state = agent.get_session_state(request.user_id, request.session_id)
        

        # по хорошему надо вернуть русский эквивалент "unknown"
        return ChatResponse(
            response=response,
            user_id=request.user_id or "unknown",
            session_id=request.session_id or "unknown",
            learning_mode=getattr(state, 'learning_mode', 'unknown') if state else 'unknown',
            current_topic=getattr(state, 'current_topic', 'unknown') if state else 'unknown',
            problems_solved=getattr(state, 'problems_solved', 0) if state else 0,
            average_score=getattr(state, 'average_score', 0.0) if state else 0.0,
            knowledge_level=getattr(state, 'knowledge_level', 'unknown') if state else 'unknown',
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{user_id}")
async def get_analytics(user_id: str):
    """Получение аналитики обучения пользователя"""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        analytics = agent.get_learning_analytics(user_id)
        
        return AnalyticsResponse(
            progress=analytics,
            topics_covered=analytics.get("topics_covered", []),
            total_interactions=analytics.get("total_interactions", 0),
            problems_solved=analytics.get("problems_solved", 0),
            average_score=analytics.get("average_score", 0.0),
            knowledge_gaps=analytics.get("knowledge_gaps", [])
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_problem")
async def generate_problem(request: ProblemRequest):
    """Генерация учебной задачи"""
    try:
        if not agent:
            raise HTTPException(status_code=500, detail="Agent not initialized")
        
        from src.agents.problem_solver import ProblemSolver
        from src.agents.state import ProblemType, ProblemDifficulty
        
        problem_solver = ProblemSolver(agent.llm)
        
        problem = problem_solver.generate_problem(
            topic=request.topic,
            knowledge_level="intermediate",  # Можно адаптировать
            problem_type=ProblemType(request.problem_type),
            difficulty=ProblemDifficulty(request.difficulty)
        )
        
        return {
            "problem": problem,
            "topic": request.topic,
            "problem_type": request.problem_type,
            "difficulty": request.difficulty
        }
        
    except Exception as e:
        logger.error(f"Error generating problem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health chek спам"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "features": [
            "problem_solving",
            "solution_assessment", 
            "progress_tracking",
            "long_term_memory"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )