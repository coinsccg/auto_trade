import datetime
import os
import time
from typing import Union, Type
from web3 import Web3
from web3.contract import Contract
from config import read_config, read_abi
from wallet_collect import read_wallet_from_csv, create_wallet, write_wallet_to_csv


class ContractCall:
    """
    合约调用
    """
    w3: Web3
    router: Union[Type[Contract], Contract]
    pair: Union[Type[Contract], Contract]
    usdt: Union[Type[Contract], Contract]
    cfg: dict

    def __init__(self, config_path: str, router_abi_path: str, pair_abi_path: str, usdt_abi_path: str):
        """
        :param config_path: 配置文件路径
        :param router_abi_path: pancake路由合约abi路径
        :param pair_abi_path: 交易对合约abi路径
        :param usdt_abi_path: usdt合约abi路径
        """
        abi = read_abi(router_abi_path, pair_abi_path, usdt_abi_path)
        self.cfg = read_config(config_path)
        rpc = self.cfg.get("rpc").get("bsc_testnet")
        if not self.cfg.get("dev"):
            rpc = self.cfg.get("rpc").get("bsc_mainnet")

        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.router = self.w3.eth.contract(address=self.cfg.get("contract").get("router"), abi=abi[0])
        self.pair = self.w3.eth.contract(address=self.cfg.get("contract").get("pair"), abi=abi[1])
        self.usdt = self.w3.eth.contract(address=self.cfg.get("contract").get("usdt"), abi=[2])

    def get_pair_reserve(self) -> [int, int]:
        res = self.pair.functions.getReserves().call()
        return res[0], res[1]

    def get_k_last(self) -> int:
        return self.pair.functions.kLast().call()

    def get_token0_price(self) -> int:
        reserve0, reserve1 = self.get_pair_reserve()
        if self.get_token0() == self.cfg.get("contract").get("erc20"):
            return reserve0 / reserve1
        else:
            return reserve1 / reserve0

    def get_token0(self) -> str:
        token0 = self.pair.functions.token0().call()
        return token0

    def get_amount_out(self, amount_in: int, in_address: str, out_address: str) -> int:
        """
        根据输入量查询交易最终输出量
        :param amount_in: 输入数量
        :param in_address: 输入合约地址
        :param out_address: 输出合约地址
        :return:
        """
        amount_in = Web3.toWei(amount_in, 'ether')
        amount_in_address = Web3.toChecksumAddress(in_address)
        amount_out_address = Web3.toChecksumAddress(out_address)
        result = self.router.functions.getAmountsOut(amount_in, [amount_in_address, amount_out_address]).call()
        print(result)
        return result[1]

    def eth_transfer(self, sender: str, to: str, private_key: str):
        """
        转账原生代币
        :param sender: 发送者地址
        :param to: 接收者地址
        :param private_key: 私钥
        :return:
        """
        nonce = self.w3.eth.get_transaction_count(sender)
        gasPrice = self.w3.eth.gasPrice
        balance = self.w3.eth.get_balance(sender)
        if balance > Web3.toWei(0.01, "ether"):
            tx = self.w3.eth.account.sign_transaction({
                "chainId": self.w3.eth.chainId,
                "nonce": nonce,
                "gasPrice": gasPrice,
                "gas": 100000,
                "from": sender,
                "to": Web3.toChecksumAddress(to),
                "value": balance - Web3.toWei(0.005, "ether"),
                "data": b"",
            }, private_key)
            res = self.w3.eth.send_raw_transaction(tx.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(res)
            print(res.hex())

    def usdt_transfer(self, sender: str, to: str, private_key: str):
        """
        转账ERC20代币
        :param sender: 发送者地址
        :param to: 接受者地址
        :param private_key: 私钥
        :return:
        """
        balance = self.usdt.functions.balanceOf(sender).call()
        if balance > 0:
            nonce = self.w3.eth.get_transaction_count(Web3.toChecksumAddress(sender))
            chia_id = self.w3.eth.chainId
            gas_price = Web3.toWei('10', 'gwei')
            gas_limit = 300000
            option = {'chainId': chia_id, 'gas': gas_limit, 'gasPrice': gas_price, "nonce": nonce}
            ts = self.usdt.functions.transfer(Web3.toChecksumAddress(to), balance).build_transaction(option)
            tx = self.w3.eth.account.sign_transaction(ts, private_key)
            res = self.w3.eth.send_raw_transaction(tx.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(res)
            print(res.hex())

    def transfer_to_new(self, wallets_old_path: str, wallets_new_path: str):
        """
        将旧钱包中的代币转入新钱包
        :param wallets_old_path: 旧钱包路径
        :param wallets_new_path: 新钱包路径
        :return:
        """
        if os.path.exists(wallets_new_path) and os.path.exists(wallets_old_path):
            wallets_old = read_wallet_from_csv(wallets_old_path)
            wallets_new = read_wallet_from_csv(wallets_new_path)

            for i in range(len(wallets_old)):
                self.eth_transfer(wallets_old[i][0], wallets_new[i][0], wallets_old[i][1])
                self.usdt_transfer(wallets_old[i][0], wallets_new[i][0], wallets_old[i][1])

    def swap_token_for_token_on_free(self,
                                     amount: int,
                                     token0: str,
                                     token1: str,
                                     to: str,
                                     private_key: str):
        """
        采用token兑换token的方式
        :param amount: 输入金额
        :param token0: 输入合约地址
        :param token1: 输出合约地址
        :param to: 接受者地址
        :param private_key: 私钥
        :return:
        """
        amount_in = Web3.toWei(amount, 'ether')
        amount_min_out = self.get_amount_out(amount, token0, token1)
        amount_in_address = Web3.toChecksumAddress(token0)
        amount_out_address = Web3.toChecksumAddress(token1)
        target_address = Web3.toChecksumAddress(to)
        now = datetime.datetime.now() + datetime.timedelta(seconds=10)
        time_list = time.strptime(now.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        deadline = int(time.mktime(time_list))
        nonce = self.w3.eth.get_transaction_count(target_address)
        chia_id = self.w3.eth.chainId
        gas_price = Web3.toWei('10', 'gwei')
        gas_limit = 300000
        option = {'chainId': chia_id, 'gas': gas_limit, 'gasPrice': gas_price, "nonce": nonce}
        ts = self.router.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(
            amount_in, amount_min_out, [amount_in_address, amount_out_address],
            target_address, deadline).build_transaction(option)
        tx = self.w3.eth.account.sign_transaction(ts, private_key)
        res = self.w3.eth.send_raw_transaction(tx.rawTransaction)

    def trade(self, new_path: str):
        """
        交易
        :param new_path: 新钱包路径
        :return:
        """
        wallets = read_wallet_from_csv(new_path)
        amount_in = 100
        amount_in_address = self.cfg.get("contract").get("usdt")
        amount_out_address = self.cfg.get("contract").get("erc20")

        # 买入
        for w in wallets:
            self.swap_token_for_token_on_free(
                amount_in,
                amount_in_address,
                amount_out_address,
                w[0],
                w[1])

        # 卖出
        for w in wallets:
            self.swap_token_for_token_on_free(
                amount_in,
                amount_out_address,
                amount_in_address,
                w[0],
                w[1])

    def run(self, num: int, old_path: str, new_path: str, backup_path: str):

        # 将旧钱包中的代币转入新钱包
        self.transfer_to_new(old_path, new_path)

        # 创建钱包
        wallets = create_wallet(num)

        # 将旧钱包备份并写入新钱包
        write_wallet_to_csv(new_path, old_path, backup_path, wallets)

        # 交易


if __name__ == '__main__':
    instance = ContractCall("../config/config.toml", "../abi/pancake_router.abi", "../abi/erc20_pair.abi",
                            "../abi/usdt.abi")

    # instance.transfer_to_new("../wallets/wallets.csv")
    instance.transfer_to_new("../wallets/wallets_old.csv", "../wallets/wallets_new.csv")
    # amount_in = 500
    # amount_in_address = "0x844c10DCA138DCfA1cb78F3f2ebCC7461995099c"
    # amount_out_address = "0xfC9Be152343fe598a3a935833Cde4ea51CceDcE7"
    # target_address = "0xd3dE9c47b917baAd93F68B2c0D6dEe857D20b015"
    # private_key = ""
    # instance.swap_token_for_token_on_free(amount_in, amount_in_address, amount_out_address, target_address, private_key)
