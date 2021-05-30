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
    print(failed_links)

if __name__ == "__main__":
    failed_links = {}
    file = os.path.join(os.getcwd(), "relation.xlsx")
    sheet = pd.read_excel(file, None)

    test_header(sheet, failed_links)
    # run()