# python
import json
import csv
import re
import os

def getJson(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 构建节点
def build_node_ids(json_data):
    node_names = set()
    for d in json_data:
        node_names.add(d['subject'])
        node_names.add(d['object'])
    node_ids = {}
    for idx, name in enumerate(sorted(node_names), start=1):
        node_ids[name] = idx
    return node_ids

def write_nodes_csv(node_ids, output_path):
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([':ID', 'name'])
        for name, node_id in node_ids.items():
            writer.writerow([node_id, name])
            
def write_rels_csv(json_data, node_ids, output_path):
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([':START_ID', ':END_ID', ':TYPE', 'chunk'])
        for d in json_data:
            start_id = node_ids[d['subject']]
            end_id = node_ids[d['object']]
            rel_type = d.get('predicate', 'RELATED_TO').replace(' ', '_').upper()

            if 'chunk' in d:
                chunk = d['chunk']
            else:
                chunk = ''
            writer.writerow([start_id, end_id, rel_type, chunk])

if __name__ == "__main__":
    json_data = getJson("./mydocument6.json")
    node_ids = build_node_ids(json_data)
    write_nodes_csv(node_ids, "./nodes6.csv")
    write_rels_csv(json_data, node_ids, "./relationships6.csv")