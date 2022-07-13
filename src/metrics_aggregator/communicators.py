"""Tools for gathering metrics about the communicators in a repo's issues."""

# TODO:
# 1. update docstrings
#   - include info on what each function needs from the input data to operate
#       - eg making the graphs needs issue comments, issue bodies, etc.
#           - document ALL items

import datetime
import igraph

TAB = " " * 4


def gather_all_issues_comm_metrics(issue_data: dict) -> dict:
    """
    Create a dictionary of metrics for all issues in a dictionary of issues.

    Notes:
        This functionality requires:
            - issue number
            - closure date
            - userid
            - issue comments
                - userid
                - comment body

    Args:
        issue_data (dict): dict of data about all issues of interest in a
        repository's history.

    Returns:
        dict: {period str: dict of metrics from graph of "conversation" for
                period key}
    """
    cur_bucket_metrics: dict = {}
    total_metrics: dict = {}

    issue_buckets: dict = create_partitioned_issue_dict(issue_data)

    for period, issue_nums in issue_buckets.items():
        cur_bucket_graph = make_period_network_matrix(issue_data, issue_nums)

        cur_bucket_metrics = get_graph_metric_dict(cur_bucket_graph)

        total_metrics[period] = cur_bucket_metrics

    return total_metrics


def make_issue_network_matrix(
    cur_issue: dict, cur_graph: igraph.Graph
) -> igraph.Graph:
    """
    Create an adjacency matrix for participants in one issue conversation.

    Notes:
        This functionality requires:
            - userid
            - issue comments
                - userid

    Args:
        cur_issue (dict):
        cur_graph (igraph.Graph):

    Returns:
        igraph.Graph: graph object update with nodes and edges from the
        conversation that transpired in the given issue parameter
    """
    # TODO: add comment about why we are using this list
    cur_node_list: list = []

    # idempotently add the original poster of the issue
    userid: str = cur_issue["userid"]

    try:
        cur_vertex_obj = cur_graph.vs.find(name=userid)

    except ValueError:
        cur_vertex_obj = cur_graph.add_vertex(name=userid)

    cur_node_list.append(cur_vertex_obj)

    for _, comment in cur_issue["comments"].items():

        # idempotently add each commenter
        userid = comment["userid"]

        # add vertices idempotently
        try:
            cur_vertex_obj = cur_graph.vs.find(name=userid)

        except ValueError:
            cur_vertex_obj = cur_graph.add_vertex(name=userid)

        cur_node_list.append(cur_vertex_obj)

        # for each vertex added to the current graph, add an edge
        # from the current vertex.
        for added_vertex in cur_node_list:
            try:
                cur_graph.es.find(_between=([cur_vertex_obj], [added_vertex]))

            # if there is no edge present, add the edge and init
            # the weight.
            except ValueError:
                # only continue if we the current vertex is
                # not being compared to itself
                if cur_vertex_obj["name"] != added_vertex["name"]:
                    cur_graph.add_edge(cur_vertex_obj, added_vertex)
                    cur_graph[cur_vertex_obj, added_vertex] = 1

            else:
                cur_graph[cur_vertex_obj, added_vertex] += 1

    return cur_graph


def make_period_network_matrix(
    issue_data: dict, period_issue_nums: list
) -> igraph.Graph:
    """
    TODO.

    Args:
        period_num_list ():
        issue_data (dict):

    Returns:
        igraph.Graph: graph of social network for period
    """
    cur_bucket_graph = igraph.Graph(directed=True)

    for num in period_issue_nums:
        cur_bucket_graph = make_issue_network_matrix(
            issue_data[num], cur_bucket_graph
        )

    return cur_bucket_graph


