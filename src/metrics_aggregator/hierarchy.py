"""Hierarchy, adapted from JUNG and Burt's 'Structural Holes'."""

import math
import networkx


def global_hierarchy(graph):
    """
    Get a list of hierarchies (a node-level metric) for all nodes in a graph.

    Args:
        graph ():

    Returns:
        list: hierarchy for every node in a graph.
    """
    return [hierarchy(graph, node) for node in graph.nodes]


def hierarchy(graph, node):
    """
    Get the hierarchy value for every node in the graph.

    Relevant JUNG source code found at
    https://github.com/jrtom/jung/blob/1f579fe5d74ecbaecbe32ce6762e1fa9e17ed225/jung-algorithms/src/main/java/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.java#L134-L176

    JUNG docs for hierarchy found at
    http://jung.sourceforge.net/doc/api/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.html

    JUNG docs for v.degree() and v.getNeighbors() found at
    http://jung.sourceforge.net/doc/api/edu/uci/ics/jung/graph/Hypergraph.html

    Notes:
        We use all_neighbors() because the docs for JUNG's hierarchy
        implementation indicate to use getNeighbors() (see docs link
        above), which seems very similar to both neighbors() and
        all_neighbors(). The source for hierarchy conspicuously does
        NOT use getNeighbors(). It instead uses a method called
        adjacentNodes(). At the time of writing, the definition for
        this method cannot be found in the JUNG source except for
        overrides. adjacentNodes() appears to be getNeighbors() renamed.

    Args:
        nx_graph ():

    Returns:
        hierarchy of one node; value between 0 and 1
    """
    node_degree = graph.degree(node)

    if node_degree == 0:
        return math.nan

    if node_degree == 1:
        return 1

    local_constraints: list = get_neighbor_local_constraints(graph, node)

    node_agg_constraint = sum(local_constraints)

    denom = node_agg_constraint / node_degree

    # NOTE: do not need to check if node == neighbor because
    # our graphs are not permitted to have self loops.
    numerator = sum(
        compound_val_by_natlog(constraint / denom)
        for constraint in local_constraints
    )

    return numerator / compound_val_by_natlog(node_degree)


def get_neighbor_local_constraints(graph, node):
    """
    TODO.

    Args:
        graph ():
        node ():

    Returns:
        list: list of local constraints between a node and all
            of it's neighbors
    """
    return [
        networkx.local_constraint(graph, node, neighbor)
        for neighbor in graph.neighbors(node)
    ]


def compound_val_by_natlog(val):
    """
    Sum a value and its natural log.

    Args:
        val(number): value to compound

    Returns:
        Sum of a value and its natural log.
    """
    return val * math.log(val)
