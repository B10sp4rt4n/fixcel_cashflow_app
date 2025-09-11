
import networkx as nx

def verificar_relaciones():
    """Verifica las relaciones entre las hojas para detectar cualquier error o relación rota."""
    grafo = nx.Graph()

    # Agregar nodos y relaciones aquí
    grafo.add_edge("Hoja1", "Hoja2")
    grafo.add_edge("Hoja2", "Hoja3")

    # Revisar relaciones
    if not nx.has_path(grafo, "Hoja1", "Hoja3"):
        return None  # Relación rota

    return grafo

def mostrar_alertas():
    """Muestra alertas si hay relaciones rotas."""
    grafo = verificar_relaciones()
    if grafo is None:
        return ["Relación rota entre las hojas"]
    else:
        return []
