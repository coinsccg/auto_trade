import datetime
import time
from typing import Union, Type
from web3 import Web3
from web3.contract import Contract
from config import read_config, read_abi


class ContractCall:
    """
    合约调用
    """
    w3: Web3
    router: Union[Type[Contract], Contract]
    pair: Union[Type[Contract], Contract]

    def __init__(self, config_path: str, router_abi_path: str, pair_abi_path: str):
        router_abi, pair_abi = read_abi(router_abi_path, pair_abi_path)
        cfg = read_config(config_path)
        rpc = cfg.get("rpc").get("bsc_testnet")
        if not cfg.get("dev"):
            rpc = cfg.get("rpc").get("bsc_mainnet")

        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.router = self.w3.eth.contract(address=cfg.get("contract").get("router"), abi=router_abi)
        self.pair = self.w3.eth.contract(address=cfg.get("contract").get("pair"), abi=pair_abi)

    def get_pair_reserve(self) -> [int, int]:
        res = self.pair.functions.getReserves().call()
        return res[0], res[1]

    def get_token0(self) -> str:
        token0 = self.pair.functions.token0().call()
        return token0

    def swap_token_for_token_on_free(self, private_key: str):
        amount_in = Web3.toWei(100, 'ether')
        amount_min_out = Web3.toWei(9000, 'ether')
        amount_in_address = Web3.toChecksumAddress("0x844c10DCA138DCfA1cb78F3f2ebCC7461995099c")
        amount_out_address = Web3.toChecksumAddress("0xfC9Be152343fe598a3a935833Cde4ea51CceDcE7")
        target_address = Web3.toChecksumAddress("0xd3dE9c47b917baAd93F68B2c0D6dEe857D20b015")
        now = datetime.datetime.now() + datetime.timedelta(seconds=10)
        time_list = time.strptime(now.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        deadline = int(time.mktime(time_list))
        nonce = self.w3.eth.get_transaction_count(target_address)
        option = {'chainId': 97, 'gas': 1400000, 'gasPrice': Web3.toWei('40', 'gwei'), "nonce": nonce}
        transaction = self.router.functions. \
            swapExactTokensForTokensSupportingFeeOnTransferTokens(amount_in, amount_min_out,
                                                                  [amount_in_address, amount_out_address],
                                                                  target_address, deadline). \
            build_transaction(option)
        print(transaction)
        tx = self.w3.eth.account.sign_transaction(transaction, private_key)
        res = self.w3.eth.send_raw_transaction(tx.rawTransaction)
        print(res.hex())


if __name__ == '__main__':
    instance = ContractCall("../config/config.toml", "../abi/pancake_router.abi", "../abi/erc20_pair.abi")
    # token0 = instance.get_token0()
    # reserve = instance.get_pair_reserve()
    # print(token0)
    # for i in reserve:
    #     print(type(i))

    private_key = ""
    instance.swap_token_for_token_on_free(private_key)
