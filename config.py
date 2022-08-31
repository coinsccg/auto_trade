import toml
import json


def read_abi(*args) -> list:
    abi_list = []
    try:
        for p in args:
            with open(p, "r") as f:
                content = f.read()
            abi_list.append(json.loads(content))
        return abi_list
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
