import getopt, sys, os
import optparse
import re
from re import sub
import pandas as pd

CONST_QUDT_UNIT = "http://qudt.org/vocab/unit/"

def prepare_properties(file, output, range, prefix):

    # Parse range
    rangeFrom = rangeTo = 0

    if ':' in range:
        temp_r = range.split(':')
        rangeFrom = int(temp_r[0])
        rangeTo = int(temp_r[1])

    #file1 = open(file, 'r')
    #input_lines = file1.readlines()
    sheet = "TotalSetOfNominalProperties"

    xls_file = pd.ExcelFile(file)
    df1 = pd.read_excel(xls_file, sheet, header=None, na_filter=True)

    fOut = open(output, "w")

    result_all = ""

    l_count = 0

    #for line in input_lines:
    for index in df1.index:

        line = df1.loc[index]

        #l_count = l_count + 1

        # First line is header
        # property super class,property class,property sub class,unit,QUDT unit,symbol,refers to,comments,actual class (generic material property),author
        if index == 0: # 1
            result = "SuperClassIRI;ClassNameIRI;label;textUnit;qudtUnit;symbol\n"
            result_all = result_all + result
            continue

        print(line)

        class_name_1 = str(line[1]).strip()
        class_name_2 = str(line[2]).strip()
        super_class = str(line[0]).strip()
        unit_text = str(line[3]).strip()
        qudt_unit = str(line[4]).strip()
        symbol = str(line[5]).strip()

        if symbol.lower() == "nan":
            symbol = ""
        if unit_text.lower() == "nan":
            unit_text = ""
        if super_class.lower() == "nan":
            super_class = ""

        # Ignore materials with no superClass
        if len(super_class) == 0:
            continue

        if len(class_name_2) == 0 or class_name_2.lower() == "nan":
            class_name = class_name_1
        else:
            class_name = class_name_2

        label = class_name.capitalize()

        # Join and uppercase
        class_name = class_name.replace('\'','').replace('-',' ').replace('/',' ') .replace('(','').replace(')','')
        temp_list = class_name.split(' ')
        classNameIRI = prefix + ''.join([x[0].upper() + x[1:] for x in temp_list])

        # Add prefix to superClass
        temp_list = super_class.split(' ')
        superClassIRI = prefix + ''.join([x[0].upper() + x[1:]  for x in temp_list])
        
        # Complete qudt unit IRI
        qudt_unit = qudt_unit.replace("unit:",CONST_QUDT_UNIT)

         # Remove text with brackets
        #classNameShort = re.sub("[\(].*?[\)]", "", className)
        #classNameShort = re.sub(r"[\_\/\-]", " ", classNameShort).strip()

        result = superClassIRI + ";" + classNameIRI + ";" + label + ";" + unit_text + ";" + qudt_unit + ";" +  symbol + "\n"
        result_all = result_all + result # + os.linesep

        print(result)


    fOut.write(result_all)

    fOut.close()


def main(argv):

    parser = optparse.OptionParser()
    parser.add_option('--input', action="store", dest="input", default="./data/NominalMaterialProperties_2025_05_05.xlsx")
    parser.add_option('--output', action="store", dest="output", default="./data/NominalMaterialProperties_cleaned_om.csv")
    parser.add_option('--range', action="store", dest="range", default="0:0") # 74:100
    parser.add_option('--prefix', action="store", dest="prefix", default="ontomat:") # ontomat:

    (options, args) = parser.parse_args()

    prepare_properties(options.input, options.output, options.range, options.prefix)

if __name__ == "__main__":
    import sys

    main(sys.argv[1:])