"""Test communicator social metric-generating functionality."""

import sys
from metrics_aggregator import communicators as comm

TAB = " " * 4


def assert_matrix_equality(correct_mat, graph_mat):
    """
    TODO.

    Args:
        correct_mat ():
        graph_mat ():
    """
    i = 0

    correct_mat_len = len(correct_mat)
    graph_mat_len = graph_mat._nrow

    print()
    print("Matrices:")
    print_matrix(f"{TAB}True:", graph_mat)
    print_matrix(f"{TAB}Correct:", correct_mat)

    try:
        assert (
            graph_mat_len == correct_mat_len
        ), "Matrices are not the same length!\n"

    except AssertionError as err_msg:
        print(f"\nAssertionError: \n    {err_msg}")
        sys.exit()

    finally:
        print("Length:")
        print(f"{TAB}Correct num rows: {correct_mat_len}")
        print(f"{TAB}True num rows   : {graph_mat_len}")
        print()

    try:
        while i < graph_mat_len:
            cur_true_row = graph_mat[i]
            cur_correct_row = correct_mat[i]

            assert (
                cur_true_row == cur_correct_row
            ), f"""Rows at index {i} are not identical
{TAB * 2}Correct: {cur_correct_row}
{TAB * 2}Actual : {cur_true_row}\n"""

            i += 1

    except AssertionError as err_msg:
        print(f"\nAssertionError: \n    {err_msg}")
        sys.exit()

    else:
        print("Matrix rows are identical!\n")


def print_matrix(label: str, mat: list[list[int]]) -> None:
    """
    Print a list of lists of ints.

    Args:
        mat (list[list[int]]): matrix to print
    """
    print(label)

    for row in mat:
        print(f"{TAB}{row}")

    print()


def verify_issue_matrix_equivalence(issue_test_input: dict):
    """
    TODO: update.

    Check if adjacency-matrix-producing function produces correct output.

    Given an issue and the corresponding adjacency matrix, check if the
    function that we are using to produce adjacency matrices produces
    the correct output.

    Args:
        issue_data (dict):
    """
    correct_matrix: dict = issue_test_input["matrix"]
    issue_data: dict = issue_test_input["by_issue"]

    cur_network_graph = comm.make_period_network_matrix(
        issue_data, list(issue_data.keys())
    )

    adj_mat = cur_network_graph.get_adjacency()

    assert_matrix_equality(correct_matrix, adj_mat)
