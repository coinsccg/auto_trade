import csv
from eth_account import Account
from web3 import Web3


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
            "id": str(i),
            "address": address,
            "privateKey": privateKey,
            "publicKey": publicKey
        }
        wallets.append(list(wallet.values()))

    return wallets


def write_wallet_to_csv(path: str, json_data: list) -> None:
    """
    将钱包地址、私钥、公钥写入文件
    :param path: 存放钱包地址的csv文件路径
    :param json_data: 钱包地址、公钥、私钥
    :return:
    """
    with open(path, 'a', newline='', encoding="UTF-8") as file:
        file_writer = csv.writer(file)
        file_writer.writerow(["序号", "钱包地址", "私钥", "公钥"])
        file_writer.writerows(json_data)


def read_wallet_from_csv(path: str) -> [dict]:
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


def eth_transfer(sender: str, private_key: str):
    w3 = Web3(Web3.HTTPProvider('https://ropsten.infura.io/v3/457c1ac43c544b05abfef0163084a7a6'))
    nonce = w3.eth.get_transaction_count(sender)
    gasPrice = w3.eth.gasPrice
    balance = w3.eth.get_balance(sender)
    if balance > Web3.toWei(1, "ether"):
        tx = w3.eth.account.sign_transaction({
            "nonce": nonce,
            "gasPrice": gasPrice,
            "gas": 100000,
            "from": sender,
            "to": "0xd3dE9c47b917baAd93F68B2c0D6dEe857D20b015",
            "value": balance - 30000000000000000,
            "data": b"",
        }, private_key)
        res = w3.eth.send_raw_transaction(tx.rawTransaction)
        print(balance, res.hex())


if __name__ == "__main__":
    wallets = create_wallet(10)
    write_wallet_to_csv("../wallets/wallets.csv", wallets)
