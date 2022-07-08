"""TODO."""

import datetime
import math


def find_core_contribs_per_issue(input_data: dict):
    """TODO."""

    def find_issue_core_contribs(
        cur_issue, core_per_timeframe: dict, timeframe_keys: list
    ):
        def find_commit_period_key(cur_issue_date: str, interval_timestrs: list) -> str:
            def str_to_datetime(time_str: str) -> datetime.datetime:

                return datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")

            i: int = 0

            # Format is "03/12/14, 11:38:01 AM
            cur_issue_datetime: datetime.datetime = datetime.datetime.strptime(
                cur_issue_date, "%m/%d/%y, %I:%M:%S %p"
            )

            # TODO: use binary search?
            while cur_issue_datetime > str_to_datetime(interval_timestrs[i]):
                i += 1

            return contrib_interval_start_timestrs[i - 1]

        issue_bucket_key: str = find_commit_period_key(
            cur_issue["date"], timeframe_keys
        )

        issue_period_core_contribs: dict = core_per_timeframe[issue_bucket_key]

        # get list of contribs in issue who are in period dict too
        return [
            dev
            for dev in cur_issue["contributors"]
            if dev in issue_period_core_contribs
        ]

    commit_input: dict = input_data["by_commit"]
    issue_input: dict = input_data["by_issue"]

    contribs_per_issue: dict = _get_contribs_per_issue(issue_input)

    core_contribs_per_timeframe = _get_core_contribs_per_timeframe(commit_input)

    contrib_interval_start_timestrs: list = list(core_contribs_per_timeframe.keys())

    for _, issue in contribs_per_issue.items():

        # get list of contribs in issue who are in period dict too
        issue_core_contribs = find_issue_core_contribs(
            issue, core_contribs_per_timeframe, contrib_interval_start_timestrs
        )

        # TODO: package this up and return it
        print(issue_core_contribs)


def _get_contribs_per_issue(issue_input: dict) -> dict:
    """
    TODO.

    This functionality requires that the incoming dictionary of issues has:
        - the dictionary of commit info for each issue
            - this must include the author name for the commit
        - the time that one wants to use to determine the issue's bucket
            - i.e. what timeframe the issue will "belong" to

    Args:
        issue_input (dict): dictionary of data about issues for repo of interest.

    Returns:
        dict: {issue_num:contributor_list}
    """

    def get_contribs_for_one_issue(cur_issue: dict) -> dict:
        """
        TODO.

        Args:
            cur_issue (dict):

        Returns:
            TODO.
        """
        cur_entry: dict = {}
        commit_dict = cur_issue["pr"]["commits"]

        for _, commit in commit_dict.items():
            try:
                contrib_set.add(commit["author_name"])
            except KeyError:
                # A key error at this stage would mean that the commit
                # currently being looked at does not have any information
                # in the input, likely because it had no files changed and,
                # as a consequence, was not of interest to the project
                pass

        cur_entry["contributors"] = contrib_set

        # partition by closed date
        cur_entry["date"] = cur_issue["closed_at"]

        return cur_entry

    def issue_has_commits(issue: dict):
        """
        TODO.

        Args:
            issue (dict):

        Returns:
            TODO.
        """
        if issue["pr"]["commits"]:
            return True

        return False

    contrib_set: set = set()
    issue_contribs: dict = {}

    for issue_num, issue in issue_input.items():
        if issue_has_commits(issue):
            issue_contribs[issue_num] = get_contribs_for_one_issue(issue)

    return issue_contribs


def _get_core_contribs_per_timeframe(commit_input: dict):
    """
    TODO.

    Args:
        input_dict (dict):
    """
    core_contribs_per_timeframe: dict = {}

    for start_datetime_key in commit_input.keys():
        contrib_dict = commit_input[start_datetime_key]

        core_contribs: dict = _get_core_contributor_dict(contrib_dict)

        core_contribs_per_timeframe[start_datetime_key] = core_contribs

    return core_contribs_per_timeframe


def _get_core_contributor_dict(commit_dict: dict) -> dict:
    """
    Create a list of the core contributors of the given repository.

    Implements the Coelho et al. custom "Commit-Based Heuristic"
    algorithm: "the core team are those who produce 80% of the
    overall amount of commits in a project. However, as usually
    defined, this heuristic accepts developers with few
    contributions, regarding the total number of commits. For
    this reason, we customized the heuristic after some initial
    experiments to require core developers to have at least 5%
    of the total number of commits; candidates who have fewer
    commits are excluded."

    Citations:
        Coelho J, Valente MT, Silva LL, Hora A (2018) Why we engage in floss:
        Answers from core developers. In: Proceedings of the 11th International
        Workshop on Cooperative and Human Aspects of Software Engineering, pp
        114–121

        link: https://arxiv.org/pdf/1803.05741.pdf
    """

    def create_core_list(contrib_dict: dict) -> list:
        """
        TODO.

        Args:
            commit_dict (dict):

        Returns:
            list: unfiltered list of core contributors
        """
        contrib_list: list = list(contrib_dict["contributions"].items())
        core_thresh: int = math.floor(contrib_dict["num_commits"] * 0.8)

        contrib_sum: int = 0
        i: int = 0
        out_list: list = []

        while i < len(contrib_list) and contrib_sum < core_thresh:
            cur_entry = contrib_list[i]
            contrib_sum += cur_entry[1]
            out_list.append(cur_entry)
            i += 1

        return out_list

    def has_minimum_commit_quant(dev_commits, total_commits):
        """
        Check if a developer passes a commit percentage threshhold.

        The number of commits made by a developer must be at least 5%
        of total commits, whether for a time period or the entire repo
        history.

        Args:
            dev_commits (int): number of commits made by a developer.
            total_commits (int): total number of commits to check against.

        Returns:
            bool: true if a developer has at least 5% of total commits.
        """
        return dev_commits > total_commits * 0.05

    def rm_invalid_contribs_by_name(core_list: list) -> list:
        """
        Remove bots from list of core developers.

        Args:
            core_list (list): list of core developers to filter.

        Returns:
            list: list of core contributors with invalid contributors removed.
        """
        prohib_list: list = ["dependabot", "github actions"]

        # TODO: could be cleaned up. This is messy.
        for core_entry in core_list:
            for prohib_name in prohib_list:
                if prohib_name in core_entry[0]:
                    core_list.remove(core_entry)

        return core_list

    raw_core_contribs = create_core_list(commit_dict)

    filtered_core_contribs = [
        dev_entry
        for dev_entry in raw_core_contribs
        if has_minimum_commit_quant(dev_entry[1], commit_dict["num_commits"])
    ]

    core_devs: list = rm_invalid_contribs_by_name(filtered_core_contribs)

    return dict(core_devs)
