"""
Storehouse for tools that derive social metrics from extractor data.

iGraph docs:
    • https://igraph.org/python/api/latest/

"""
import argparse
from src.metrics_aggregator import communicators as comm
from src.metrics_aggregator.utils import file_io_utils as file_io

TAB = " " * 4


def main():
    """Top-level access point for gathering social metrics data."""
    in_json_path: str = get_cli_args()
    input_dict: dict = file_io.read_jsonfile_into_dict(in_json_path)

    issue_data: dict = input_dict["by_issue"]

    metrics: dict = comm.gather_all_issues_comm_metrics(issue_data)

    # get out file name
    issue_filename: str = in_json_path.rsplit("/", 1)[1]
    out_filename: str = issue_filename.rsplit(".", 1)[0]
    out_path: str = file_io.mk_json_outpath(
        "./data/output", out_filename, "_metrics"
    )

    file_io.write_dict_to_jsonfile(metrics, out_path)


def get_cli_args() -> str:
    """
    Get initializing arguments from CLI.

    :return: path to file with arguments to program
    :rtype: str
    """
    # establish positional argument capability
    arg_parser = argparse.ArgumentParser(
        description="Produce social metrics from Extractor data.",
    )

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_data_path",
        help="Path to Extractor output, the data to produce metrics from",
    )

    return arg_parser.parse_args().extractor_data_path


if __name__ == "__main__":
    main()
