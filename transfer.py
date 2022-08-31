import os

from web3 import Web3
from typing import Union, Type
from web3.contract import Contract
from wallet_collect import read_wallet_from_csv
from config import read_config
from loguru import logger
from config import read_abi


class Transfer:
    w3: Web3
    usdt: Union[Type[Contract], Contract]
    cfg: dict
    abi: list

    def __init__(self, usdt_abi_path: str):
        self.abi = read_abi(usdt_abi_path)
        rpc = self.cfg.get("rpc").get("bsc_testnet")
        if not self.cfg.get("dev"):
            rpc = self.cfg.get("rpc").get("bsc_mainnet")
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.usdt = self.w3.eth.contract(address=self.cfg.get("contract").get("router"), abi=self.abi[0])

    def total_wallet_transfer_eth(self, new_path: str, sender: str, amount: int, private_key: str):
        """
        总钱包向子钱包转入原生代币
        :param new_path: 子钱包路径
        :param sender: 总钱包地址
        :param amount: 金额
        :param private_key: 总钱包私钥
        :return:
        """
        wallets = read_wallet_from_csv(new_path)
        for w in wallets:
            tx = self.w3.eth.account.sign_transaction({
                "chainId": self.w3.eth.chainId,
                "nonce": self.w3.eth.get_transaction_count(Web3.toChecksumAddress(sender)),
                "gasPrice": self.w3.eth.gasPrice,
                "gas": 100000,
                "from": sender,
                "to": Web3.toChecksumAddress(w[0]),
                "value": Web3.toWei(amount, "ether"),
                "data": b"",
            }, private_key)
            res = self.w3.eth.send_raw_transaction(tx.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(res)

    def total_wallet_transfer_usdt(self, new_path: str, sender: str, amount: int, private_key: str):
        wallets = read_wallet_from_csv(new_path)
        for w in wallets:
            option = {
                'chainId': self.w3.eth.chainId,
                'gas': 100000,
                'gasPrice': Web3.toWei('10', 'gwei'),
                "nonce": self.w3.eth.get_transaction_count(Web3.toChecksumAddress(sender))
            }
            amount = Web3.toWei(amount, "ether")
            ts = self.usdt.functions.transfer(w[0], amount).build_transaction(option)
            tx = self.w3.eth.account.sign_transaction(ts, private_key)
            res = self.w3.eth.send_raw_transaction(tx.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(res)
            print(res.hex())


if __name__ == '__main__':
    abs_path = os.path.abspath(".")
    config_path = os.path.join(abs_path, "config/config.toml")
    log_path = os.path.join(abs_path, "logs/transfer.log")
    usdt_abi_path = os.path.join(abs_path, "abi/usdt.abi")
    wallets_new_path = os.path.join(abs_path, "wallets/wallets_new.csv")

    logger.add(log_path, format="{time} {level} {message}", level="DEBUG")
    cfg = read_config(config_path)

    transfer = Transfer(usdt_abi_path)

    # 转eth
    transfer.total_wallet_transfer_eth(
        wallets_new_path,
        cfg.get("account").get("sender"),
        cfg.get("amount").get("eth"),
        cfg.get("account").get("pk"))

    # 转usdt
    transfer.total_wallet_transfer_eth(
        wallets_new_path,
        cfg.get("account").get("sender"),
        cfg.get("amount").get("erc20"),
        cfg.get("account").get("pk"))
