from web3 import Web3

from src.utils.constants.abis import V3, V4

w3_v3 = Web3(Web3.HTTPProvider('http://172.16.152.65:8545',
                            request_kwargs={'timeout': 2}))
contract_v3 = w3_v3.eth.contract(
    address="0x05883D24a5712c04f1b843C4839dC93073A56Ef4", abi=V3)
address = w3_v3.toChecksumAddress("0x2607e6f021922a5483d64935f87e15ea797fe8d4")
print(address)
print(contract_v3.functions.withdrawablePayment(address).call())


contract_v4 = w3_v4.eth.contract(
    address="0x05883D24a5712c04f1b843C4839dC93073A56Ef4", abi=V4)
address = w3.toChecksumAddress("0x2607e6f021922a5483d64935f87e15ea797fe8d4")
print(address)
print(contract_v3.functions.withdrawablePayment(address).call())
# TODO: Tomorrow continue trying out every function
# TODO: Check for v3 or v4 and parse accordingly
# TODO: If neither v4 nor v3 do nothing
# TODO: Do not start evm contracts monitor if no evm url or no cl url
# TODO: pass parent_id, chain_name, node_name and some meta_data if any with
#     : current data
