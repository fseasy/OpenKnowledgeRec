#!python3
# -*- coding: utf-8 -*-
"""build hierarchical categories
"""
import argparse
import json
import pathlib
import pickle

import tqdm

from category_network import CategoryNetwork


def main():
    parser = argparse.ArgumentParser(description="build category level")
    parser.add_argument("--data", "-d", help="path to extracted page json data", required=True)
    parser.add_argument("--output", "-o", help="path to network pickle", required=True)
    args = parser.parse_args()

    network = CategoryNetwork()
    with open(args.data, encoding="utf-8") as f:
        for line in tqdm.tqdm(f):
            # sample line (formated):
            # {
            #   "title": "Wikipedia:Upload log", 
            #   "categories": ["中文維基百科上載日誌存檔"], ...
            #  }
            d = json.loads(line)
            title = d["title"]
            categories = d["categories"]
            network.add_node_and_link(title, categories)

    network_str = network.serialize()
    # Test serialize works fine.
    # new_n = CategoryNetwork.deserialize(network_str)
    # assert new_n == network
    p = pathlib.Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open(mode="wt", encoding="utf-8") as f:
        print(network_str, file=f)


if __name__ == "__main__":
    main()