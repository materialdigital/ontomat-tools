import getopt, sys, os
import optparse
import re
import json
from re import sub
import pandas as pd


def prepare_properties(file, output, prefix):

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError("Unerwartete JSON-Struktur: Liste mit mindestens 2 Elementen erwartet.")

 
    metaData = data[0]
    processName = metaData.get("name")
    processTargetNamespace = metaData.get("targetNamespace")

 
    block = data[1]

    process = block.get("process", {})
    processType = process.get("$type")
    processId = process.get("id")

    processObjects = block.get("elementDataInformation", [])

    allowedTypes = {"fpb:ProcessOperator", "fpb:Product"}
    filtered = [obj for obj in processObjects if obj.get("$type") in allowedTypes]

    print("Process:", processName, processId, processType)
    for obj in filtered:
        print("   ", obj.get("$type"), obj.get("id"))

    if filtered:
        df = pd.json_normalize(filtered)
        df.to_csv(output, index=False, encoding="utf-8")


"""

"""


def main(argv):

    parser = optparse.OptionParser()
    parser.add_option('--input', action="store", dest="input", default="./example/FE_Process_general.json")
    parser.add_option('--output', action="store", dest="output", default="./example/FE_Process_general_tranformed.csv")
    parser.add_option('--prefix', action="store", dest="prefix", default="ontomat:") # ontomat:

    (options, args) = parser.parse_args()

    prepare_properties(options.input, options.output, options.prefix)

if __name__ == "__main__":
    import sys

    main(sys.argv[1:])