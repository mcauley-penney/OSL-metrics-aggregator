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


# TODO:
#   • do we need to include OP id in discussants set?
#       • if so, need to refactor
#           • matrix fn


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
    cmmnt_dict = issue_dict["issue_comments"]

    # get unique discussants set. This only counts the number of
    # commenters and does not include the original poster. We
    # must add one to the number of discussants to count the
    # poster.
    discussant_set = get_unique_discussants(cmmnt_dict)
    num_discussants = len(discussant_set) + 1
    node_list = []

    # init node list by adding node for original poster.
    # The conversation starts with the person who originally posted
    # the issue.
    creator_id = issue_dict["userid"]

    # if the original poster is also in the set of comment
    # discussants, we want to make sure that we do not take
    # any more info from that person. We consequently remove
    # them from the set and decrement the length of the set.
    if creator_id in discussant_set:
        discussant_set.remove(creator_id)
        num_discussants -= 1

    # append row in adjacency matrix for creator.
    # This person will have no edges connecting them to commenters
    # so we give them 0's for the number of discussants.
    node_list.append([0] * num_discussants)

    # if there are no discussants in the API object, i.e. no one
    # commented on an issue or PR, then return the list as is,
    # with just the original poster.
    if num_discussants > 0:
        for _, cmmnt in cmmnt_dict.items():

            discussant = cmmnt["discussant"]["userid"]

            if discussant in discussant_set:
                discussant_set.remove(discussant)

                # append 1's for each prior node. The 1's indicate that
                # this node will connect to the node at the index of the
                # 1, e.g. if there are five total nodes, the nodes that
                # come after the first will all connect to the first, so
                # the first index in each node list will have a one. All
                # adjacency matrices should appear the same, with a format
                # like
                #
                # [0, 0, 0]
                # [1, 0, 0]
                # [1, 1, 0]
                node = [1] * len(node_list) + [0] * (num_discussants - len(node_list))
                node_list.append(node)

    return node_list


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


def get_graph_plot(adj_graph, discussant_list: list, path: str):
    """
    TODO.

    :param graph_obj:
    :type graph_obj:
    :param discussant_list:
    :type discussant_list: list
    """
    settings = dict(layout="fruchterman_reingold", vertex_label=discussant_list)

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
    print(issue_dict)
    id_list = [issue_dict["userid"]]

    issuecmmnt_dict = issue_dict["issue_comments"]

    if len(issuecmmnt_dict) > 0:
        id_list += [
            comment["discussant"]["userid"]
            for comment in issuecmmnt_dict.values()
            if isinstance(comment["discussant"]["userid"], str)
        ]

        discussants_set = list(dict.fromkeys(id_list))

        return discussants_set

    return id_list


def print_graph_data(key: str, adj_mat: list, discussants_set: list) -> None:
    """
    Print graph data. Used for debugging.

    :param key: key of issue
    :type key: str
    :param adj_mat: matrix for discussant relations
    :type adj_mat: list
    :param discussants_list: list of discussants
    :type discussants_list: list
    """
    print(f"{key}:")
    print(f"{TAB}discussants:")
    for discussant in discussants_set:
        print(f"{TAB * 2}{discussant}")

    print(f"{TAB}matrix:")
    for adj_list in adj_mat:
        print(f"{TAB * 2}{adj_list}")

    print()


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

        print_graph_data(key, adj_mat, discussant_set)

        # create graph object
        # graph = produce_graph_obj(adj_mat)

        # # plot graph
        # get_graph_plot(graph, discussant_set, f"graphs/{key}")


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
