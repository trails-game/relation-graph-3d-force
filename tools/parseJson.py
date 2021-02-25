import pandas as pd
import threading
import requests
import json
import os

SEARCH_URL = "https://trails-game.com/wp-json/wp/v2/search"
BASE_URL = "https://trails-game.com/?p="

TYPES = ["Char", "Org", "Fam"]

def search_for_link(name, new_node, type_):
    result = None
    if type_.split(".")[0] == "Char":
        result = requests.get(SEARCH_URL, 
        params={"type":"post", 
        "subtype": "dt_team", 
        "per_page":"1",
        "search": name})
    else:
        result = requests.get(SEARCH_URL, 
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

def parse_name_page(sheet, names, name_id_map, thread_list, malformed_types, nodes):
    #name sheet processing
    id = 0
    values = sheet["角色"].to_dict(orient="records")
    for v in values:
        if not v["name"] in names:
            names.add(v["name"])

            new_node = {"name" : v["name"], "id": str(id)}
            name_id_map[v["name"]] = str(id)

            id = id + 1
            if (str(v["avatar"]) != "nan"):
                new_node["avatar"] = str(v["avatar"])
            if (str(v["postid"]) != "nan"):
                new_node["wikiPage"] = BASE_URL + str(int(v["postid"]))
            else:
                t = threading.Thread(target=search_for_link, args=(v["name"], new_node, v["type"]))
                thread_list.append(t)
                t.start()

            new_node["type"]=v["type"] if v["type"] in TYPES else malformed_types.append(v)

            nodes.append(new_node)

def parse_relations(sheet, names, malformed_relations, missing_names, name_id_map, links):
    # not used
    # set的效率比list高很多。
    exising_src_dest_pairs = set()

    _values = sheet["人物组织关系"].to_dict(orient="records")

    for v in _values:
        # 验证
        if (str(v["source"]) == "nan" or str(v["target"]) == "nan" or str(v["Relation"]) == "nan" or str(v["RelationType"]) == "nan"):
            malformed_relations.append(v)
            continue
        if (not v["source"] in names and not v["source"] in missing_names):
            missing_names.append(v["source"])
            continue
        if (not v["target"] in names and not v["target"] in missing_names):
            missing_names.append(v["target"])
            continue
        # 验证结束
        # 这个if没有任何作用，因为前面有问题的都continue了
        # if (not v["source"] in missing_names and not v["target"] in missing_names):
        source_id = name_id_map[v["source"]]
        target_id = name_id_map[v["target"]]

        # 这里要用tuple，用dict的话，in就只会参考source_id而忽略target_id
        pair = (source_id, target_id)
        if not pair in exising_src_dest_pairs:
            exising_src_dest_pairs.add(pair)
            new_link = {"source":source_id, "target":target_id, "relation":v["Relation"], "type":v["RelationType"]}
            links.append(new_link)

def check_values(missing_names, malformed_types, malformed_relations):
    if (len(missing_names) > 0):
        raise ValueError("missing names: ", missing_names)
    if (len(malformed_types) > 0):
        raise ValueError("malformed types: ", malformed_types)
    if (len(malformed_relations) > 0):
        raise ValueError("malformed relations: ", malformed_relations)

def write_outputs(output):
    target_file = os.path.join("dist", "data.json")
    with open(target_file, "w") as f:
        output = json.dumps(output, sort_keys=True, indent=4, ensure_ascii=False)
        print(output)
        f.write(output)
        f.flush()

def run():
    file=os.path.join(os.getcwd(), "tools", "relation.xlsx")

    output = {"nodes":[], "links":[]}

    names = set()
    name_id_map = {}

    missing_names = []
    malformed_types = []
    malformed_relations = []

    thread_list = []

    sheet = pd.read_excel(file, None)
    parse_name_page(sheet, names, name_id_map, thread_list, malformed_types, output["nodes"])
    parse_relations(sheet, names, malformed_relations, missing_names, name_id_map, output["links"])

    # no use?
    for t in thread_list:
        t.join()

    check_values(missing_names, malformed_types, malformed_relations)
    write_outputs(output)


if __name__ == "__main__":
    run()
