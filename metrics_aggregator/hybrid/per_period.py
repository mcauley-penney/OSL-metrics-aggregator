"""Hybrid period metrics combine issue-level and whole-period aggregates."""

from concurrent import futures
from datetime import datetime, timedelta
import math
import igraph
import networkx
from metrics_aggregator import __hierarchy as hierarchy


TAB = " " * 4
TIME_FMT = "%m/%d/%y, %I:%M:%S %p"


def gather_all_period_comm_metrics(issue_data: dict) -> dict:
    """
    Create a dictionary of period metrics for all issues in a repository.

    The hybrid pipeline emits nested per-period issue metrics and whole-period
    graph aggregates.
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
                    period,
                )
            }

        res = {period: future.result() for (period, future) in res.items()}

    return res


def create_partitioned_issue_dict(issue_data: dict) -> dict:
    """
    Partition input issues into 12-week periods keyed by period end date.
    """

    def datetime_to_github_time_str(date: datetime) -> str:
        return datetime.strftime(date, TIME_FMT)

    def github_time_str_to_datetime(date: str) -> datetime:
        return datetime.strptime(date, TIME_FMT)

    def get_start_date(issues: dict) -> datetime:
        first_item_val = list(issues.values())[0]
        return github_time_str_to_datetime(first_item_val["closed_at"])

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

        i = 0
        while cur_date > github_time_str_to_datetime(date_key_list[i]):
            i += 1

        issue_interval_data[date_key_list[i]].append(key)

    return issue_interval_data


def gather_single_period_comm_metrics(issue_data: dict, issue_nums: list, period_name: str) -> dict:
    """
    Gather all communication metrics for one temporal period.
    """
    keys: dict = {"keys": issue_nums}
    cur_bucket_graph: igraph.Graph = make_igraph_period_network_matrix(issue_data, issue_nums)

    print(f"{TAB*2} #{period_name}: getting period-issue metrics...\n")
    period_issue_metrics: dict = get_period_issue_metrics(cur_bucket_graph, issue_data, issue_nums)

    print(f"{TAB*2} #{period_name}: getting whole-period graph metrics...\n")
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


def get_period_issue_metrics(graph: igraph.Graph, issue_data: dict, issue_nums: list) -> dict:
    """
    Gather issue-level metrics derived from each issue's participants in the
    period graph.
    """

    def create_dev_role_metric_dict(cur_graph: igraph.Graph) -> dict:
        metrics: dict = {}

        try:
            vertex_names = cur_graph.vs["name"]
        except KeyError:
            return {}

        betweenness = cur_graph.betweenness()
        closeness = cur_graph.closeness()

        for index, userid in enumerate(vertex_names):
            metrics[userid] = {
                "betweenness": betweenness[index],
                "closeness": closeness[index],
            }

        return metrics

    def get_issue_set(issue: dict) -> set:
        participants: set = {issue["userid"]}

        for _, comment in issue["comments"].items():
            participants.add(comment["userid"])

        return participants

    def get_issue_metrics(participants: set, metric_lookup: dict) -> dict:
        betweennesses: list = []
        closenesses: list = []

        for participant in participants:
            cur_metrics = metric_lookup[participant]
            betweennesses.append(cur_metrics["betweenness"])
            closenesses.append(cur_metrics["closeness"])

        return {"betweenness": betweennesses, "closeness": closenesses}

    period_issue_metrics: dict = {}
    dev_role_metrics: dict = create_dev_role_metric_dict(graph)

    for num in issue_nums:
        cur_issue: dict = issue_data[num]
        issue_participants: set = get_issue_set(cur_issue)
        metrics = get_issue_metrics(issue_participants, dev_role_metrics)

        period_issue_metrics[num] = {
            "participants": sorted(issue_participants),
            **aggregate_node_metric(metrics["betweenness"], "betweenness"),
            **aggregate_node_metric(metrics["closeness"], "closeness"),
        }

    return {"per_period_issue": period_issue_metrics}


def make_igraph_period_network_matrix(issue_data: dict, period_issue_nums: list) -> igraph.Graph:
    """
    Create a graph of all communication in a single period.
    """
    cur_bucket_graph = igraph.Graph(directed=True)

    for num in period_issue_nums:
        cur_bucket_graph = make_igraph_issue_network_matrix(issue_data[num], cur_bucket_graph)

    return cur_bucket_graph


def make_igraph_issue_network_matrix(cur_issue: dict, graph: igraph.Graph) -> igraph.Graph:
    """
    Add the communication edges for one issue to the running graph.
    """
    issue_nodes: list = []
    edges: list = []

    cur_vertex, graph = idempotent_add(cur_issue["userid"], graph)
    issue_nodes.append(cur_vertex)

    for _, comment in cur_issue["comments"].items():
        cur_vertex, graph = idempotent_add(comment["userid"], graph)
        issue_nodes.append(cur_vertex)

        edges.extend(
            (cur_vertex, present_vertex)
            for present_vertex in issue_nodes
            if cur_vertex["name"] != present_vertex["name"]
        )

    graph.add_edges(edges)

    return graph


def idempotent_add(userid: str, graph: igraph.Graph):
    """
    Add a vertex only if it does not already exist.
    """
    try:
        vertex_obj = graph.vs.find(name=userid)

    except ValueError:
        vertex_obj = graph.add_vertex(name=userid)

    return vertex_obj, graph


def get_networkx_graph_metrics(ig_graph: igraph.Graph) -> dict:
    """
    Get NetworkX-specific aggregates from an iGraph graph.
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


