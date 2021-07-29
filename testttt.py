from web3 import Web3

from src.utils.constants.abis import V3, V4

# xdai node
w3_v3 = Web3(Web3.HTTPProvider('http://172.16.152.65:8545',
                               request_kwargs={'timeout': 2}))
contract_v3 = w3_v3.eth.contract(
    address="0x4958D7a5309740926C868d7EcA0d9DCCAC0BcB4A", abi=V3)
address = w3_v3.toChecksumAddress("0x12d61a95CF55e18D267C2F1AA67d8e42ae1368f8")
print(address)
print(contract_v3.functions.withdrawablePayment(address).call())

# # geth node
# w3_v4 = Web3(Web3.HTTPProvider('http://172.16.10.47:8545',
#                                request_kwargs={'timeout': 2}))
# contract_v4 = w3_v4.eth.contract(
#     address="0x01A1F73b1f4726EB6EB189FFA5CBB91AF8E14025", abi=V4)
# address = w3_v4.toChecksumAddress("0xc74ce67bfc623c803d48afc74a09a6ff6b599003")
# print(address)
# print(contract_v4.functions.owedPayment(address).call())
# TODO: Check for v3 or v4 and parse accordingly
# TODO: If neither v4 nor v3 do nothing
# TODO: Do not start evm contracts monitor if no evm url or no cl url
# TODO: pass parent_id, chain_name, node_name and some meta_data if any with
#     : current data
