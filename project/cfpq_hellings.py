from networkx import MultiDiGraph
from pyformlang.cfg import CFG
from typing import Set, Tuple

import pyformlang.cfg
import networkx as nx


def cfg_to_weak_normal_form(cfg: pyformlang.cfg.CFG) -> pyformlang.cfg.CFG:
    cfg = cfg.eliminate_unit_productions()

    cfg = cfg.remove_useless_symbols()

    short_production = cfg._get_productions_with_only_single_terminals()

    final_productions = set(cfg._decompose_productions(short_production))

    return pyformlang.cfg.CFG(
        start_symbol=cfg._start_symbol,
        productions=final_productions,
    )


def _hellings_based_cfpq(
    cfg: CFG, graph: MultiDiGraph
) -> Set[Tuple[int, pyformlang.cfg.Variable, int]]:
    cfg = cfg_to_weak_normal_form(cfg)

    # A -> eps
    epsilon_productions = set()

    # A -> a
    single_terminal_productions = set()

    # A -> B C
    double_non_terminal_productions = set()

    for production in cfg.productions:
        if len(production.body) == 1:
            single_terminal_productions.add(production)
        elif len(production.body) == 2:
            double_non_terminal_productions.add(production)
        else:
            epsilon_productions.add(production)

    result = set()

    for production in epsilon_productions:
        for node in graph.nodes:
            result.add((node, production.head, node))

    for n, m, label in graph.edges(data="label"):
        for production in single_terminal_productions:
            if label == production.body[0].value:
                result.add((n, production.head, m))

    new = set(result)

    while new:
        # Pick and remove an (n, N, m) from new
        (n, N, m) = new.pop()

        for n_prime, M, m_prime in list(result):
            if m_prime == n:
                for production in double_non_terminal_productions:
                    if production.body[0] == M and production.body[1] == N:
                        new_triple = (n_prime, production.head, m)
                        if new_triple not in result:
                            new.add(new_triple)
                            result.add(new_triple)

            if n_prime == m:
                for production in double_non_terminal_productions:
                    if production.body[0] == N and production.body[1] == M:
                        new_triple = (n, production.head, m_prime)
                        if new_triple not in result:
                            new.add(new_triple)
                            result.add(new_triple)

    return result


def hellings_based_cfpq(
    cfg: pyformlang.cfg.CFG,
    graph: nx.DiGraph,
    start_nodes: Set[int] = None,
    final_nodes: Set[int] = None,
) -> Set[Tuple[int, int]]:
    result = _hellings_based_cfpq(cfg, graph)

    return {
        (n, m)
        for n, var, m in result
        if var == cfg.start_symbol and n in start_nodes and m in final_nodes
    }
