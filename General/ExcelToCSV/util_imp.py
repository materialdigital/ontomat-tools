import base64
import os
import json
import logging
#import utility_functions as util
import requests
import yaml

import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON, POST

# Constants
CONST_VAL_ALL = "<all values>"
CONST_VAL_MINUS = '\\'
CONST_VAL_EMPTY = "<empty>"
CONST_VAL_SEPERATOR = ';'
CONST_QUERY_TYPE = '$TYPE$'
CONST_QUERY_SCOPE = '$SCOPE$'
CONST_QUERY_CLASS = '$CLASS$'
CONST_QUERY_PRODUCT = '$PRODUCT$'
CONST_NAN = "nan"

CONST_OM_URI = "https://www.materialdigital.de/ontomat/"
CONST_OM_PREFIX = "ontomat:"

CONST_INSTANCE_URI = "https://www.materialdigital.de/ontomat/instance/"
CONST_INSTANCE_PREFIX = "ontoins:"

CONST_QUDT_URI = "https://qudt.org/vocab/unit/"
CONST_QUDT_PREFIX = "unit:"

BOOLEAN_DATATYPE = 'http://www.w3.org/2001/XMLSchema#boolean'

CONST_MODE_GPT = "GPT"
CONST_MODE_SIMPLE = "SIMPLE"
CONST_MODE_SPACY = "SPACY"

def switchKeyValue(dictToSwitch):
    returnDict = {}

    # Take into considerations that val is (desc, label), label has priority
    for key, val in dictToSwitch.items():
        returnDict[val] = key

    return returnDict


def switchKeyTuple(dictToSwitch):
    returnDict = {}

    # Take into considerations that val is (label, featValues), label has priority
    for key, val in dictToSwitch.items():
        label = val[0]
        returnDict[label] = key

    return returnDict


def cleanLabel(inLabel, lower=False):  # self,
    labelStr = str(inLabel)
    if lower:
        labelStr = labelStr.lower()

    return labelStr.replace('°', '').replace(' ', '')


def createLabel(featValLabel, featValDesc, clean):
    fLabel = ""
    if len(featValLabel) > 0:
        fLabel = featValLabel
    else:
        fLabel = featValDesc

    if clean:
        fLabel = cleanLabel(fLabel.lower())

    return fLabel


def replace_comma_with_decimal_dot_separator(df: pd.DataFrame):
    """Replace the ',' (comma) decimal separator with '.' (dot) decimal separator in the entire DataFrame."""
    # (?<=\d),(?=\d) - regex to match the comma between two digits; it will then replace the comma with a '.' dot
    df.replace(r"(?<=\d),(?=\d)", '.', regex=True, inplace=True)


def get_classes_path(kg_endpoint, kg_user, kg_pw, start_iri):

    # Get all features and values from KG
    sparql = SPARQLWrapper(kg_endpoint)  # , agent=agent_str
    sparql.setReturnFormat(JSON)
    sparql.setCredentials(user=kg_user, passwd=kg_pw)

    queryText = open("sparql/select-superclasses-path.sparql").read()
    queryText = queryText.replace("$START$", start_iri)
    sparql.setQuery(queryText)
    ret1 = sparql.query().convert()

    rows1 = ret1["results"]["bindings"]
    logging.info("Contexts: {}".format(len(rows1)))

    class_path = ""

    # Create tupels with (label, ctvtFeatures) for each feature
    for row in rows1:

        path_element = ""
        if ("superclass" in row) and (row["superclass"]["type"] == "uri"):
            path_element = row["superclass"]["value"]

        if CONST_OM_URI in path_element:
            path_element = path_element.replace(CONST_OM_URI, CONST_OM_PREFIX)

        # Ignore, since IntensiveMaterialProperty should be the route
        if path_element == "ontomat:ProductProperty":
            continue

        if len(class_path) > 0:
            class_path = class_path + "|" + path_element
        else:
            class_path = path_element

    return class_path

def get_leaf_classes(kg_endpoint, kg_user, kg_pw):

    # Get all features and values from KG
    sparql = SPARQLWrapper(kg_endpoint)  # , agent=agent_str
    sparql.setReturnFormat(JSON)
    sparql.setCredentials(user=kg_user, passwd=kg_pw)

    queryText = open("sparql/select-leaf-classes.sparql").read()
    sparql.setQuery(queryText)
    ret1 = sparql.query().convert()

    rows1 = ret1["results"]["bindings"]
    logging.info("Contexts: {}".format(len(rows1)))

    leaf_classes = {}

    # Create tupels with (label, ctvtFeatures) for each feature
    for row in rows1:

        leaf_class = ""
        if ("class" in row) and (row["class"]["type"] == "uri"):
            leaf_class = row["class"]["value"]

        label = ""
        if ("label" in row) and (row["label"]["type"] == "literal"):
            label = row["label"]["value"]

        if CONST_OM_URI in leaf_class:
            leaf_class = leaf_class.replace(CONST_OM_URI, CONST_OM_PREFIX)

        if not leaf_class in leaf_classes:
            leaf_classes[leaf_class] = label
        #leaf_classes.append(leaf_class)

    return leaf_classes

def load_mat_classes(kg_endpoint, kg_user, kg_pw, store_by_label):

    sparql = SPARQLWrapper(kg_endpoint)  # , agent=agent_str
    sparql.setReturnFormat(JSON)
    sparql.setCredentials(user=kg_user, passwd=kg_pw)

    queryText = open("sparql/select-material-classes.sparql").read()
    sparql.setQuery(queryText)
    ret1 = sparql.query().convert()

    rows1 = ret1["results"]["bindings"]
    logging.info("Contexts: {}".format(len(rows1)))

    results = {}

    # Create tupels with (label, id) for each feature
    for row in rows1:

        uri = ""
        label = ""
        identifier = ""
        if ("subject" in row) and (row["subject"]["type"] == "uri"):
            uri = row["subject"]["value"]

        if ("label" in row) and (row["label"]["type"] == "literal"):
            label = row["label"]["value"]

        if ("ident" in row) and (row["ident"]["type"] == "literal"):
            identifier = row["ident"]["value"]

        if store_by_label:
            if len(label) == 0:
                continue

            if not label.lower() in results: # use lower to make it case-insentive
                results[label.lower()] = uri

        else:
            if len(identifier) == 0:
                continue

            if not identifier in results:
                results[identifier] = uri

    return results

def load_mat_properties(kg_endpoint, kg_user, kg_pw):

    sparql = SPARQLWrapper(kg_endpoint)  # , agent=agent_str
    sparql.setReturnFormat(JSON)
    sparql.setCredentials(user=kg_user, passwd=kg_pw)

    queryText = open("sparql/select-material-props.sparql").read()
    sparql.setQuery(queryText)
    ret1 = sparql.query().convert()

    rows1 = ret1["results"]["bindings"]
    logging.info("Contexts: {}".format(len(rows1)))

    results = {}

    # Create tupels with (label, id) for each feature
    for row in rows1:

        uri = ""
        label = ""
        unit = ""
        if ("subject" in row) and (row["subject"]["type"] == "uri"):
            uri = row["subject"]["value"]

        if ("label" in row) and (row["label"]["type"] == "literal"):
            label = row["label"]["value"]

        if ("unit" in row) and (row["unit"]["type"] == "literal"):
            unit = row["unit"]["value"]

        if len(label) == 0:
            continue

        if not label.lower() in results: # use lower to make it case-insentive
            results[label.lower()] = (uri, unit)


    return results

def read_yaml_config_file(file_path: str):
    config_path = os.path.abspath(file_path)
    with open(config_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as exception:
            logging.error(exception)

