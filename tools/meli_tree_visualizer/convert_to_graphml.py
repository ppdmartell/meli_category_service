# The JSON file to be converted must be in the same folder of this script!!
# Usage: python convert_to_graphml.py input.json output.graphml
#
# 0- Manually modify the resulting graphml file. Change (in line 2) attr.type="long" to attr.type="int".
# 1- Download and install yEd Editor (https://www.yworks.com/products/yed/download)
# 2- Open the graphml file (you will see only 1 square)
# 3- Edit > Properties Mapper > Add new configuration (+) > New configuration for Nodes
# 4- Add new entry (+) >
# 5- Change Data Source value from total_items to label. Don't in checkbox "Fit Node to Label". Click Ok
# 6- Tools > Fit Label to Node
# 7- Layout > Tree > Directed:
#                    Layout Style: Directed
#                    Orientation: Top To Bottom
#                    Routing style for non-tree edges: Organic
#
# To run this script you need venv with networkx and lxml (pip install networkx lxml)


import json
import time
import logging
import networkx as nx
from pathlib import Path
import sys
sys.setrecursionlimit(50000)

LOG_FILE = Path(__file__).with_suffix(".log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

LOGGER = logging.getLogger(__name__)

def add_node_recursive(G, node):
    """
    Docstring for add_node_recursive:
    This method recursively adds nodes to the resulting graph. This utility converts from JSON to GraphML
    to create an image for visualization purposes.
    The purpose of this entire work is to find out if the tree is being built correctly.
    
    :param G: Graph
    :param node: Node to be added to the graph
    """
    node_id = node["id"]
    name = node.get("name", "")

    display_label = f"{name}\n{node_id}"

    G.add_node(
        node_id,
        label=display_label,
        total_items=int(node.get("total_items_in_this_category", 0))
    )

    for child_id, child_node in node.get("children", {}).items():
        child_name = child_node.get("name", "")
        child_label = f"{child_name}\n{child_id}"

        G.add_node(
            child_id,
            label=child_label,
            total_items=int(child_node.get("total_items_in_this_category", 0))
        )

        G.add_edge(node_id, child_id)

        add_node_recursive(G,child_node)


def convert(input_path, output_path):
    """
    Docstring for convert:
    The actual convertion from JSON to GraphML is done here by calling the add_node_recursive
    method.
    
    :param input_path: input argument which is the JSON file
    :param output_path: output argument which is the resulting GraphML file
    """
    start = time.perf_counter()

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            LOGGER.info(f"JSON file {input} was successfully loaded.")
    except Exception as exc:
        raise RuntimeError("JSON file load failed: {exc}")
    
    G = nx.DiGraph()
    for root_id, root_node in data.items():
        add_node_recursive(G, root_node)

    LOGGER.info(f"Nodes: {G.number_of_nodes()}")
    LOGGER.info(f"Edges: {G.number_of_edges()}")

    nx.write_graphml(G, output_path)
    end = time.perf_counter()
    LOGGER.info(f"GraphML saved to file: {output_path}")
    LOGGER.info(f"Total time: {(end - start):.4f} seconds.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_to_graphml.py input.json output.graphml")
        sys.exit(1)

    convert(Path(sys.argv[1]), Path(sys.argv[2]))
