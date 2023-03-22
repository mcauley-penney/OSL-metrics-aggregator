"""Tools for gathering metrics about the communicators in a repo's issues."""

from concurrent import futures
from datetime import datetime, timedelta
import math
import igraph
import networkx
from metrics_aggregator import __hierarchy as hierarchy


TAB = " " * 4


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
    res: dict = {}
    workers: int = 10

    print(f"\n{TAB}Partitioning issues into temporal periods...")
    issue_buckets: dict = create_partitioned_issue_dict(issue_data)
    print(f"{TAB*2}- {len(issue_data.keys())} keys")
    print(f"{TAB*2}- {len(issue_buckets.keys())} buckets\n")

    with futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for period, issue_nums in issue_buckets.items():
            print(f"{TAB}Launching #{period}: {len(issue_nums)} issues...")
            res |= {
                period: executor.submit(
                    gather_single_period_comm_metrics,
                    issue_data,
                    issue_nums,
                    period
                )
            }

        res = {period: f.result() for (period, f) in res.items()}

    return res


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

    def datetime_to_github_time_str(date: datetime) -> str:
        return datetime.strftime(date, "%m/%d/%y, %I:%M:%S %p")

    def get_start_date(issue_data: dict) -> datetime:
        """
        TODO.
        Args:
            issue_data (dict):
        Returns:
            datetime.datetime:
        """
        first_item_val = list(issue_data.values())[0]
        start_date: str = first_item_val["closed_at"].split(",")[0]

        return datetime.strptime(start_date, "%m/%d/%y")

    def github_time_str_to_datetime(date: str) -> datetime:
        return datetime.strptime(date, "%m/%d/%y, %I:%M:%S %p")

    def init_issue_interval_dict_keys(issues: dict) -> dict:
        interval: timedelta = timedelta(weeks=12, days=0)
        issue_interval_data: dict = {}
        start_date: datetime = get_start_date(issues)

        while start_date < datetime.now():
            next_interval_start = start_date + interval
            interval_date_str = datetime_to_github_time_str(next_interval_start)
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


def gather_single_period_comm_metrics(issue_data: dict, issue_nums: list, period_name):
    """
    Gather all communication metrics for one temporal period.

    Args:
        period ():
        issue_nums ():
    """
    keys: dict = {"keys": issue_nums}

    cur_bucket_graph: igraph.Graph = make_igraph_period_network_matrix(issue_data, issue_nums)

    print(f"{TAB*2} #{period_name}: getting period-issue metrics...\n")

    period_issue_metrics: dict = get_period_issue_metrics(cur_bucket_graph, issue_data, issue_nums)

    # fast, doesn't need print statement
    igraph_metrics = get_igraph_graph_metrics(cur_bucket_graph)

    print(f"{TAB*2} #{period_name}: getting networkx metrics...\n")

    networkx_metrics = get_networkx_graph_metrics(cur_bucket_graph)

    print(f"{TAB*2} #{period_name}: done\n")

    return {
        **keys,
        **period_issue_metrics,
        **igraph_metrics,
        **networkx_metrics,
    }


def get_period_issue_metrics(graph: igraph.Graph, issue_data, issue_nums) -> dict:
    """
    TODO.

    Args:
        issue_data ():
        issue_nums ():
        graph:

    Returns:
        todo.

    """
    def create_dev_role_metric_dict(graph: igraph.Graph) -> dict:
        """
        TODO.

        Args:
            graph:

        Returns:
            todo.

        """
        metrics: dict = {}

        try:
            vseq = graph.vs["name"]
        except KeyError:
            return {}

        betweenness = graph.betweenness()
        closeness = graph.closeness()

        # can get names of vertices, userids in our case, with graph.vs()["name"]
        for index, userid in enumerate(vseq):
            metrics[userid] = {
                "betweenness": betweenness[index],
                "closeness": closeness[index],
            }

        return metrics

    def get_issue_set(issue) -> set:
        participants: set = set()

        participants.add(issue["userid"])

        for _, comment in issue["comments"].items():
            participants.add(comment["userid"])

        return participants

    def get_issue_metrics(participants, metrics) -> dict:
        betweennesses: list = []
        closenesses: list = []

        for participant in participants:
            cur_metrics = metrics[participant]
            betweennesses.append(cur_metrics["betweenness"])
            closenesses.append(cur_metrics["closeness"])

        return {"betweenness": betweennesses, "closeness": closenesses}

    period_issue_metrics: dict = {}

    # consider using https://igraph.readthedocs.io/en/main/api/igraph.VertexSeq.html#select
    dev_role_metrics: dict = create_dev_role_metric_dict(graph)

    for num in issue_nums:
        cur_issue: dict = issue_data[num]

        # get who participated in the issue
        issue_participants: set = get_issue_set(cur_issue)

        # get their values from dev_role_metrics
        metrics = get_issue_metrics(issue_participants, dev_role_metrics)

        # send to be calculated
        period_issue_metrics[num] = {
            "participants": list(issue_participants),
            **aggregate_node_metric(metrics["betweenness"], "betweenness"),
            **aggregate_node_metric(metrics["closeness"], "closeness"),
        }

    return {"per_period_issue": period_issue_metrics}


def make_igraph_period_network_matrix(issue_data: dict, period_issue_nums: list) -> igraph.Graph:
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
        cur_bucket_graph = make_igraph_issue_network_matrix(issue_data[num], cur_bucket_graph)

    return cur_bucket_graph


def make_igraph_issue_network_matrix(cur_issue: dict, graph: igraph.Graph) -> igraph.Graph:
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
    # TODO: can use sets?
    issue_nodes: list = []
    edges: list = []

    # idempotently add the original poster of the issue
    cur_vertex, graph = idempotent_add(cur_issue["userid"], graph)
    issue_nodes.append(cur_vertex)

    for _, comment in cur_issue["comments"].items():
        # idempotently add each commenter
        cur_vertex, graph = idempotent_add(comment["userid"], graph)
        issue_nodes.append(cur_vertex)

        edges.extend(
            (cur_vertex, present_vertex)
            for present_vertex in issue_nodes
            if cur_vertex["name"] != present_vertex["name"]
        )

    graph.add_edges(edges)

    return graph


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

    node_eff_sz: dict = networkx.effective_size(nx_graph)
    node_efficiencies: dict = global_efficiency(nx_graph, node_eff_sz)
    node_hierarchies: dict = hierarchy.global_hierarchy(nx_graph)

    return {
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
        Alternative implementations:
            [
                ((sz / degree) if (degree := graph.degree(node)) > 0 else 0)
                for node, sz in esize.items()
            ]

            Note: ":=" operator available in >=Python 3.8

    Args:
        graph ():
    """
    return {node: efficiency(graph.degree(node), sz) for node, sz in esize.items()}


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

    return {
        # Structural Holes of Communication
        **aggregate_node_metric(graph.constraint(), "constraint"),
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
        return aggregates

    for key, val in {
        sum_key: sum(clean_metrics),
        max_key: max(clean_metrics),
        avg_key: sum(clean_metrics) / num_nodes,
    }.items():
        aggregates[key] = val

    return aggregates
