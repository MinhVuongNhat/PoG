import requests

# Remote Freebase endpoint (via risub.com public API)
SPARQLPATH = "https://kg.risub.com/public/freebase.php"
SPARQL_API_KEY = "h29djdoqmcgtrushdjskahd8ldpjsaukxz"


sparql_head_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ns:%s ?relation ?x .\n}"""
sparql_tail_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation ns:%s .\n}"""
sparql_tail_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\nns:%s ns:%s ?tailEntity .\n}""" 
sparql_head_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\n?tailEntity ns:%s ns:%s  .\n}"""
sparql_id = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n  UNION\n  {\n    ?entity <http://www.w3.org/2002/07/owl#sameAs> ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""


sparql_tail_entities_and_relations = """
PREFIX ns: <http://rdf.freebase.com/ns/>
SELECT ?relation ?tailEntity
WHERE {
    ns:%s ?relation ?tailEntity .
}
"""

sparql_head_entities_and_relations = """
PREFIX ns: <http://rdf.freebase.com/ns/>
SELECT ?relation ?headEntity
WHERE {
    ?headEntity ?relation ns:%s .
}
"""


def check_end_word(s):
    words = [" ID", " code", " number", "instance of", "website", "URL", "inception", "image", " rate", " count"]
    return any(s.endswith(word) for word in words)

def abandon_rels(relation):
    if relation == "type.object.type" or relation == "type.object.name" or relation.startswith("common.") or relation.startswith("freebase.") or "sameAs" in relation:
        return True

def format(entity_id):
    return entity_id

def format1(entity_id):
    if "http://" in entity_id:
        return f"<{entity_id}>"
    else:
        return f"ns:{entity_id}"
    return entity_id

import time
import json as _json
from urllib.error import HTTPError


def _post_sparql(sparql_txt, retries=3, delay=2):
    """Send a SPARQL query via HTTP POST to the remote Freebase endpoint.
    Returns the list of binding dicts on success, or None on failure."""
    for attempt in range(retries):
        try:
            resp = requests.post(
                SPARQLPATH,
                data={"query": sparql_txt, "key": SPARQL_API_KEY},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["results"]["bindings"]
        except Exception as e:
            print(f"SPARQL error (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    print("Failed to execute after multiple attempts.")
    return None


def execurte_sparql(sparql_txt):
    return _post_sparql(sparql_txt)


def execute_sparql(sparql_txt):
    return _post_sparql(sparql_txt)


def replace_relation_prefix(relations):
    if relations is None:
        return []  
    return [relation['relation']['value'].replace("http://rdf.freebase.com/ns/","") for relation in relations]

def replace_entities_prefix(entities):
    if entities is None:
        return []  
    return [entity['tailEntity']['value'].replace("http://rdf.freebase.com/ns/","") for entity in entities]



from functools import lru_cache
import re

@lru_cache(maxsize=1024)
def id2entity_name_or_type(entity_id):
    query = sparql_id % (format(entity_id), format(entity_id))
    results = _post_sparql(query)

    if not results:
        return "Unnamed Entity"

    # Prefer English-tagged values
    english_results = [
        r["tailEntity"]["value"]
        for r in results
        if r["tailEntity"].get("xml:lang") == "en"
    ]
    if english_results:
        return english_results[0]

    # Fallback: alphanumeric values
    alphanumeric_results = [
        r["tailEntity"]["value"]
        for r in results
        if re.match(r"^[a-zA-Z0-9 ]+$", r["tailEntity"]["value"])
    ]
    if alphanumeric_results:
        return alphanumeric_results[0]

    return "Unnamed Entity"

