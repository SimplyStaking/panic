# TODO: Need to be rebuilt as we go along in development. Basically, redis uses
#       hashed keys, so these are not known before. What we must keep in mind
#       is that for a chain, there must be only 1 node with the same name
#       (This was enforced in the setup but not in the config parsing).
#       Hash(Chain) -> Key(node)


# TODO: Change the default hashes according to new configuration

# Hashes
_hash_blockchain = "hash_bc1"
_hash_channel = "hash_ch1"

# eX_<email_id>
_key_email_id = "e1"
_key_email_config_name = "e2"
_key_email_smtp_config = "e3"
_key_email_from = "e4"
_key_email_to = "e5"
_key_email_username = "e6"
_key_email_password = "e7"
_key_email_info = "e8"
_key_email_warning = "e9"
_key_email_critical = "e9"
_key_email_error = "e9"

def _as_prefix(key) -> str:
    return key + "_"

class Keys:
    @staticmethod
    def get_hash_blockchain(chain_name: str) -> str:
        return _as_prefix(_hash_blockchain) + chain_name
    
    @staticmethod
    def get_hash_channel() -> str:
        return _as_prefix(_hash_channel) + "channel"

    @staticmethod
    def get_email_config_name(email_id: str) -> str:
        return _as_prefix(_key_email_config_name) + email_id

    @staticmethod
    def get_email_smtp_config(email_id: str) -> str:
        return _as_prefix(_key_email_smtp_config) + email_id

    @staticmethod
    def get_email_from(email_id: str) -> str:
        return _as_prefix(_key_email_from) + email_id

    @staticmethod
    def get_email_to(email_id: str) -> str:
        return _as_prefix(_key_email_to) + email_id

    @staticmethod
    def get_email_username(email_id: str) -> str:
        return _as_prefix(_key_email_username) + email_id

    @staticmethod
    def get_email_password(email_id: str) -> str:
        return _as_prefix(_key_email_password) + email_id

    @staticmethod
    def get_email_info(email_id: str) -> str:
        return _as_prefix(_key_email_info) + email_id

    @staticmethod
    def get_email_warning(email_id: str) -> str:
        return _as_prefix(_key_email_warning) + email_id

    @staticmethod
    def get_email_critical(email_id: str) -> str:
        return _as_prefix(_key_email_critical) + email_id

    @staticmethod
    def get_email_error(email_id: str) -> str:
        return _as_prefix(_key_email_error) + email_id