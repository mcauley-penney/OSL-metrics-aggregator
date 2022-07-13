"""TODO."""

import argparse
from tests import test_communicators as comm
from src.metrics_aggregator.utils import file_io_utils as file_io


def main():
    """TODO."""
    in_json_path: str = get_cli_args()
    input_dict: dict = file_io.read_jsonfile_into_dict(in_json_path)

    comm.verify_issue_matrix_equivalence(input_dict)


def get_cli_args() -> str:
    """
    Get initializing arguments from CLI.

    :return: path to file with arguments to program
    :rtype: str
    """
    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Test social metric data generation functionality",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "test_data_json",
        help="Path to metrics test input",
    )

    return arg_parser.parse_args().test_data_json


if __name__ == "__main__":
    main()
