import toml
import json


def read_abi(router_path: str, pair_path: str) -> (list, list):
    try:
        with open(router_path, "r") as f:
            router = f.read()

        with open(pair_path, "r") as f:
            pair = f.read()

        return json.loads(router), json.loads(pair)
    except Exception as e:
        raise e


def read_config(path: str) -> dict:
    try:
        content = toml.load(path)
        return content
    except Exception as e:
        raise e


if __name__ == '__main__':
    # read_config("./config/config.toml")
    result = read_abi("./abi/pancake_router.abi", "./abi/erc20_pair.abi")
    for i in result:
        print(i)
