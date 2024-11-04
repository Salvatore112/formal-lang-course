import networkx as nx

from scipy.sparse import csc_array
from pyformlang import rsa, cfg as pycfg
from pyformlang.finite_automaton import NondeterministicFiniteAutomaton
from project.adjacency_matrix_fa import AdjacencyMatrixFA, intersect_automata
from project.finite_automata_lib import graph_to_nfa
from typing import Set, Tuple


def cfg_to_rsm(cfg: pycfg.CFG) -> rsa.RecursiveAutomaton:
    return ebnf_to_rsm(cfg.to_text())


def ebnf_to_rsm(ebnf: str) -> rsa.RecursiveAutomaton:
    return rsa.RecursiveAutomaton.from_text(ebnf)


def bool_decomposed_rsm(rsm: rsa.RecursiveAutomaton) -> AdjacencyMatrixFA:
    nfa_of_rsm = NondeterministicFiniteAutomaton()

    for nonterminal, box in rsm.boxes.items():
        box_dfa = box.dfa

        for s in box_dfa.final_states | box_dfa.start_states:
            if s in box_dfa.final_states:
                nfa_of_rsm.add_final_state((nonterminal, s))
            if s in box_dfa.start_states:
                nfa_of_rsm.add_start_state((nonterminal, s))

        for edge in box_dfa.to_networkx().edges(data="label"):
            nfa_of_rsm.add_transition(
                (nonterminal, edge[0]), edge[2], (nonterminal, edge[1])
            )

    return AdjacencyMatrixFA(nfa_of_rsm)


def tensor_based_cfpq(
    rsm: rsa.RecursiveAutomaton,
    graph: nx.DiGraph,
    start_nodes: Set[int] | None = None,
    final_nodes: Set[int] | None = None,
) -> Set[Tuple[int, int]]:
    decomposed_rsa = bool_decomposed_rsm(rsm)
    decomposed_graph = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))

    for nonterminal in rsm.boxes:
        for matrix in (decomposed_graph, decomposed_rsa):
            if nonterminal not in matrix.bool_decomposition:
                matrix.bool_decomposition[nonterminal] = csc_array(
                    (matrix.states_count, matrix.states_count), dtype=bool
                )

    last_nonzero_number = 0
    current_nonzero_number = None

    while last_nonzero_number != current_nonzero_number:
        last_nonzero_number = current_nonzero_number
        intersection = intersect_automata(decomposed_rsa, decomposed_graph)

        transitive_closure = intersection.get_transitive_closure()

        for row_index, column_index in zip(*transitive_closure.nonzero()):
            row_state = intersection.id_state[row_index]
            column_state = intersection.id_state[column_index]

            (row_symbol, row_rsm_state), row_graph_state = row_state.value
            (column_symbol, column_rsm_state), column_graph_state = column_state.value

            if (
                row_symbol == column_symbol
                and row_rsm_state in rsm.boxes[row_symbol].dfa.start_states
                and column_rsm_state in rsm.boxes[row_symbol].dfa.final_states
            ):
                row_graph_index = decomposed_graph.state_id[row_graph_state]
                column_graph_index = decomposed_graph.state_id[column_graph_state]

                decomposed_graph.bool_decomposition[row_symbol][
                    row_graph_index, column_graph_index
                ] = True

        current_nonzero_number = sum(
            decomposed_graph.bool_decomposition[nonterminal].count_nonzero()
            for nonterminal in decomposed_graph.bool_decomposition
        )

    return {
        (n, m)
        for n in decomposed_graph.start_states
        for m in decomposed_graph.final_states
        if decomposed_graph.bool_decomposition[rsm.initial_label][
            decomposed_graph.state_id[n], decomposed_graph.state_id[m]
        ]
    }
