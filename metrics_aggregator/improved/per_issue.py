"""TODO."""
import igraph


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
        comm_context = get_comm_context(data)
        network_props = get_comm_network_props(data)

        per_issue_metrics[issue] = {**comm_context, **network_props}

    return per_issue_metrics


def get_comm_context(data: dict) -> dict:
    return {
        "num_comments": len(list(data["comments"])),
        "num_discussants": len(get_unique_discussants(data)),
        "wordiness": get_issue_wordiness(data),
    }


def get_comm_network_props(data: dict) -> dict:
    graph = igraph.Graph(directed=True)
    graph = make_igraph_issue_network_matrix(data, graph)

    return {
        "edges": graph.ecount(),
        "vertices": graph.vcount(),
        "density": graph.density(),
        "diameter": graph.diameter(),
    }


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

    id_list += [comment["userid"] for comment in issue_dict["comments"].values() if isinstance(comment["userid"], str)]

    return id_list


def get_issue_wordiness(issue_dict: dict) -> int:
    """
    Count the amount of words over a length of 2 in each comment in an issue.

    :param issuecmmnt_dict: dictionary of comments for an issue
    :type issuecmmnt_dict: dict
    """
    sum_wc = 0

    try:
        sum_wc += len([word for word in issue_dict["body"].split() if len(word) > 2 and word.lower() != "nan"])

    except (AttributeError, KeyError):
        pass

    for comment in issue_dict["comments"].values():
        body = comment["body"]

        # get all words greater in len than 2
        split_body = [word for word in body.split() if len(word) > 2]

        sum_wc += len(split_body)

    return sum_wc
