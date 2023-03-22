"""
Storehouse for tools that derive social metrics from extractor data.

iGraph docs:
    • https://igraph.org/python/api/latest/

"""
import argparse
import sys
from metrics_aggregator.standard import per_issue as standard_issue, per_period as standard_period
from metrics_aggregator.improved import per_issue as improved_issue, per_period as improved_period
from metrics_aggregator.utils import file_io_utils as file_io

TAB = " " * 4


def main():
    """Top-level access point for gathering social metrics data."""
    cfg: dict = get_user_cfg()
    issue_data: dict = file_io.read_jsonfile_into_dict(cfg["issue_data"])

    try:
        method = cfg["processing_method"]

    except KeyError:
        print("Configuration requires processing method!")
        sys.exit()

    if method == "old":
        metrics: dict = {
            "per_issue": standard_issue.gather_all_issue_comm_metrics(issue_data),
            "per_period": standard_period.gather_all_period_comm_metrics(issue_data),
        }

    else:
        metrics: dict = {
            "per_issue": improved_issue.gather_all_issue_comm_metrics(issue_data),
            "per_period": improved_period.gather_all_period_comm_metrics(issue_data),
        }

    file_io.write_dict_to_jsonfile(metrics, cfg["out_path"])


def get_user_cfg() -> dict:
    """
    Get path to and read from configuration file.

    :return: dict of configuration values
    :rtype: dict
    """
    cfg_path = get_cli_args()

    return file_io.read_jsonfile_into_dict(cfg_path)


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

    arg_parser.add_argument(
        "json_cfg",
        help="Path to JSON configuration file",
    )

    return arg_parser.parse_args().json_cfg


if __name__ == "__main__":
    main()
