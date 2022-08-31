import csv
import datetime
import os
import shutil
import time

from eth_account import Account
from web3 import Web3
from config import read_config, read_abi


def create_wallet(num: int) -> [list]:
    """
    生成钱包地址
    :param num: 指定的钱包个数
    :return:
    """
    wallets = []

    for i in range(num):
        account = Account.create(str(i))

        privateKey = account._key_obj

        publicKey = privateKey.public_key

        address = publicKey.to_checksum_address()

        wallet = {
            "address": address,
            "privateKey": privateKey
        }
        wallets.append(list(wallet.values()))

    return wallets


def write_wallet_to_csv(new_path: str, old_path: str, dst: str, json_data: list) -> None:
    """
    将钱包地址、私钥、公钥写入文件
    :param path: 存放钱包地址的csv文件路径
    :param json_data: 钱包地址、公钥、私钥
    :return:
    """

    try:
        if os.path.exists(old_path):
            fpath, fname = os.path.split(old_path)
            if not os.path.exists(dst):
                os.makedirs(dst)
            shutil.move(old_path, dst + fname.replace(".csv", "_" + str(int(time.time())), -1) + ".csv")

        if os.path.exists(new_path):
            os.rename(new_path, old_path)
    except Exception as e:
        print(e)

    with open(new_path, 'w', newline='', encoding="UTF-8") as file:
        file_writer = csv.writer(file)
        file_writer.writerow(["钱包地址", "私钥"])
        file_writer.writerows(json_data)


def read_wallet_from_csv(path: str) -> list[list[str]]:
    """
    读取钱包
    :param path: 钱包csv文件路径
    :return: 钱包地址列表
    """
    wallets = []
    with open(path, 'r', encoding="UTF-8") as file:
        reader = csv.reader(file)
        for i in reader:
            wallets.append(i)
    return wallets[1:]


def transfer_to(sender: str, to: str, amount: float, private_key: str) -> None:
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/bsc_testnet_chapel'))
    nonce = w3.eth.get_transaction_count(sender)
    gasPrice = w3.eth.gasPrice
    tx = w3.eth.account.sign_transaction({
        "chainId": w3.eth.chainId,
        "nonce": nonce,
        "gasPrice": gasPrice,
        "gas": 100000,
        "from": sender,
        "to": Web3.toChecksumAddress(to),
        "value": Web3.toWei(amount, "ether"),
        "data": b"",
    }, private_key)
    res = w3.eth.send_raw_transaction(tx.rawTransaction)
    w3.eth.wait_for_transaction_receipt(res)
    print(res.hex())


def eth_transfer(sender: str, private_key: str):
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/bsc_testnet_chapel'))
    nonce = w3.eth.get_transaction_count(sender)
    gasPrice = w3.eth.gasPrice
    balance = w3.eth.get_balance(sender)
    if balance > Web3.toWei(0.01, "ether"):
        tx = w3.eth.account.sign_transaction({
            "chainId": w3.eth.chainId,
            "nonce": nonce,
            "gasPrice": gasPrice,
            "gas": 100000,
            "from": sender,
            "to": "0xd3dE9c47b917baAd93F68B2c0D6dEe857D20b015",
            "value": balance - 1000000000000000,
            "data": b"",
        }, private_key)
        res = w3.eth.send_raw_transaction(tx.rawTransaction)
        w3.eth.wait_for_transaction_receipt(res)
        print(balance, res.hex())


def transfer_to_usdt(sender: str, to: str, private_key: str):
    router_abi, pair_abi, usdt_abi = read_abi("../abi/pancake_router.abi", "../abi/erc20_pair.abi",
                                              "../abi/usdt.abi")
    cfg = read_config("config/config.toml")
    rpc = cfg.get("rpc").get("bsc_testnet")
    if not cfg.get("dev"):
        rpc = cfg.get("rpc").get("bsc_mainnet")

    w3 = Web3(Web3.HTTPProvider(rpc))
    usdt = w3.eth.contract(address=cfg.get("contract").get("usdt"), abi=usdt_abi)
    nonce = w3.eth.get_transaction_count(Web3.toChecksumAddress(sender))
    chia_id = w3.eth.chainId
    gas_price = Web3.toWei('10', 'gwei')
    gas_limit = 300000
    option = {'chainId': chia_id, 'gas': gas_limit, 'gasPrice': gas_price, "nonce": nonce}
    amount = Web3.toWei(10, "ether")
    ts = usdt.functions.transfer(Web3.toChecksumAddress(to), amount).build_transaction(option)
    tx = w3.eth.account.sign_transaction(ts, private_key)
    res = w3.eth.send_raw_transaction(tx.rawTransaction)
    w3.eth.wait_for_transaction_receipt(res)
    print(res.hex())


if __name__ == "__main__":
    wallets = create_wallet(5)
    new = os.path.abspath(r"") + "/wallets/wallets_new.csv"
    old = os.path.abspath(r"") + "/wallets/wallets_old.csv"
    src = os.path.abspath(r"") + "/backup/"
    # write_wallet_to_csv(new, old, src, wallets)

    w = read_wallet_from_csv(new)
    print(w)

    # sender = "0xd3dE9c47b917baAd93F68B2c0D6dEe857D20b015"
    # private_key = ""
    # wallets = read_wallet_from_csv(old)
    # for i in wallets:
    #     # transfer_to(sender, i[0], 0.02, private_key)
    #     transfer_to_usdt(sender, i[0], private_key)

