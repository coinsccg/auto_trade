import toml
import json


def read_abi(path: str) -> list:
    try:
        with open(path, "r") as f:
            content = f.read()

        return json.loads(content)
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
