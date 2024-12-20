from dataclasses import dataclass
from typing import Dict, Set, Tuple
from pyformlang import rsa
import networkx as nx


@dataclass(frozen=True)
class AutomatonState:
    variable: str
    substate: str


@dataclass(frozen=True)
class ParseForestNode:
    gss_node: "GSSNode"
    state: AutomatonState
    node_id: int


class GSSNode:
    def __init__(self, state: AutomatonState, node_id: int):
        self.state = state
        self.node_id = node_id
        self.refs = {}
        self.visited_nodes = set()

    def pop(self, current_node_id: int) -> Set[ParseForestNode]:
        if current_node_id in self.visited_nodes:
            return set()
        self.visited_nodes.add(current_node_id)
        return {
            ParseForestNode(gss, state, current_node_id)
            for state, gss_list in self.refs.items()
            for gss in gss_list
        }

    def add_ref(
        self, return_state: AutomatonState, gss_node: "GSSNode"
    ) -> Set[ParseForestNode]:
        if gss_node in self.refs.setdefault(return_state, set()):
            return set()
        self.refs[return_state].add(gss_node)
        return {
            ParseForestNode(gss_node, return_state, current_node)
            for current_node in self.visited_nodes
        }


@dataclass
class AutomatonStateData:
    terminal_edges: Dict[str, AutomatonState]
    variable_edges: Dict[str, Tuple[AutomatonState, AutomatonState]]
    is_final_state: bool


class GLLParser:
    def __init__(self, rsm: rsa.RecursiveAutomaton, graph: nx.DiGraph):
        self.node_edges = {
            node: {
                symbol: set() for _, _, symbol in graph.edges(data="label") if symbol
            }
            for node in graph.nodes()
        }

        self.state_data = {
            variable: {
                state: AutomatonStateData({}, {}, state in box.dfa.final_states)
                for state in box.dfa.to_networkx().nodes
            }
            for variable, box in rsm.boxes.items()
        }

        self.start_state = AutomatonState(
            rsm.initial_label, rsm.boxes[rsm.initial_label].dfa.start_state.value
        )

        self.graph = graph
        self.pending_nodes = set()
        self.added_nodes = set()

        self.accept_gss_node = GSSNode(AutomatonState("$", "fin"), None)
        self.gss_nodes = {}

        for from_node, to_node, symbol in graph.edges(data="label"):
            if symbol:
                self.node_edges[from_node].setdefault(symbol, set()).add(to_node)

        for variable, box in rsm.boxes.items():
            for from_state, to_state, symbol in box.dfa.to_networkx().edges(
                data="label"
            ):
                if symbol:
                    state_data = self.state_data[variable][from_state]
                    if symbol in rsm.boxes:
                        sub_box = rsm.boxes[symbol].dfa
                        state_data.variable_edges[symbol] = (
                            AutomatonState(symbol, sub_box.start_state.value),
                            AutomatonState(variable, to_state),
                        )
                    else:
                        state_data.terminal_edges[symbol] = AutomatonState(
                            variable, to_state
                        )

    def get_gss_node(self, state: AutomatonState, node_id: int) -> GSSNode:
        if (state, node_id) not in self.gss_nodes:
            self.gss_nodes[(state, node_id)] = GSSNode(state, node_id)
        return self.gss_nodes[(state, node_id)]

    def add_parse_nodes(self, nodes: Set[ParseForestNode]):
        new_nodes = nodes - self.added_nodes
        self.added_nodes.update(new_nodes)
        self.pending_nodes.update(new_nodes)

    def process_popped_nodes(
        self, nodes: Set[ParseForestNode], previous_node: ParseForestNode
    ) -> Tuple[Set[ParseForestNode], Set[Tuple[int, int]]]:
        return {node for node in nodes if node.gss_node != self.accept_gss_node}, {
            (previous_node.gss_node.node_id, node.node_id)
            for node in nodes
            if node.gss_node == self.accept_gss_node
        }

    def _gll_based_cfpq(
        self, from_nodes: Set[int], to_nodes: Set[int]
    ) -> Set[Tuple[int, int]]:
        reachable_pairs = set()
        for node_id in from_nodes:
            gss_node = self.get_gss_node(self.start_state, node_id)
            gss_node.add_ref(AutomatonState("$", "fin"), self.accept_gss_node)
            self.add_parse_nodes({ParseForestNode(gss_node, self.start_state, node_id)})

        while self.pending_nodes:
            parse_node = self.pending_nodes.pop()
            state_data = self.state_data[parse_node.state.variable][
                parse_node.state.substate
            ]

            for terminal, new_state in state_data.terminal_edges.items():
                if terminal in self.node_edges[parse_node.node_id]:
                    self.add_parse_nodes(
                        {
                            ParseForestNode(parse_node.gss_node, new_state, new_node_id)
                            for new_node_id in self.node_edges[parse_node.node_id][
                                terminal
                            ]
                        }
                    )

            for _, (
                start_rsm_state,
                return_rsm_state,
            ) in state_data.variable_edges.items():
                sub_node = self.get_gss_node(start_rsm_state, parse_node.node_id)
                popped_nodes = sub_node.add_ref(return_rsm_state, parse_node.gss_node)
                popped_nodes, sub_reachable_pairs = self.process_popped_nodes(
                    popped_nodes, parse_node
                )
                self.add_parse_nodes(popped_nodes)
                self.add_parse_nodes(
                    {ParseForestNode(sub_node, start_rsm_state, parse_node.node_id)}
                )
                reachable_pairs.update(sub_reachable_pairs)

            if state_data.is_final_state:
                new_parse_nodes = parse_node.gss_node.pop(parse_node.node_id)
                new_parse_nodes, start_end_pairs = self.process_popped_nodes(
                    new_parse_nodes, parse_node
                )
                self.add_parse_nodes(new_parse_nodes)
                reachable_pairs.update(start_end_pairs)

        return {
            (start_node, end_node)
            for start_node, end_node in reachable_pairs
            if end_node in to_nodes
        }


def gll_based_cfpq(
    rsm: rsa.RecursiveAutomaton,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> Set[Tuple[int, int]]:
    return GLLParser(rsm, graph)._gll_based_cfpq(
        start_nodes or set(graph.nodes()), final_nodes or set(graph.nodes())
    )