# TODO: could be a lot smarter, I think
def create_partitioned_issue_dict(issue_data: dict) -> dict:
    """
    Partition all input issues into a dictionary of time frames.

    Each key is a string of a date and each val is a list of issue numbers
    that fall into that time frame.

    Note, 07/07/2022:
        The values of each key are issues that were closed
        before the date of the key but after the last key. If an issue was
        closed on March 1st, the last key was February 1st, and the current key
        is April 1st, the issue closed on March 1st belongs in the April 1st
        key.

    Args:
        issue_data (dict): dictionary of data mined about the issues in a
        repository's history.

    Returns:
        dict: {date string: python list of issue nums}
    """

    def datetime_to_github_time_str(date: datetime.datetime) -> str:
        return datetime.datetime.strftime(date, "%m/%d/%y, %I:%M:%S %p")

    def get_start_date(issue_data: dict) -> datetime.datetime:
        """
        TODO.

        Args:
            issue_data (dict):

        Returns:
            datetime.datetime:
        """
        first_item_val = list(issue_data.values())[0]
        start_date: str = first_item_val["closed_at"].split(",")[0]

        return datetime.datetime.strptime(start_date, "%m/%d/%y")

    def github_time_str_to_datetime(date: str) -> datetime.datetime:
        return datetime.datetime.strptime(date, "%m/%d/%y, %I:%M:%S %p")

    def init_issue_interval_dict_keys(issues: dict) -> dict:

        interval: datetime.timedelta = datetime.timedelta(weeks=12, days=0)
        issue_interval_data: dict = {}
        start_date: datetime.datetime = get_start_date(issues)

        while start_date < datetime.datetime.now():
            next_interval_start = start_date + interval
            interval_date_str = datetime_to_github_time_str(
                next_interval_start
            )
            issue_interval_data[interval_date_str] = []
            start_date = next_interval_start

        return issue_interval_data

    issue_interval_data = init_issue_interval_dict_keys(issue_data)
    date_key_list = list(issue_interval_data.keys())

    for key, val in issue_data.items():
        cur_date = github_time_str_to_datetime(val["closed_at"])

        # NOTE: could use binary search if performance became an issue
        i = 0
        while cur_date > github_time_str_to_datetime(date_key_list[i]):
            i += 1

        issue_interval_data[date_key_list[i]].append(key)

    return issue_interval_data


def get_graph_metric_dict(graph: igraph.Graph) -> dict:
    """
    Get metrics of interest about a social network from the network's graph.

    Args:
        graph(igraph.Graph): graph of conversation from issues in some time
        period.

    Returns:
        dict: dict of social metrics derived from the input graph.
    """
    return {
        "betweenness": graph.betweenness(),
        "closeness": graph.closeness(),
        "density": graph.density(),
        "diameter": graph.diameter(),
        "edges": graph.ecount(),
        "vertices": graph.vcount(),
    }


def get_discussants_list(issue_dict: dict) -> list[str]:
    """
    TODO.

    :param issue_dict:
    :type issue_dict: dict
    :return: list of discussants in issue, including original poster
    :rtype: list
    """
    id_list = [issue_dict["userid"]]

    id_list += [
        comment["discussant"]["userid"]
        for comment in issue_dict["issue_comments"].values()
        if isinstance(comment["discussant"]["userid"], str)
    ]

    return id_list


def get_graph_plot(graph, path: str):
    """
    TODO.

    :param graph_obj:
    :type graph_obj:
    :param discussant_list:
    :type discussant_list: list
    """
    igraph.plot(graph, bbox=(200, 200), target=f"{path}.png")


def get_issue_wordiness(issue_dict: dict) -> int:
    """
    Count the amount of words over a length of 2 in each comment in an issue.

    :param issuecmmnt_dict: dictionary of comments for an issue
    :type issuecmmnt_dict: dict
    """
    sum_wc = 0

    try:
        sum_wc += len(
            [
                word
                for word in issue_dict["body"].split()
                if len(word) > 2 and word != "Nan"
            ]
        )

    except KeyError:
        # TODO: comment: why pass?
        pass

    for comment in issue_dict["issue_comments"].values():
        body = comment["body"]

        # get all words greater in len than 2
        split_body = [word for word in body.split() if len(word) > 2]

        sum_wc += len(split_body)

    return sum_wc


def get_unique_discussants(issue_dict: dict) -> list:
    """
    Create set of discussants in a dictionary of comments on an issue.

    TODO:
    :param issuecmmnt_dict:
    :type issuecmmnt_dict: dict
    :return:
    :rtype:
    """
    discussant_list = get_discussants_list(issue_dict)

    discussants_set = list(dict.fromkeys(discussant_list))

    return discussants_set
