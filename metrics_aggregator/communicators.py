"""Tools for gathering metrics about the communicators in a repo's issues."""

import datetime
import math
import igraph
import networkx
from metrics_aggregator import hierarchy


CLR = "\x1b[K"
TAB = " " * 4


def gather_all_issue_comm_metrics(issue_data: dict) -> dict:
    """
    Gather per-issue metrics from repo data.

    Args:
        issue_data (dict): dictionary of {issue_num: issue_data} key pairs.

    Returns:
        dict of dicts: {issue_num: {issue_metrics}}

    """
    per_issue_metrics: dict = {}

    print()
    print(f"{TAB}Gathering per-issue metrics...")

    for issue, data in issue_data.items():
        per_issue_metrics[issue] = {
            "num_comments": len(list(data["comments"])),
            "num_discussants": len(get_unique_discussants(data)),
            "wordiness": get_issue_wordiness(data),
        }

    print(f"{TAB * 2}Done!")

    return per_issue_metrics


def gather_all_period_comm_metrics(issue_data: dict) -> dict:
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
    igraph_metrics: dict = {}
    networkx_metrics: dict = {}
    total_metrics: dict = {}

    print()
    print(f"{TAB}Partitioning issues into temporal periods...")
    issue_buckets: dict = create_partitioned_issue_dict(issue_data)
    print(f"{TAB*2}{len(issue_buckets.keys())} buckets to process...\n")

    print(f"{TAB}Calculating metrics...")
    for period, issue_nums in issue_buckets.items():

        keys: dict = {"keys": issue_nums}

        print(f'{CLR}{TAB * 2}Period: "{period}", Issues: {len(issue_nums)}')

        print(f"{TAB * 3}Producing graph...")
        cur_bucket_graph: igraph.Graph = make_igraph_period_network_matrix(
            issue_data, issue_nums
        )
        print(f"{TAB * 4}Done!")

        print(f"{TAB * 3}Gathering iGraph metrics...")
        igraph_metrics = get_igraph_graph_metrics(cur_bucket_graph)
        print(f"{TAB * 4}Done!")

        print(f"{TAB * 3}Gathering NetworkX metrics...")
        networkx_metrics = get_networkx_graph_metrics(cur_bucket_graph)
        print(f"{TAB * 4}Done!")

        total_metrics[period] = {
            **keys,
            **igraph_metrics,
            **networkx_metrics,
        }

    print(f"\n\n{TAB}Metrics calculation complete!")

    return total_metrics


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


