import matplotlib.pyplot as plt
import networkx as nx

import fandom_scraper

def visualize_graph(characters):
    # Add edges to graph
    graph = nx.Graph()
    for character in characters:
        for wiki in character.appearances:
            if not character.wiki == wiki:
                if graph.has_edge(character.wiki, wiki):
                    graph[character.wiki][wiki]['weight'] += 1
                else:
                    graph.add_edge(character.wiki, wiki, weight=1)

    # Visualize
    nx.draw_networkx(graph)
    pos = nx.spring_layout(graph, k=1/10)
    weights = nx.get_edge_attributes(graph, 'weight')
    nx.draw(graph, pos)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=weights)
    plt.show()





if __name__ == '__main__':
    characters = fandom_scraper.load_characters_from_file('characters.csv')
    visualize_graph(characters)
