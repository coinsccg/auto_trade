import os.path
from loguru import logger

from trade.eth import ContractCall

abs_path = os.path.abspath(".")

config_path = os.path.join(abs_path, "config/config.toml")

router_abi_path = os.path.join(abs_path, "abi/pancake_router.abi")
pair_abi_path = os.path.join(abs_path, "abi/erc20_pair.abi")
usdt_abi_path = os.path.join(abs_path, "abi/usdt.abi")

wallets_old_path = os.path.join(abs_path, "wallets/wallets_old.csv")
wallets_new_path = os.path.join(abs_path, "wallets/wallets_new.csv")

log_path = os.path.join(abs_path, "logs/transfer.log")


def main():
    logger.add(log_path, format="{time} {level} {message}", level="DEBUG")
    instance = ContractCall(config_path, router_abi_path, pair_abi_path, usdt_abi_path)

    # 将旧钱包中的代币转入新钱包
    instance.transfer_to_new(wallets_old_path, wallets_new_path)


if __name__ == '__main__':
    main()
