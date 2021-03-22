import os


def get_routing_key(src_path: str, root_dir: str = "./") -> str:
    """
    A small utility function that converts a file path to a routing key
    :param src_path: Event's source path
    :param root_dir: Directory to make root, must be an ancestor of src_path or
        it will have no effect. Defaults to current directory
    :return: Routing key
    """
    normalised_path = os.path.normpath(src_path)
    normalised_directory = os.path.normpath(root_dir)
    root_dir_relative_path = normalised_path.split(normalised_directory, 1)[1]

    head = os.path.splitext(root_dir_relative_path)[0]
    path_list = []

    while True:
        head, tail = os.path.split(head)
        if not tail:
            break

        path_list.append(tail)

    return '.'.join(reversed(path_list))
