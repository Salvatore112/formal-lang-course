import pyformlang.cfg
import networkx as nx

from project import cfpq_hellings


def test_cfg_to_weak_normal_form():
    grammar_with_long_productions = """S -> A B
                                       A -> a B c B
                                       B -> d e f"""

    long_production_test_grammar = cfpq_hellings.cfg_to_weak_normal_form(
        pyformlang.cfg.CFG.from_text(grammar_with_long_productions, start_symbol="S")
    )

    for production in long_production_test_grammar.productions:
        assert len(production.body) <= 2

    grammar_with_unit_productions = """A -> B | a
                                       B -> C | b
                                       C -> DD | c"""

    unit_productions_test_grammar = cfpq_hellings.cfg_to_weak_normal_form(
        pyformlang.cfg.CFG.from_text(grammar_with_unit_productions, start_symbol="A")
    )

    for unit_pair in unit_productions_test_grammar.get_unit_pairs():
        assert unit_pair[0] == unit_pair[1]

    grammar_with_not_generating_symbols = """S -> A c
                                             A -> S D
                                             D -> a D
                                             A -> a"""

    not_generating_symbols_test_grammar = pyformlang.cfg.CFG.from_text(
        grammar_with_not_generating_symbols, start_symbol="A"
    )

    generating_symbols = not_generating_symbols_test_grammar.get_generating_symbols()

    not_generating_symbols_test_grammar = cfpq_hellings.cfg_to_weak_normal_form(
        not_generating_symbols_test_grammar
    )
    for production in not_generating_symbols_test_grammar.productions:
        assert production.head.value in generating_symbols

    grammar_with_not_reachable_symbols = """S -> A B | C D
                                            A -> E F
                                            G -> A D
                                            C -> c"""

    not_reachable_symbols_test_grammar = pyformlang.cfg.CFG.from_text(
        grammar_with_not_reachable_symbols, start_symbol="S"
    )

    reachable_symbols = not_generating_symbols_test_grammar.get_reachable_symbols()

    not_reachable_symbols_test_grammar = cfpq_hellings.cfg_to_weak_normal_form(
        not_reachable_symbols_test_grammar
    )
    for production in not_generating_symbols_test_grammar.productions:
        assert production.head.value in reachable_symbols


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
    cfpq_result = cfpq_hellings.hellings_based_cfpq(
        grammar_from_lecture,
        graph_from_lecture,
        start_nodes={3},
        final_nodes={0, 1, 2, 3},
    )
    assert cfpq_result == {(3, 0), (3, 1)}
