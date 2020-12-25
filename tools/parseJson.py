import pandas as pd
from bs4 import BeautifulSoup
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

sen_url = "https://trails-game.com/characters_sen/"
zero_ao_url = "https://trails-game.com/characters_sen/characters_za/"

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


def append_new_node(name):
    global id
    names.append(name)
    new_node = {"name" : name, "id": str(id)}
    new_node["group"] = 2
    name_id_map[name] = str(id)
    id = id+1
    nodes.append(new_node)


build_name_to_link_map(sen_url)
build_name_to_link_map(zero_ao_url)

sheet = pd.read_excel(file, None)

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
            new_node["wikiPage"] = ""
        new_node["isOrganization"] = v["isOrganization"]
        nodes.append(new_node)

values2 = sheet["人物组织关系"].to_dict(orient="records")
for v in values2:
    if (str(v["source"]) == "nan" or str(v["target"]) == "nan" or str(v["Relation"]) == "nan" or str(v["RelationType"]) == "nan"):
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

        new_link = {"source":source_id, "target":target_id, "relation":v["Relation"], "type":v["RelationType"]}
        links.append(new_link)

if (len(missing_names) > 0):
    raise ValueError("missing names: ", missing_names)

output = {"nodes":nodes, "links":links}
output = json.dumps(output, sort_keys=True, indent=4, ensure_ascii=False)

print(output)

target_file = os.path.join("dist", "data.json")

with open(target_file, "w") as f:
    f.write(output)
    f.flush()
