import logging

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """Визуализатор графа диалога"""
    
    @staticmethod
    def visualize_learning_graph(learning_graph):
        """Визуализация графа обучения"""
        try:
            # Попытка импорта только если установлены
            import networkx as nx
            import matplotlib.pyplot as plt
            
            G = nx.DiGraph()
            
            nodes = [
                "analyze_context",
                "retrieve_memory", 
                "select_mode",
                "generate_response",
                "update_memory"
            ]
            
            for node in nodes:
                G.add_node(node, label=node.replace('_', '\n').title())
            
            edges = [
                ("analyze_context", "retrieve_memory"),
                ("retrieve_memory", "select_mode"),
                ("select_mode", "generate_response"),
                ("generate_response", "update_memory")
            ]
            
            G.add_edges_from(edges)
            
            plt.figure(figsize=(12, 8))
            pos = nx.spring_layout(G, seed=42)
            
            nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='lightblue', 
                                  alpha=0.9, node_shape='s', edgecolors='darkblue')
            
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True,
                                  arrowsize=20, arrowstyle='->', width=2)
            
            labels = nx.get_node_attributes(G, 'label')
            nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight='bold')
            
            plt.title("Learning Companion Agent - Dialog Graph", size=14)
            plt.axis('off')
            plt.tight_layout()
            
            plt.savefig('./learning_graph.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            logger.info("Граф визуализирован и сохранен как 'learning_graph.png'")
            
        except ImportError:
            logger.warning("networkx или matplotlib не установлены. Пропускаем визуализацию.")
            GraphVisualizer.print_graph_structure()
    
    @staticmethod
    def print_graph_structure():
        """Печать структуры графа"""
        print("=" * 50)
        print("LEARNING COMPANION AGENT - DIALOG GRAPH")
        print("=" * 50)
        print("\nNODES:")
        print("1. analyze_context   - Анализ контекста обучения")
        print("2. retrieve_memory   - Поиск в долгосрочной памяти")
        print("3. select_mode       - Выбор режима обучения") 
        print("4. generate_response - Генерация адаптированного ответа")
        print("5. update_memory     - Обновление памяти\n")
        
        print("EDGE FLOW:")
        print("analyze_context → retrieve_memory → select_mode → generate_response → update_memory")
        print("\n" + "=" * 50)