def make_igraph_period_network_matrix(
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
        cur_bucket_graph = make_igraph_issue_network_matrix(
            issue_data[num], cur_bucket_graph
        )

    return cur_bucket_graph


def make_igraph_issue_network_matrix(
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
    cur_node_list: list = []

    # idempotently add the original poster of the issue
    userid: str = cur_issue["userid"]

    cur_vertex_obj, cur_graph = idempotent_add(userid, cur_graph)
    cur_node_list.append(cur_vertex_obj)

    for _, comment in cur_issue["comments"].items():

        # idempotently add each commenter
        userid = comment["userid"]

        cur_vertex_obj, cur_graph = idempotent_add(userid, cur_graph)
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


def idempotent_add(userid, graph):
    """
    TODO: update name, finish docstring.

    Args:
        userid ():
        graph ():

    Returns:
        vertex_obj:
        graph:
    """
    try:
        vertex_obj = graph.vs.find(name=userid)

    except ValueError:
        vertex_obj = graph.add_vertex(name=userid)

    return vertex_obj, graph


def get_networkx_graph_metrics(ig_graph: igraph.Graph):
    """
    Get NetworkX-specific metrics from an iGraph graph.

    Args:
        graph (igraph.Graph): igraph graph to convert to NetworkX
    """
    nx_graph = ig_graph.to_networkx()

    node_constraints: dict = networkx.constraint(nx_graph)
    node_eff_sz: dict = networkx.effective_size(nx_graph)
    node_efficiencies: dict = global_efficiency(nx_graph, node_eff_sz)
    node_hierarchies: dict = hierarchy.global_hierarchy(nx_graph)

    return {
        **calc_aggregates_from_dict(node_constraints, "constraint"),
        **calc_aggregates_from_dict(node_eff_sz, "effective_size"),
        **calc_aggregates_from_dict(node_efficiencies, "efficiency"),
        **calc_aggregates_from_dict(node_hierarchies, "hierarchy"),
    }


def calc_aggregates_from_dict(node_data: dict, metric_name: str):
    """
    TODO.

    Args:
        node_data (dict):

    Returns:
        dict: aggregate values for list of node values

    """
    node_vals: list = list(node_data.values())

    return aggregate_node_metric(node_vals, metric_name)


def global_efficiency(graph, esize):
    """
    Produce list of efficiencies for all nodes in a network.

    Notes:
        Implementations:
            1. [
                ((sz / degree) if (degree := graph.degree(node)) > 0 else 0)
                for node, sz in esize.items()
            ]

            2. [
                efficiency(graph.degree(node), sz) for node, sz in
                esize.items()
            ]

        ":=" operator available in >=Python 3.8

    Args:
        graph ():
    """
    return {
        node: efficiency(graph.degree(node), sz) for node, sz in esize.items()
    }


def efficiency(degree: int, effective_size: int):
    """
    Get the efficiency between a node and one of it's neighbors.

    JUNG source code found at
    https://github.com/jrtom/jung/blob/1f579fe5d74ecbaecbe32ce6762e1fa9e17ed225/jung-algorithms/src/main/java/edu/uci/ics/jung/algorithms/metrics/StructuralHoles.java#L88-L104

    NetworkX notes on efficiency found at
    https://github.com/networkx/networkx/blob/36d446bae7059d9a6b2db742f3b75457f89db032/networkx/algorithms/structuralholes.py#L102-L106

    Args:
        graph ():
        node ():
        neighbor ():

    Returns:
        double
    """
    if degree == 0:
        return 0

    return effective_size / degree


def get_igraph_graph_metrics(graph: igraph.Graph) -> dict:
    """
    Get metrics of interest about a social network from the network's graph.

    Args:
        graph(igraph.Graph): graph of conversation from issues in some time
        period.

    Returns:
        dict: dict of social metrics derived from the input graph.
    """
    # TODO: can give weights to calculations to improve accuracy?
    return {
        "edges": graph.ecount(),
        "vertices": graph.vcount(),
        "density": graph.density(),
        "diameter": graph.diameter(),
        **aggregate_node_metric(graph.betweenness(), "betweenness"),
        **aggregate_node_metric(graph.closeness(), "closeness"),
    }


def aggregate_node_metric(node_metrics: list, metric_name: str):
    """
    Return aggregate values for the given metric.

    Currently used for:
        betweenness
        closeness
        constraint
        effective_size
        efficiency
        hierarchy

    Returns:
        dict:
    """
    aggregates: dict = {}

    avg_key: str = metric_name + "_" + "avg"
    max_key: str = metric_name + "_" + "max"
    sum_key: str = metric_name + "_" + "sum"

    for metric_type in (avg_key, max_key, sum_key):
        aggregates[metric_type] = 0

    if len(node_metrics) == 0:
        return aggregates

    clean_metrics: list = [val for val in node_metrics if not math.isnan(val)]
    num_nodes = len(clean_metrics)

    if num_nodes == 0:
        print(f"{TAB * 4}All nodes are NaN...")
        return aggregates

    for key, val in {
        sum_key: sum(clean_metrics),
        max_key: max(clean_metrics),
        avg_key: sum(clean_metrics) / num_nodes,
    }.items():
        aggregates[key] = val

    return aggregates


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
        comment["userid"]
        for comment in issue_dict["comments"].values()
        if isinstance(comment["userid"], str)
    ]

    return id_list


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
                if len(word) > 2 and word.lower() != "nan"
            ]
        )

    except KeyError:
        pass

    for comment in issue_dict["comments"].values():
        body = comment["body"]

        # get all words greater in len than 2
        split_body = [word for word in body.split() if len(word) > 2]

        sum_wc += len(split_body)

    return sum_wc
