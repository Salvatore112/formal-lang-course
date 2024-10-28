import pyformlang.cfg
import networkx as nx

from project import matrix_cfpq


def test_hellings_based_cfpq():
    graph_from_lecture = nx.MultiDiGraph()
    graph_from_lecture.add_edges_from(
        [
            (0, 1, {"label": "b"}),
            (1, 0, {"label": "b"}),
            (0, 2, {"label": "a"}),
            (2, 3, {"label": "a"}),
            (3, 0, {"label": "a"}),
        ]
    )

    grammar_from_lecture = pyformlang.cfg.CFG.from_text("S -> a S b | a b")
    cfpq_result_lecture_graph = matrix_cfpq.matrix_based_cfpq(
        grammar_from_lecture,
        graph_from_lecture,
        start_nodes={3},
        final_nodes={0, 1, 2, 3},
    )

    one_way_graph = nx.MultiDiGraph()
    one_way_graph.add_edges_from(
        [
            (0, 1, {"label": "a"}),
            (1, 2, {"label": "b"}),
        ]
    )
    ambiguous = pyformlang.cfg.CFG.from_text("""S -> A S B | $
                                                           A -> a  
                                                           B -> b""")

    unambigus = pyformlang.cfg.CFG.from_text("""S -> A S B S | $
                                                           A -> a  
                                                           B -> b""")
    cfpq_result_one_way_graph = matrix_cfpq.matrix_based_cfpq(
        unambigus,
        one_way_graph,
        start_nodes={0},
        final_nodes={2},
    )

    assert cfpq_result_one_way_graph == {(0, 2)}
