"""TODO."""


import igraph
from metrics_aggregator.utils import dict_utils


def aggregate_issue_social_metrics(issue_dict: dict) -> dict:
    """
    TODO.

    :param issue_dict:
    :type issue_dict: dict
    """
    data_dict = {}

    # for each issue in the issue dictionary
    for key, val in issue_dict.items():
        # create matrix
        adj_mat = create_adjacency_matrix(val)

        # create graph object
        graph = create_igraph_adjacency_matrix_obj(adj_mat)

        cur_dict = {
            "betweenness": graph.betweenness(),
            "closeness": graph.closeness(),
            "density": graph.density(),
            "diameter": graph.diameter(),
            "edges": graph.ecount(),
            "vertices": graph.vcount(),
            "wordiness": get_issue_wordiness(val),
        }

        print(cur_dict)

        cur_dict = {key: cur_dict}

        data_dict = dict_utils.merge_dicts(data_dict, cur_dict)

        # plot graph
        # print(f"{TAB}Plotting issue #{key}", end="\r", file=sys.stderr)
        # get_graph_plot(graph, discussant_set, f"data/output/graphs/{key}")

    return data_dict


def create_adjacency_matrix(issue_dict: dict) -> list:
    """
    Create an adjacency matrix for participants in one Issue conversation.

    :param issue_dict: dictionary of data for one issue
    :type issue_dict: dict
    :return: adjacency matrix
    :rtype: list of lists of integers
    """

    def mark_recurring_id_instances(
        adj_mat: list[list[int]],
        id_list: list[str],
        uniq_id_list: list[str],
        num_uniq_ids: int,
    ) -> list[list[int]]:
        """
        Update an adjacency matrix with edges between recurring and prior users.

        In the conversation in a GitHub issue, a commenter
        (which includes the original poster) might comment
        again. We would like to create edges between this
        users and the users they are responding to.

        An example of this might be a conversation with ID's
        appearing in the order 1,2,3,4,1. Without and with
        marking the recurring ID, we have the matrices:

            0,0,0,0     0,1,1,1
            1,0,0,0     1,0,0,0
            1,1,0,0     1,1,0,0
            1,1,1,0     1,1,1,0

        We desire the second format.

        :param adj_mat: adjacency matrix to update
        :type adj_mat: list[list[int]]
        :param id_list: list of IDs, including duplicates, in the order
            they appear in the conversation
        :type id_list: list[str]
        :param uniq_id_list: list of IDs, without duplicates. Essentially
            a set
        :type uniq_id_list: list[str]
        :param num_uniq_ids: number of unique IDs in the list of unique IDs
        :type num_uniq_ids: int
        :return: updated adjacency matrix
        :rtype: list[list[int]]
        """
        # TODO: add more to the comments and
        # docstrings. This one could use it
        for i in range(num_uniq_ids):
            key_id = uniq_id_list[i]

            # create list of all instances in discussant list of
            # current id. This creates a list of indices in the
            # list of ID's where the key ID occurs
            instance_list = [k for k, x in enumerate(id_list) if x == key_id]
            j = 0

            # loop over discussant_list up to last appearance of key id
            while j < instance_list[-1]:
                cur_id = id_list[j]

                if cur_id != key_id:
                    cur_id_matrix_index = uniq_id_list.index(cur_id)

                    # in the adjacency matrix row belonging to the current
                    # id, set all ids in the indices before the last instance
                    # of the current id to one
                    adj_mat[i][cur_id_matrix_index] = 1

                j += 1

        return adj_mat

    id_list: list = get_discussants_list(issue_dict)
    uniq_id_list: list = get_unique_discussants(issue_dict)

    num_uniq_ids = len(uniq_id_list)

    # init empty adjacency matrix.
    # NOTE: avoid creating references to existing object!
    # https://docs.python.org/3/faq/programming.html#how-do-i-create-a-multidimensional-list
    adj_mat = [[0] * num_uniq_ids for _ in range(num_uniq_ids)]

    # require that each node connects to all prior nodes.
    # The minimum possible density will be 50% in graphs
    # with more than 1 vertex.
    for i in range(num_uniq_ids):
        for j in range(i):
            adj_mat[i][j] = 1

    adj_mat = mark_recurring_id_instances(adj_mat, id_list, uniq_id_list, num_uniq_ids)

    return adj_mat


def create_igraph_adjacency_matrix_obj(adj_mat: list):
    """
    Create a weighted adjacency graph.

        • https://igraph.org/python/api/latest/igraph.Graph.html
        • https://igraph-help.nongnu.narkive.com/uYWZB0DX/igraph-graph-from-an-adjacency-matrix
    """
    graph_obj = igraph.Graph()

    adj_graph = graph_obj.Adjacency(adj_mat, mode="directed")

    return adj_graph


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


def get_graph_plot(adj_graph, discussant_list: list, path: str):
    """
    TODO.

    :param graph_obj:
    :type graph_obj:
    :param discussant_list:
    :type discussant_list: list
    """
    settings = dict(layout="kamada_kawai", vertex_label=discussant_list)

    igraph.plot(adj_graph, f"{path}.pdf", **settings)


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
