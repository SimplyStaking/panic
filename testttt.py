from web3 import Web3

from src.utils.constants.abis import V3

w3 = Web3(Web3.HTTPProvider('http://172.16.152.65:8545',
                            request_kwargs={'timeout': 2}))
contract = w3.eth.contract(address="0x05883D24a5712c04f1b843C4839dC93073A56Ef4",
                           abi=V3)
print(contract.functions.withdrawablePayment("0x2607e6f021922a5483d64935f87e15ea797fe8d4").call())
