"""TODO."""

import igraph


def main():
    """TODO."""

    # Deterministic example
    gd = igraph.Graph(directed=True)
    gd.add_vertices(5)
    gd.add_edges([(0, 1), (1, 2)])
    print(gd.get_adjacency())

    igraph.plot(gd, bbox=(200, 200), target="../data/output/graphs/test.pdf")


def test():
    """TODO."""


if __name__ == "__main__":
    main()
