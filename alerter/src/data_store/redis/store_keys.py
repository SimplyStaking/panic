# TODO: Need to be rebuilt as we go along in development. Basically, redis uses
#       hashed keys, so these are not known before. What we must keep in mind
#       is that for a chain, there must be only 1 node with the same name
#       (This was enforced in the setup but not in the config parsing).
#       Hash(Chain) -> Key(node)
