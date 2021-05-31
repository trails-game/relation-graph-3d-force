import pandas as pd
import requests
import threading
import json
import os

def request_header(v, failed_links):
    result = requests.head(str(v["avatar"]))
    if result.status_code != 200:
        failed_links[v["name"]] = str(v["avatar"])

def test_header(sheet, failed_links):
    values = sheet["角色"].to_dict(orient="records")
    thread_list = []
    for v in values:
        if str(v["avatar"]) == "nan":
            # failed_links[v["name"]] = str(v["avatar"])
            continue
        t = threading.Thread(target=request_header, args=(v, failed_links))
        thread_list.append(t)
        t.start()

    for t in thread_list:
        t.join()

if __name__ == "__main__":
    failed_links = {}
    file = os.path.join(os.getcwd(), "tools", "relation.xlsx")
    sheet = pd.read_excel(file, None)

    test_header(sheet, failed_links)
    if (len(failed_links) > 0) :
        raise ValueError("failed links: {0}".format(failed_links))