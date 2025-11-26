import chromadb
from datetime import datetime
from typing import List, Dict, Any
import uuid
import logging
import os
from src.memory.embedding_function import GigaChatEmbeddingFunction;
# import numpy as np
# from langchain_gigachat.embeddings import GigaChatEmbeddings

logger = logging.getLogger(__name__)

class VectorMemory:
    """Система долгосрочной памяти с ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):

        self.persist_directory = persist_directory
        # Инициализация Chroma
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        
        #Инициализация embeddings
        self.embeddings = GigaChatEmbeddingFunction()
        
        # Создание коллекций
        self._initialize_collections()

    
    def _initialize_collections(self):
        """Инициализация коллекций Chroma"""

        self.interaction_collection = self.chroma_client.get_or_create_collection(
            name="interaction_memory",
            metadata={"description": "Память для взаимодействия с пользователем"},
            embedding_function=self.embeddings
        )
        
        self.knowledge_collection = self.chroma_client.get_or_create_collection(
            name="knowledge_memory", 
            metadata={"description": "Память для хранения информации о состоянии пользователя"},
            embedding_function=self.embeddings
        )
        
        self.solutions_collection = self.chroma_client.get_or_create_collection(
            name="solutions_memory",
            metadata={"description": "Память для решения задач"},
            embedding_function=self.embeddings
        )
        
        self.problems_collection = self.chroma_client.get_or_create_collection(
            name="problems_memory",
            metadata={"description": "Память для проблем с обучением"},
            embedding_function=self.embeddings
        )
    
    def store_interaction(self, user_id: str, session_id: str, message: Any, 
                         topic: str, knowledge_level: str, learning_style: str,
                         metadata: Dict[str, Any]) -> str:
        """Сохранение взаимодействия в память"""
        content = message.content if hasattr(message, 'content') else str(message)
        interaction_id = f"{user_id}_{datetime.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        print("-------Контент Сохранение взаимодействия----------")
        print(content)

        # print("-------interaction_id Сохранение взаимодействия----------")
        # print(interaction_id)

        # Создание embedding
        embedding = self.embeddings.embed_query(content)

        # Сохранение в Chroma
        self.interaction_collection.add(
            ids=[interaction_id],
            embeddings=[embedding[0]],
            documents=[content],
            metadatas=[{
                "user_id": user_id,
                "session_id": session_id,
                "topic": topic,
                "knowledge_level": knowledge_level,
                "learning_style": learning_style,
                "timestamp": datetime.now().isoformat(),
                "message_type": type(message).__name__,
                "memory_type": "interaction",
                **metadata
            }]
        )
        
        return interaction_id
    
    def retrieve_relevant_memories(self, user_id: str, query: str, 
                                 n_results: int = 15) -> List[Dict]:
        """Поиск релевантных воспоминаний с RAG"""
        
        # print("-------Поиск в Chroma---------")
        # print(user_id)
        # print(query)
        
        # Поиск в Chroma
        results = self.interaction_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"user_id": user_id}
        )
        
        # print("-------Поиск в Chroma-results--------")
        # print(results)

        memories = []
        if results['documents']:
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                memories.append({
                    "content": doc,
                    "metadata": metadata,
                    "relevance_score": 1 - distance,
                    "memory_type": metadata.get("memory_type", "interaction")
                })
        
        return memories
    
    def store_solution(self, user_id: str, solution: Dict) -> str:
        """Сохранение решения задачи"""
        solution_id = f"solution_{user_id}_{uuid.uuid4().hex[:8]}"
        
        solution_text = f"""
        Задача: {solution.get('problem_statement', '')}
        Решение: {solution.get('user_solution', '')}
        Оценка: {solution.get('score', 0)}/100
        Тема: {solution.get('topic', '')}
        """
        
        embedding = self.embeddings.embed_query(solution_text)
        
        self.solutions_collection.add(
            ids=[solution_id],
            embeddings=[embedding],
            documents=[solution_text],
            metadatas=[{
                "user_id": user_id,
                "problem_type": solution.get('problem_type', ''),
                "difficulty": solution.get('difficulty', 'easy'),
                "score": solution.get('score', 0),
                "topic": solution.get('topic', ''),
                "timestamp": datetime.now().isoformat(),
                "memory_type": "solution"
            }]
        )
        
        return solution_id
    
    def store_problem(self, user_id: str, problem: Dict) -> str:
        """Сохранение учебной задачи"""
        problem_id = f"problem_{user_id}_{uuid.uuid4().hex[:8]}"
        
        problem_text = f"""
        Задача: {problem.get('problem_statement', '')}
        Тип: {problem.get('problem_type', '')}
        Сложность: {problem.get('difficulty', 'easy')}
        Тема: {problem.get('topic', '')}
        """
        
        embedding = self.embeddings.embed_query(problem_text)
        
        self.problems_collection.add(
            ids=[problem_id],
            embeddings=[embedding],
            documents=[problem_text],
            metadatas=[{
                "user_id": user_id,
                "problem_type": problem.get('problem_type', ''),
                "difficulty": problem.get('difficulty', 'easy'),
                "topic": problem.get('topic', ''),
                "timestamp": datetime.now().isoformat(),
                "memory_type": "problem"
            }]
        )
        
        return problem_id
    
    def retrieve_similar_problems(self, user_id: str, topic: str, 
                                problem_type: str, n_results: int = 3) -> List[Dict]:
        """Поиск похожих задач"""
        results = self.problems_collection.query(
            query_texts=[f"{topic} {problem_type}"],
            n_results=n_results,
            where={"user_id": user_id}
        )
        
        problems = []
        if results['documents']:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                problems.append({
                    "problem_statement": doc.split("Задача:")[1].split("Тип:")[0].strip() if "Задача:" in doc else doc,
                    "problem_type": metadata.get("problem_type", ""),
                    "difficulty": metadata.get("difficulty", "easy"),
                    "metadata": metadata
                })
        
        return problems
    
    def get_solutions_history(self, user_id: str, topic: str = None, 
                            limit: int = 10) -> List[Dict]:
        """Получение истории решений"""
        where = {"user_id": user_id}
        if topic:
            where["topic"] = topic
            
        results = self.solutions_collection.get(
            where=where,
            limit=limit
        )
        
        solutions = []
        for doc, metadata in zip(results['documents'], results['metadatas']):
            solutions.append({
                "content": doc,
                "score": metadata.get("score", 0),
                "problem_type": metadata.get("problem_type", ""),
                "topic": metadata.get("topic", ""),
                "timestamp": metadata.get("timestamp", "")
            })
        
        return sorted(solutions, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def update_knowledge_state(self, user_id: str, concept: str, 
                             understanding_level: int, examples: int = 0):
        """Обновление состояния знаний пользователя"""
        
        knowledge_id = f"knowledge_{user_id}_{concept}"
        current_time = datetime.now().isoformat()
        
        existing = self.knowledge_collection.get(
            ids=[knowledge_id],
            where={"user_id": user_id, "concept": concept}
        )
        
        knowledge_text = f"Concept: {concept}, Understanding: {understanding_level}/5, Examples: {examples}"
        
        if existing['ids']:
            current_level = existing['metadatas'][0].get("understanding_level", 1)
            current_examples = existing['metadatas'][0].get("examples_understood", 0)
            
            new_level = max(current_level, understanding_level)
            new_examples = current_examples + examples
            
            embedding = self.embeddings.embed_query(knowledge_text)
            
            self.knowledge_collection.update(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[{
                    "user_id": user_id,
                    "concept": concept,
                    "understanding_level": new_level,
                    "examples_understood": new_examples,
                    "last_reviewed": current_time,
                    "memory_type": "knowledge"
                }]
            )
        else:
            embedding = self.embeddings.embed_query(knowledge_text)
            
            self.knowledge_collection.add(
                ids=[knowledge_id],
                embeddings=[embedding],
                documents=[knowledge_text],
                metadatas=[{
                    "user_id": user_id,
                    "concept": concept,
                    "understanding_level": understanding_level,
                    "examples_understood": examples,
                    "last_reviewed": current_time,
                    "memory_type": "knowledge"
                }]
            )
    
    def get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """Получение прогресса обучения пользователя"""
        
        knowledge_results = self.knowledge_collection.get(where={"user_id": user_id})
        interaction_results = self.interaction_collection.get(where={"user_id": user_id})
        solutions_results = self.solutions_collection.get(where={"user_id": user_id})
        
        # Анализ прогресса
        topics_covered = set()
        total_interactions = len(interaction_results['ids']) if interaction_results['ids'] else 0
        understanding_levels = []
        
        for metadata in knowledge_results.get('metadatas', []):
            if 'concept' in metadata:
                topics_covered.add(metadata['concept'])
            if 'understanding_level' in metadata:
                understanding_levels.append(metadata['understanding_level'])
        
        # Анализ решений
        scores = [m.get('score', 0) for m in solutions_results.get('metadatas', [])]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        avg_understanding = sum(understanding_levels) / len(understanding_levels) if understanding_levels else 0
        
        progress = {
            "topics_covered": list(topics_covered),
            "total_interactions": total_interactions,
            "average_understanding": avg_understanding,
            "problems_solved": len(solutions_results.get('ids', [])),
            "average_score": avg_score,
            "knowledge_gaps": self._identify_knowledge_gaps(knowledge_results),
            "skill_progression": self._analyze_skill_progression(solutions_results)
        }
        
        return progress
    
    def _identify_knowledge_gaps(self, knowledge_results: Dict) -> List[str]:
        """Идентификация пробелов в знаниях"""
        gaps = []
        for metadata in knowledge_results.get('metadatas', []):
            if metadata.get('understanding_level', 0) <= 2:
                gaps.append(metadata.get('concept', 'unknown'))
        return gaps
    
    def _analyze_skill_progression(self, solutions_results: Dict) -> List[Dict]:
        """Анализ прогресса навыков"""
        progression = []
        metadatas = solutions_results.get('metadatas', [])
        
        for i, metadata in enumerate(metadatas[-10:]):  # Последние 10 решений
            progression.append({
                "timestamp": metadata.get('timestamp', ''),
                "score": metadata.get('score', 0),
                "problem_type": metadata.get('problem_type', ''),
                "topic": metadata.get('topic', '')
            })
        
        return progression