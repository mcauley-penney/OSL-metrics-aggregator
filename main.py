"""
Storehouse for tools that derive social metrics from extractor data.

iGraph docs:
    • https://igraph.org/python/api/latest/

"""
import argparse
import json
from json.decoder import JSONDecodeError
import sys
import igraph

TAB = " " * 4


def main():
    """Top-level access point for gathering social metrics data."""
    in_json_path = get_cli_args()
    issues_dict = read_jsonfile_into_dict(in_json_path)

    produce_issue_dict_graphs(issues_dict)


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
        appearing in the order 1,2,3,4,1. Without and without
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
        for i in range(num_uniq_ids):
            key_id = uniq_id_list[i]

            # create list of all instances in discussant list of current id
            instance_list = [k for k, x in enumerate(id_list) if x == key_id]
            j = 0

            # loop over discussant_list up to last appearance of key id
            while j < instance_list[-1]:
                cur_id = id_list[j]

                if key_id != cur_id:
                    cur_id_matrix_index = uniq_id_list.index(cur_id)

                    # in the adjacency matrix row belonging to the current
                    # id, set all ids in the indices before the last instance
                    # of the current id to one
                    adj_mat[i][cur_id_matrix_index] = 1

                j += 1

        return adj_mat

    def print_adj_mat(matrix: list) -> None:
        i = 0
        for row in matrix:
            print(f"{i}: {row}")
            i += 1

        print("\n")

    id_list = get_discussants_list(issue_dict)
    uniq_id_list = get_unique_discussants(issue_dict)

    num_uniq_ids = len(uniq_id_list)

    # init empty adjacency matrix.
    # NOTE: avoid creating references to existing object!
    # https://docs.python.org/3/faq/programming.html#how-do-i-create-a-multidimensional-list
    adj_mat = [[0] * num_uniq_ids for _ in range(num_uniq_ids)]

    # require that each node connects to all prior nodes.
    # minimum density will be 50% in graphs with more than
    # 1 vertex.
    for i in range(num_uniq_ids):
        for j in range(i):
            adj_mat[i][j] = 1

    adj_mat = mark_recurring_id_instances(adj_mat, id_list, uniq_id_list, num_uniq_ids)

    return adj_mat


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

    # add repo input CLI arg
    arg_parser.add_argument(
        "extractor_data_path",
        help="Path to Extractor output, the data to produce metrics from",
    )

    return arg_parser.parse_args().extractor_data_path


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


def get_issue_wordiness(issuecmmnt_dict: dict):
    """
    Count the amount of words over a length of 2 in each comment in an issue.

    :param issuecmmnt_dict: dictionary of comments for an issue
    :type issuecmmnt_dict: dict
    """
    sum_wc = 0

    for comment in issuecmmnt_dict.values():
        body = comment["body"]

        # get all words greater in len than 2
        split_body = [word for word in body.split() if len(word) > 2]

        sum_wc += len(split_body)

    return sum_wc


def get_num_uniq_discussants(issuecmmnt_dict: dict):
    """
    TODO.

    :param issuecmmnt_dict:
    :type issuecmmnt_dict: dict
    :return:
    :rtype:
    """
    return len(get_unique_discussants(issuecmmnt_dict))


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


def print_graph_data(key: str, graph, adj_mat: list, discussants_set: list) -> None:
    """
    Print graph data. Used for debugging.

    :param key: key of issue
    :type key: str
    :param adj_mat: matrix for discussant relations
    :type adj_mat: list
    :param discussants_list: list of discussants
    :type discussants_list: list
    """
    index = 0

    print(f"{key}:")
    print(f"{TAB}discussants:")
    for discussant in discussants_set:
        print(f"{TAB * 2}{index}: {discussant}")
        index += 1

    index = 0
    print()
    print(f"{TAB}matrix:")
    for adj_list in adj_mat:
        print(f"{TAB * 2}{index}: {adj_list}")
        index += 1

    print()
    print(f"{TAB}graph data:")
    print(f"{TAB * 2}diameter    : {graph.diameter()}")
    print(f"{TAB * 2}edges       : {graph.ecount()}")
    print(f"{TAB * 2}vertices    : {graph.vcount()}")
    print(f"{TAB * 2}density     : {graph.density()}")
    print(f"{TAB * 2}betweenness : {graph.betweenness()}")
    print(f"{TAB * 2}closeness   : {graph.closeness()}")

    print("\n")


def produce_graph_obj(adj_mat: list):
    """
    Create a weighted adjacency graph.

        • https://igraph.org/python/api/latest/igraph.Graph.html
        • https://igraph-help.nongnu.narkive.com/uYWZB0DX/igraph-graph-from-an-adjacency-matrix
    """
    graph_obj = igraph.Graph()

    adj_graph = graph_obj.Adjacency(adj_mat, mode="directed")

    return adj_graph


def produce_issue_dict_graphs(issue_dict: dict):
    """
    TODO.

    :param issue_dict:
    :type issue_dict: dict
    """
    # for each issue in the issue dictionary
    for key, val in issue_dict.items():
        # create list of discussants
        discussant_set = get_unique_discussants(val)

        # create matrix
        adj_mat = create_adjacency_matrix(val)

        # create graph object
        graph = produce_graph_obj(adj_mat)

        print_graph_data(key, graph, adj_mat, discussant_set)

        # plot graph
        print(f"{TAB}Plotting issue #{key}", end="\r", file=sys.stderr)
        get_graph_plot(graph, discussant_set, f"data/output/graphs/{key}")

    print()


def read_file_into_text(in_path: str) -> str:
    """
    Read file contents into string.

    Used for reading JSON data out of JSON files.

    :raises FileNotFoundError: no file found at given path

    :param in_path: path to file to read contents from
    :type in_path: str
    :return: text from file
    :rtype: str
    """
    try:
        with open(in_path, "r", encoding="UTF-8") as file_obj:
            json_text = file_obj.read()

    except FileNotFoundError:
        print(f'\nFile at "{in_path}" not found!')
        sys.exit(1)

    else:
        return json_text


def read_jsonfile_into_dict(in_path: str) -> dict:
    """
    Read the contents of the provided JSON file into a dictionary.

    :param in_path: path to JSON file to read from
    :type in_path: str
    :return: dictionary constructed from JSON contents
    :rtype: dict
    """
    json_text = read_file_into_text(in_path)

    json_dict = read_jsontext_into_dict(json_text)

    return json_dict


def read_jsontext_into_dict(json_text: str) -> dict:
    """
    Convert text from JSON file into a python dict.

    :raises JSONDecodeError: contents of str param are not valid JSON

    :param json_text: text from JSON file
    :type json_text: str
    :return: dictionary of contents from JSON file
    :rtype: dict
    """
    try:
        json_dict = json.loads(json_text)

    # if no JSON content exists there, ignore. In this context, it simply
    # means that we are writing JSON to a new file
    except JSONDecodeError:
        return {}

    else:
        return json_dict


if __name__ == "__main__":
    main()
