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
    v_degree = graph.degree(node)

    if v_degree == 0:
        return math.nan

    if v_degree == 1:
        return 1

    v_agg_constraint = aggregate_constraint(graph, node)

    denom = v_agg_constraint / v_degree

    numerator = 0
    for neighbor in graph.neighbors(node):
        if node != neighbor:
            sl_constraint = (
                networkx.local_constraint(graph, node, neighbor) / denom
            )

            numerator += compound_val_by_natlog(sl_constraint)

    return numerator / compound_val_by_natlog(v_degree)


def aggregate_constraint(graph, node):
    """
    Python adaption of JUNG's aggregate constraint method.

    JUNG source code for Aggregate Constraint found at
    https://github.com/jrtom/jung/blob/1f579fe5d74ecbaecbe32ce6762e1fa9e17ed225/jung-algorithms/src/main/java/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.java#L208-L232

    JUNG docs for aggregate_constraint found at
    http://jung.sourceforge.net/doc/api/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.html

    JUNG source for Organizational Measure found at
    https://github.com/jrtom/jung/blob/1f579fe5d74ecbaecbe32ce6762e1fa9e17ed225/jung-algorithms/src/main/java/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.java#L234-L248

    Organizational Measure discussed on p.62-64 of Burt's Structural
    Holes. JUNG just uses a value of 1, which Burt describes in 𝑶 measure
    method #3. Because JUNG uses 1, we have simply ommitted factoring in
    Organizational Measure in the below equation.

    Args:
        node (): node to calculate aggregate constraint of.

    Returns:
        double
    """
    return sum(
        networkx.local_constraint(graph, node, neighbor)
        for neighbor in graph.neighbors(node)
    )


def compound_val_by_natlog(val):
    """
    Sum a value and its natural log.

    Args:
        val(number): value to compound

    Returns:
        Sum of a value and its natural log.
    """
    return val * math.log(val)
