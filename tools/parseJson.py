import pandas as pd
from bs4 import BeautifulSoup
import threading
import requests
import json
import os

BASE_URL = "https://trails-game.com/wp-json/wp/v2/search"
SEN_URL = "https://trails-game.com/characters_sen/"
ZERO_AO_URL = "https://trails-game.com/characters_sen/characters_za/"
TYPES = ["Char", "Org", "Fam"]

def build_name_to_link_map(url, name_to_link):
    res = requests.get(url)
    bs = BeautifulSoup(res.text,'html.parser')

    refs = bs.find_all("a")

    for r in refs:
        keys = r.attrs.keys()
        if "title" in keys and not "title" in name_to_link.keys():
            link = r.attrs['href']
            title = r.attrs['title']
            name_to_link[title] = link


def search_for_link(url, name, type, new_node):
    result = None
    if type == "Char":
        result = requests.get(url, 
        params={"type":"post", 
        "subtype": "dt_team", 
        "per_page":"1",
        "search": name})
    else:
        result = requests.get(url, 
        params={"type":"post", 
        "subtype": "map", 
        "per_page":"1",
        "search": name})
    
    if result is not None:
        responseJson = result.json()
        if len(responseJson) > 0:
            new_node["wikiPage"] = responseJson[0]["url"]
        else:
            new_node["wikiPage"] = ""
    else:
        new_node["wikiPage"] = ""

def parse_name_page(sheet, names, name_id_map, name_to_link, thread_list, malformed_types, nodes):
    #name sheet processing
    id = 0
    values = sheet["角色"].to_dict(orient="records")
    for v in values:
        if (not v["name"] in names):
            names.append(v["name"])

            new_node = {"name" : v["name"], "id": str(id)}
            name_id_map[v["name"]] = str(id)

            id = id + 1
            if (str(v["avatar"]) != "nan"):
                new_node["avatar"] = str(v["avatar"])
            
            if (str(v["wikiPage"]) != "nan"):
                new_node["wikiPage"] = str(v["wikiPage"])
            elif (v["name"] in name_to_link.keys()):
                new_node["wikiPage"] = name_to_link[v["name"]]
            else:
                t = threading.Thread(target=search_for_link, args=(BASE_URL, v["name"], v["type"], new_node))
                thread_list.append(t)
                t.start()

            if (v["type"] in TYPES):
                new_node["type"] = v["type"]    
            else:
                malformed_types.append(v)
            
            nodes.append(new_node)

def parse_relations(sheet, names, malformed_relations, missing_names, name_id_map, links):
    exising_src_dest_pairs = []

    values2 = sheet["人物组织关系"].to_dict(orient="records")
    for v in values2:
        if (str(v["source"]) == "nan" or str(v["target"]) == "nan" or str(v["Relation"]) == "nan" or str(v["RelationType"]) == "nan"):
            malformed_relations.append(v)
            continue

        if (not v["source"] in names and not v["source"] in missing_names):
            missing_names.append(v["source"])
            continue
        elif (not v["target"] in names and not v["target"] in missing_names):
            missing_names.append(v["target"])
            continue
        elif (not v["source"] in missing_names and not v["target"] in missing_names):
            source_id = name_id_map[v["source"]]
            target_id = name_id_map[v["target"]]

            pair = {source_id : target_id}
            if not pair in exising_src_dest_pairs:
                exising_src_dest_pairs.append(pair)
                new_link = {"source":source_id, "target":target_id, "relation":v["Relation"], "type":v["RelationType"]}
                links.append(new_link)

def check_values(missing_names, malformed_types, malformed_relations):
    if (len(missing_names) > 0):
        raise ValueError("missing names: ", missing_names)
    if (len(malformed_types) > 0):
        raise ValueError("malformed types: ", malformed_types)
    if (len(malformed_relations) > 0):
        raise ValueError("malformed relations: ", malformed_relations)

def write_outputs(nodes, links):
    output = {"nodes":nodes, "links":links}
    output = json.dumps(output, sort_keys=True, indent=4, ensure_ascii=False)
    print(output)
    target_file = os.path.join("dist", "data.json")
    with open(target_file, "w") as f:
        f.write(output)
        f.flush()

def main():
    file=os.path.join(os.getcwd(), "tools", "relation.xlsx")

    names = []
    nodes = []
    links = []
    
    name_id_map = {}
    name_to_link = {}

    missing_names = []
    malformed_types = []
    malformed_relations = []

    thread_list = []

    build_name_to_link_map(SEN_URL, name_to_link)
    build_name_to_link_map(ZERO_AO_URL, name_to_link)

    sheet = pd.read_excel(file, None)
    parse_name_page(sheet, names, name_id_map, name_to_link, thread_list, malformed_types, nodes)
    parse_relations(sheet, names, malformed_relations, missing_names, name_id_map, links)

    for t in thread_list:
        t.join()

    check_values(missing_names, malformed_types, malformed_relations)
    write_outputs(nodes, links)

if __name__ == "__main__":
    main()