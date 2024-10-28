import pyformlang
import scipy
import networkx as nx


from project.cfpq_hellings import cfg_to_weak_normal_form
from typing import Set
from collections import defaultdict


def _matrix_based_cfpq(cfg, graph):
    node_id = {node: index for index, node in enumerate(graph.nodes)}
    id_node = {index: node for node, index in node_id.items()}

    wcfg = cfg_to_weak_normal_form(cfg)

    # A -> eps
    epsilon_productions = set()

    # A -> a
    single_terminal_productions = defaultdict(list)

    # A -> B C
    double_non_terminal_productions = set()

    for production in wcfg.productions:
        if len(production.body) == 1:
            single_terminal_productions[production.body[0].value].append(
                production.head
            )
        elif len(production.body) == 2:
            double_non_terminal_productions.add(
                (production.head, production.body[0], production.body[1])
            )
        else:
            epsilon_productions.add(production.head)

    bool_decomposition = defaultdict(
        lambda: scipy.sparse.csr_matrix(
            (graph.number_of_nodes(), graph.number_of_nodes()), dtype=bool
        )
    )

    for start, finish, attributes in graph.edges.data():
        for nonterminal in single_terminal_productions[attributes["label"]]:
            bool_decomposition[nonterminal][node_id[start], node_id[finish]] = True

    for node_id in range(graph.number_of_nodes()):
        for var in epsilon_productions:
            bool_decomposition[var][node_id, node_id] = True

    last_nonzero_number = 0
    current_nonzero_number = sum(
        matrix.count_nonzero() for matrix in bool_decomposition.values()
    )
    count = 0
    while last_nonzero_number != current_nonzero_number:
        count += 1
        for hd, nonterminal_1, nonterminal_2 in double_non_terminal_productions:
            bool_decomposition[hd] += bool_decomposition[nonterminal_1].dot(
                bool_decomposition[nonterminal_2]
            )

        last_nonzero_number = current_nonzero_number
        current_nonzero_number = sum(
            matrix.count_nonzero() for matrix in bool_decomposition.values()
        )

    result = {
        (id_node[i], nonterminal, id_node[j])
        for nonterminal, bool_matrix in bool_decomposition.items()
        for i, j in zip(*bool_matrix.nonzero())
    }
    return result


def matrix_based_cfpq(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> set[tuple[int, int]]:
    result = _matrix_based_cfpq(cfg, graph)
    return {
        (n, m)
        for (n, nonterminal, m) in result
        if nonterminal == cfg.start_symbol and n in start_nodes and m in final_nodes
    }
