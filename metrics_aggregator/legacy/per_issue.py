"""Legacy per-issue metrics."""


def gather_all_issue_comm_metrics(issue_data: dict) -> dict:
    """
    Gather per-issue metrics from repo data.

    Args:
        issue_data (dict): dictionary of {issue_num: issue_data} key pairs.

    Returns:
        dict of dicts: {issue_num: {issue_metrics}}

    """
    per_issue_metrics: dict = {}

    for issue, data in issue_data.items():
        per_issue_metrics[issue] = {
            "num_comments": len(list(data["comments"])),
            "num_discussants": len(get_unique_discussants(data)),
            "wordiness": get_issue_wordiness(data),
        }

    return per_issue_metrics


def get_unique_discussants(issue_dict: dict) -> list:
    """
    Create set of discussants in a dictionary of comments on an issue.
    """
    discussant_list = get_discussants_list(issue_dict)

    discussants_set = list(dict.fromkeys(discussant_list))

    return discussants_set


def get_discussants_list(issue_dict: dict) -> list[str]:
    """
    Return the list of discussants in an issue, including the original poster.
    """
    id_list = [issue_dict["userid"]]

    id_list += [
        comment["userid"]
        for comment in issue_dict["comments"].values()
        if isinstance(comment["userid"], str)
    ]

    return id_list


def get_issue_wordiness(issue_dict: dict) -> int:
    """
    Count the amount of words over a length of 2 in each comment in an issue.
    """
    sum_wc = 0

    try:
        sum_wc += len(
            [
                word
                for word in issue_dict["body"].split()
                if len(word) > 2 and word.lower() != "nan"
            ]
        )

    except (AttributeError, KeyError):
        pass

    for comment in issue_dict["comments"].values():
        body = comment["body"]
        split_body = [word for word in body.split() if len(word) > 2]
        sum_wc += len(split_body)

    return sum_wc
