from pyformlang.finite_automaton import (
    NondeterministicFiniteAutomaton,
    Symbol,
)
from typing import Iterable

import project.finite_automata_lib as fa_lib
import scipy
import numpy as np
from functools import reduce
import operator


class AdjacencyMatrixFA:
    def __init__(self, nfa: NondeterministicFiniteAutomaton):
        if nfa is None:
            self.states = set()
            self.states_number = 0
            self.state_id = {}
            self.start_states = set()
            self.final_states = set()
            self.bool_decomposition = {}
        else:
            self.states = nfa.states
            self.states_number = len(self.states)
            self.state_id = {state: index for index, state in enumerate(nfa.states)}
            self.start_states = set(nfa.start_states)
            self.final_states = set(nfa.final_states)
            self.bool_decomposition = self.build_bool_decomposition(nfa)

    def build_bool_decomposition(self, nfa: NondeterministicFiniteAutomaton):
        bool_decomposition = {}
        for fst_state, symbol_snd_states in nfa.to_dict().items():
            for symbol, next_states in symbol_snd_states.items():
                next_states = (
                    {next_states} if not isinstance(next_states, set) else next_states
                )

                for next_state in next_states:
                    if symbol not in bool_decomposition:
                        bool_decomposition[symbol] = scipy.sparse.csr_matrix(
                            (self.states_number, self.states_number), dtype=bool
                        )
                    bool_decomposition[symbol][
                        self.state_id[fst_state], self.state_id[next_state]
                    ] = True

        return bool_decomposition

    def accepts(self, word: Iterable[Symbol]) -> bool:
        current_states = set(self.start_states)

        for symbol in word:
            next_states = set()
            if symbol in self.bool_decomposition:
                transition_matrix = self.bool_decomposition[symbol]
                for current_state in current_states:
                    next_states.update(
                        next_state
                        for next_state in range(self.states_number)
                        if transition_matrix[self.state_id[current_state], next_state]
                    )

            current_states = next_states

        return bool(self.final_states & current_states)

    def get_transitive_closure(self):
        """
        Returns transitive closure for automaton states.
        Get indices from `states` attribute to index the matrix
        """
        if not self.bool_decomposition:
            return np.diag(np.ones(self.states_number, dtype=np.bool_))

        matrices = list(self.bool_decomposition.values())
        sum: scipy.sparse.csr_array = reduce(operator.add, matrices[1:], matrices[0])
        sum.setdiag(True)  # make reflexive

        # compute transitive closure using matrix exponentiation
        tc = sum.toarray()
        for pow in range(2, self.states_number + 3):
            prev = tc
            tc = np.linalg.matrix_power(prev, pow)
            if np.array_equal(prev, tc):
                break

        return tc

    def is_empty(self) -> bool:
        transitive_closure = self.get_transitive_closure()
        for start_state in self.start_states:
            for final_state in self.final_states:
                if transitive_closure[
                    self.state_id[start_state], self.state_id[final_state]
                ]:
                    return False
        return True


def print_csc_matrix(matrix):
    # Convert to dense format for better readability
    dense_matrix = matrix.toarray()

    # Calculate the maximum width for formatting
    max_width = max(len(str(item)) for row in dense_matrix for item in row)

    for row in dense_matrix:
        formatted_row = " | ".join(f"{str(item):>{max_width}}" for item in row)
        print(f"| {formatted_row} |")


def intersect_automata(
    automaton1: AdjacencyMatrixFA, automaton2: AdjacencyMatrixFA
) -> AdjacencyMatrixFA:
    automata_intersection = AdjacencyMatrixFA(None)
    automata_intersection.states_number = (
        automaton1.states_number * automaton2.states_number
    )
    new_symbols = (
        automaton1.bool_decomposition.keys() & automaton2.bool_decomposition.keys()
    )
    for symbol in new_symbols:
        automata_intersection.bool_decomposition[symbol] = scipy.sparse.kron(
            automaton1.bool_decomposition[symbol],
            automaton2.bool_decomposition[symbol],
            "csr",
        )
    for first_state, first_state_id in automaton1.state_id.items():
        for second_state, second_state_id in automaton2.state_id.items():
            new_state = first_state_id * automaton2.states_number + second_state_id
            automata_intersection.state_id[new_state] = new_state
            if (
                first_state in automaton1.start_states
                and second_state in automaton2.start_states
            ):
                automata_intersection.start_states.add(new_state)

            if (
                first_state in automaton1.final_states
                and second_state in automaton2.final_states
            ):
                automata_intersection.final_states.add(new_state)

    return automata_intersection


def print_csc_matrix(matrix):
    # Convert to dense format for better readability
    dense_matrix = matrix.toarray()

    # Calculate the maximum width for formatting
    max_width = max(len(str(item)) for row in dense_matrix for item in row)

    for row in dense_matrix:
        formatted_row = " | ".join(f"{str(item):>{max_width}}" for item in row)
        print(f"| {formatted_row} |")


def tensor_based_rpq(
    regex,
    graph,
    start_nodes: set = None,
    final_nodes: set = None,
):
    nfa = fa_lib.graph_to_nfa(graph, start_nodes, final_nodes)
    dfa = fa_lib.regex_to_dfa(regex)

    bool_matrix_for_graph = AdjacencyMatrixFA(nfa)
    bool_matrix_for_query = AdjacencyMatrixFA(dfa)

    bool_matrix_intersected = intersect_automata(
        bool_matrix_for_graph, bool_matrix_for_query
    )

    start_states = bool_matrix_intersected.start_states
    final_states = bool_matrix_intersected.final_states

    transitive = bool_matrix_intersected.get_transitive_closure()

    result = set()

    for first_state, second_state in zip(*transitive.nonzero()):
        if first_state in start_states and second_state in final_states:
            result.add(
                (
                    first_state // bool_matrix_for_query.states_number,
                    second_state // bool_matrix_for_query.states_number,
                )
            )
    print("Result", result)
    return result
