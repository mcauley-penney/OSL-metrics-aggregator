"""
Storehouse for tools that derive social metrics from extractor data.

iGraph docs:
    • https://igraph.org/python/api/latest/

"""

import argparse
import sys
from metrics_aggregator.legacy import (
    per_issue as legacy_issue,
    per_period as legacy_period,
)
from metrics_aggregator.hybrid import (
    per_issue as hybrid_issue,
    per_period as hybrid_period,
)
from metrics_aggregator.utils import file_io_utils as file_io

TAB = " " * 4
PROCESSING_METHODS = {
    "legacy": (legacy_issue, legacy_period),
    "hybrid": (hybrid_issue, hybrid_period),
}


def main():
    """Top-level access point for gathering social metrics data."""
    cfg: dict = get_user_cfg()
    issue_data: dict = file_io.read_jsonfile_into_dict(cfg["issue_data"])

    try:
        method = cfg["processing_method"]

    except KeyError:
        print("Configuration requires processing method!")
        sys.exit()

    try:
        issue_processor, period_processor = PROCESSING_METHODS[method]

    except KeyError:
        valid_methods = ", ".join(sorted(PROCESSING_METHODS))
        print(
            f"Unknown processing method '{method}'. "
            f"Expected one of: {valid_methods}"
        )
        sys.exit()

    metrics: dict = {
        "per_issue": issue_processor.gather_all_issue_comm_metrics(issue_data),
        "per_period": period_processor.gather_all_period_comm_metrics(issue_data),
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
