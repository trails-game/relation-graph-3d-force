import pandas as pd
from bs4 import BeautifulSoup
import threading
import requests
import json
import os

file=os.path.join(os.getcwd(), "tools", "relation.xlsx")

id = 0
names = []
nodes = []
links = []
name_id_map = {}
name_to_link = {}
missing_names = []
malformed_types = []
malformed_relations = []
exising_src_dest_pairs = []

thread_list = []

base_url = "https://trails-game.com/wp-json/wp/v2/search"
sen_url = "https://trails-game.com/characters_sen/"
zero_ao_url = "https://trails-game.com/characters_sen/characters_za/"
type_list = ["Char", "Org", "Fam"]

def build_name_to_link_map(url):
    global name_to_link
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

def parse_name_page(sheet):
    global id
    #name sheet processing
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
                t = threading.Thread(target=search_for_link, args=(base_url, v["name"], v["type"], new_node))
                thread_list.append(t)
                t.start()

            if (v["type"] in type_list):
                new_node["type"] = v["type"]    
            else:
                malformed_types.append(v)
            
            nodes.append(new_node)

def parse_relations(sheet):
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

def check_values():
    if (len(missing_names) > 0):
        raise ValueError("missing names: ", missing_names)
    if (len(malformed_types) > 0):
        raise ValueError("malformed types: ", malformed_types)
    if (len(malformed_relations) > 0):
        raise ValueError("malformed relations: ", malformed_relations)

def write_outputs():
    output = {"nodes":nodes, "links":links}
    output = json.dumps(output, sort_keys=True, indent=4, ensure_ascii=False)
    print(output)
    target_file = os.path.join("dist", "data.json")
    with open(target_file, "w") as f:
        f.write(output)
        f.flush()

def main():
    build_name_to_link_map(sen_url)
    build_name_to_link_map(zero_ao_url)

    sheet = pd.read_excel(file, None)
    parse_name_page(sheet)
    parse_relations(sheet)

    for t in thread_list:
        t.join()

    check_values()
    write_outputs()

if __name__ == "__main__":
    main()