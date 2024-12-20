import numpy as np

from typing import Dict, Iterable
from pyformlang.finite_automaton import NondeterministicFiniteAutomaton, State, Symbol
from scipy.sparse import csc_matrix, eye, kron, csr_matrix
from project.finite_automata_lib import graph_to_nfa, regex_to_dfa
from networkx import MultiDiGraph
from pyformlang.rsa.recursive_automaton import RecursiveAutomaton


class AdjacencyMatrixFA:
    def __init__(
        self, nfa: NondeterministicFiniteAutomaton | RecursiveAutomaton
    ) -> None:
        if nfa is None:
            self.start_states_id = set()
            self.final_states_id = set()
            self.start_states = set()
            self.final_states = set()
            self.states_count = 0
            self.state_id = {}
            self.id_state = {}
            self.bool_decomposition = {}
            return
        self.start_states = nfa.start_states
        self.final_states = nfa.final_states

        self.states_count = len(nfa.states)
        self.id_state = {state: index for state, index in enumerate(nfa.states)}
        self.state_id = {state: index for index, state in enumerate(nfa.states)}

        self.start_states_id = {
            self.state_id[st] for st in nfa.states if st in nfa.start_states
        }
        self.final_states_id = {
            self.state_id[st] for st in nfa.states if st in nfa.final_states
        }

        self.bool_decomposition = self.build_bool_decomposition(nfa)

    def build_bool_decomposition(
        self, nfa: NondeterministicFiniteAutomaton
    ) -> Dict[Symbol, csr_matrix]:
        bool_decomposition = {}
        for fst_state, symbol_snd_states in nfa.to_dict().items():
            for symbol, next_states in symbol_snd_states.items():
                next_states = (
                    {next_states} if not isinstance(next_states, set) else next_states
                )

                for next_state in next_states:
                    if symbol not in bool_decomposition:
                        bool_decomposition[symbol] = csr_matrix(
                            (self.states_count, self.states_count), dtype=bool
                        )
                    bool_decomposition[symbol][
                        self.state_id[fst_state], self.state_id[next_state]
                    ] = True

        return bool_decomposition

    def accepts(self, word: Iterable[Symbol]) -> bool:
        current_states = set(self.start_states_id)

        for symbol in word:
            next_states = set()
            if symbol in self.bool_decomposition:
                transition_matrix = self.bool_decomposition[symbol]
                for current_state in current_states:
                    next_states.update(
                        next_state
                        for next_state in range(self.states_count)
                        if transition_matrix[current_state, next_state]
                    )

            current_states = next_states
        return bool(self.final_states_id & current_states)

    def is_empty(self) -> bool:
        transitive_closure = self.get_transitive_closure()
        for start_state_id in self.start_states_id:
            for final_state_id in self.final_states_id:
                if transitive_closure[start_state_id, final_state_id]:
                    return False
        return True

    def get_transitive_closure(self) -> csc_matrix:
        identity_matrix = eye(self.states_count, dtype=bool)
        adjacency_matrix = csc_matrix(identity_matrix)

        for symbol in self.bool_decomposition:
            adjacency_matrix += self.bool_decomposition[symbol]

        current_power = adjacency_matrix
        exponent = self.states_count

        while exponent != 0:
            if exponent % 2 == 1:
                closure_matrix = np.dot(adjacency_matrix, current_power)
            current_power = np.dot(current_power, current_power)
            exponent //= 2

        return closure_matrix


def intersect_automata(
    automaton1: AdjacencyMatrixFA, automaton2: AdjacencyMatrixFA
) -> AdjacencyMatrixFA:
    intersection = AdjacencyMatrixFA(None)
    new_symbols = (
        automaton1.bool_decomposition.keys() & automaton2.bool_decomposition.keys()
    )

    for symbol in new_symbols:
        intersection.bool_decomposition[symbol] = kron(
            automaton1.bool_decomposition[symbol],
            automaton2.bool_decomposition[symbol],
            "csr",
        )
    intersection.states_count = automaton1.states_count * automaton2.states_count

    for first_state, first_state_id in automaton1.state_id.items():
        for second_state, second_state_id in automaton2.state_id.items():
            new_state_id = first_state_id * automaton2.states_count + second_state_id
            state = State((first_state.value, second_state.value))
            intersection.state_id[state] = new_state_id
            if (
                first_state in automaton1.start_states
                and second_state in automaton2.start_states
            ):
                intersection.start_states.add(state)
                intersection.start_states_id.add(new_state_id)
            if (
                first_state in automaton1.final_states
                and second_state in automaton2.final_states
            ):
                intersection.final_states.add(state)
                intersection.final_states_id.add(new_state_id)
    intersection.id_state = {
        index: state for state, index in intersection.state_id.items()
    }
    return intersection


def tensor_based_rpq(
    regex: str, graph: MultiDiGraph, start_nodes: set[int], final_nodes: set[int]
) -> set[tuple[int, int]]:
    nfa_of_graph = AdjacencyMatrixFA(graph_to_nfa(graph, start_nodes, final_nodes))
    dfa_of_regex = AdjacencyMatrixFA(regex_to_dfa(regex))

    intersection = intersect_automata(nfa_of_graph, dfa_of_regex)
    transitive_closure = intersection.get_transitive_closure()

    result = set()

    for start in start_nodes:
        for final in final_nodes:
            for dfa_start_state in dfa_of_regex.start_states:
                for dfa_final_state in dfa_of_regex.final_states:
                    intersection_start_id = intersection.state_id[
                        (start, dfa_start_state)
                    ]
                    intersection_final_id = intersection.state_id[
                        (final, dfa_final_state)
                    ]
                    if transitive_closure[
                        intersection_start_id,
                        intersection_final_id,
                    ]:
                        result.add((start, final))

    return result
