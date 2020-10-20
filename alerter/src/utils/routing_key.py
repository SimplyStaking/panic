import os


def get_routing_key(src_path: str, root_dir: str = "./") -> str:
    """
    A small utility function that converts a file path to a routing key
    :param src_path: Event's source path
    :param root_dir: Directory to make root, must be an ancestor of src_path or it will have no effect.
           Defaults to current directory
    :return: Routing key
    """
    normpath = os.path.normpath(src_path)
    normdir = os.path.normpath(root_dir)
    path_without_config_folder = normpath.split(normdir, 1)[1]

    head = os.path.splitext(path_without_config_folder)[0]
    path_list = []

    while True:
        head, tail = os.path.split(head)
        if not tail:
            break

        path_list.append(tail)

    return ".".join(reversed(path_list))
