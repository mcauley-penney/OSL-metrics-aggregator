"""TODO."""

import igraph
from src.metrics_aggregator import communicators as comm

TAB = " " * 4


def verify_issue_matrix_equivalence(cur_issue: dict, correct_adj_mat: list[list[int]]):
    """
    Check if adjacency-matrix-producing function produces correct output.

    Given an issue and the corresponding adjacency matrix, check if the
    function that we are using to produce adjacency matrices produces
    the correct output.

    Args:
        issue_data (dict):
    """
    graph_adj_mat = get_issue_data_adj_mat(cur_issue)

    assert_mat_attributes_equality(correct_adj_mat, graph_adj_mat)


def assert_mat_attributes_equality(correct_mat, graph_mat):
    """
    TODO.

    Args:
        correct_mat ():
        graph_mat ():
    """
    i = 0

    graph_mat_len = graph_mat._nrow
    correct_mat_len = len(correct_mat)

    print()
    print("Length:")
    print(f"{TAB}True num rows   : {graph_mat_len}")
    print(f"{TAB}Correct num rows: {correct_mat_len}")
    print()

    try:

        assert graph_mat_len == correct_mat_len, "Matrices are not the same length!\n"

        print("True:")
        for row in graph_mat:
            print(row)

        print()

        print("Correct:")
        for row in correct_mat:
            print(row)

        print()

        while i < graph_mat_len:
            cur_true_row = graph_mat[i]
            cur_correct_row = correct_mat[i]

            assert (
                cur_true_row == cur_correct_row
            ), f"""Rows at index {i} are not identical
{TAB * 2}Actual: {cur_true_row}
{TAB * 2}Correct: {cur_correct_row}"""

            i += 1

        print("Matrices are identical...\n")

    except AssertionError as err_msg:
        print(f"AssertionError: \n    {err_msg}")


def get_issue_data_adj_mat(issue: dict):
    """
    TODO.

    Args:
        issue (dict):
    """
    cur_graph = igraph.Graph(directed=True)

    cur_graph = comm.build_issue_conversation_matrix(issue, cur_graph)

    return cur_graph.get_adjacency()