def calc_aggregates_from_dict(node_data: dict, metric_name: str) -> dict:
    """
    Return aggregate values for the values in a node-keyed metric dictionary.
    """
    node_vals: list = list(node_data.values())

    return aggregate_node_metric(node_vals, metric_name)


def global_efficiency(graph, effective_sizes: dict) -> dict:
    """
    Produce efficiencies for all nodes in a network.
    """
    return {
        node: efficiency(graph.degree(node), effective_size)
        for node, effective_size in effective_sizes.items()
    }


def efficiency(degree: int, effective_size: int):
    """
    Get the efficiency between a node and one of its neighbors.
    """
    if degree == 0:
        return 0

    return effective_size / degree


def get_igraph_graph_metrics(graph: igraph.Graph) -> dict:
    """
    Get whole-period aggregates derived directly from the period graph.
    """
    return {
        "edges": graph.ecount(),
        "vertices": graph.vcount(),
        "density": graph.density(),
        "diameter": graph.diameter(),
        **aggregate_node_metric(graph.constraint(), "constraint"),
        **aggregate_node_metric(graph.betweenness(), "betweenness"),
        **aggregate_node_metric(graph.closeness(), "closeness"),
    }


def aggregate_node_metric(node_metrics: list, metric_name: str) -> dict:
    """
    Return min, avg, max, and sum for a node-level metric list.
    """
    aggregates: dict = {}

    min_key: str = metric_name + "_" + "min"
    avg_key: str = metric_name + "_" + "avg"
    max_key: str = metric_name + "_" + "max"
    sum_key: str = metric_name + "_" + "sum"

    for metric_type in (min_key, avg_key, max_key, sum_key):
        aggregates[metric_type] = 0

    if len(node_metrics) == 0:
        return aggregates

    clean_metrics: list = [val for val in node_metrics if not math.isnan(val)]
    num_nodes = len(clean_metrics)

    if num_nodes == 0:
        return aggregates

    for key, val in {
        min_key: min(clean_metrics),
        sum_key: sum(clean_metrics),
        max_key: max(clean_metrics),
        avg_key: sum(clean_metrics) / num_nodes,
    }.items():
        aggregates[key] = val

    return aggregates
