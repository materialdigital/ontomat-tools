import json
import getopt, sys
import optparse
from util_imp import CONST_OM_PREFIX
from RunLutra import run_lutra_simple
from merge_rdf_files import merge_plain
from prepare_property_classes import prepare_properties

def main(argv):

    parser = optparse.OptionParser()
    parser.add_option('--input', action="store", dest="input", default="./data/NominalMaterialProperties_2025_05_05.xlsx")
    parser.add_option('--output', action="store", dest="output", default="./output/mat-properties-generated.ttl")
    parser.add_option('--library', action="store", dest="library", default="./templates/stottr/") 
    parser.add_option('--ontology', action="store", dest="ontology", default="../Ontology/ontomat-base-0.5.ttl")
    (options, args) = parser.parse_args()

    output_0 = "./data/NominalMaterialProperties_cleaned_om.csv"

    prepare_properties(options.input, output_0, "0:0", CONST_OM_PREFIX)

    # Call preparation script
    input_1 = "./templates/bottr/material-property.bottr"
    output_1 = options.output
    run_lutra_simple(input_1, output_1, options.library)

if __name__ == "__main__":
    import sys

    main(sys.argv[1:])