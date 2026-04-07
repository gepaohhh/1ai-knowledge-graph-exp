import json
import csv
from collections import defaultdict


def load_json_triples(file_path):
    """加载 JSON 格式的三元组文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        triples = json.load(f)
    return triples


def generate_neo4j_csv(triples, output_dir='.'):
    """
    生成 Neo4j 可导入的 CSV 文件

    需要生成三个文件：
    1. nodes.csv - 所有节点（实体）
    2. relationships.csv - 所有关系（边）
    """

    # 收集所有唯一的节点
    nodes_set = set()
    node_info = {}  # 记录节点的额外信息

    for triple in triples:
        subject = triple.get('subject', '')
        object_val = triple.get('object', '')

        # 添加主语节点
        if subject and subject.strip():
            nodes_set.add(subject)
            if subject not in node_info:
                node_info[subject] = {
                    'chunk': triple.get('chunk', ''),
                    'inferred': triple.get('inferred', False)
                }

        # 添加宾语节点
        if object_val and object_val.strip():
            nodes_set.add(object_val)
            if object_val not in node_info:
                # 宾语节点可能没有 chunk 和 inferred 信息
                node_info[object_val] = {
                    'chunk': '',
                    'inferred': ''
                }

    # 生成 nodes.csv
    nodes_file = f'{output_dir}/nodes3.csv'
    with open(nodes_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 写入表头 - Neo4j 格式
        writer.writerow([':ID', 'name', ':LABEL'])

        # 写入节点数据
        for idx, node in enumerate(sorted(nodes_set), start=1):
            # 默认标签为 Entity
            label = 'Entity'
            writer.writerow([idx, node, label])

    print(f"✓ 节点文件已生成：{nodes_file} (共 {len(nodes_set)} 个节点)")

    # 生成 relationships.csv
    relationships_file = f'{output_dir}/relationships3.csv'
    with open(relationships_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 写入表头 - Neo4j 格式
        writer.writerow([':START_ID', ':END_ID', ':TYPE', 'relation'])

        # 创建节点 ID 映射
        node_id_map = {node: idx for idx, node in enumerate(sorted(nodes_set), start=1)}

        # 写入关系数据
        rel_count = 0
        for triple in triples:
            subject = triple.get('subject', '')
            object_val = triple.get('object', '')
            predicate = triple.get('predicate', '')
            inferred = triple.get('inferred', False)

            # 跳过空节点
            if not subject or not object_val:
                continue

            if subject in node_id_map and object_val in node_id_map:
                start_id = node_id_map[subject]
                end_id = node_id_map[object_val]
                # Neo4j 关系类型需要大写，不能有特殊字符
                rel_type = sanitize_relation_type(predicate)
                writer.writerow([start_id, end_id, rel_type, predicate])
                rel_count += 1

    print(f"✓ 关系文件已生成：{relationships_file} (共 {rel_count} 条关系)")

    return nodes_file, relationships_file


def sanitize_relation_type(relation):
    """
    清理关系类型，使其符合 Neo4j 命名规范
    Neo4j 关系类型只能包含字母、数字、下划线
    """
    # 替换特殊字符
    sanitized = relation.replace('.', '_').replace('-', '_').replace(' ', '_')
    # 转为大写
    return sanitized.upper()

if __name__ == "__main__":
    # 配置路径
    input_file = r"D:\InformationExtraction\1ai-knowledge-graph-exp\OutPut\mydocument3.json"
    output_dir = r"D:\InformationExtraction\1ai-knowledge-graph-exp\OutPut"

    # 加载 JSON 三元组数据
    print("正在加载 JSON 三元组数据...")
    triples = load_json_triples(input_file)
    print(f"✓ 共加载 {len(triples)} 个三元组")

    # 生成 Neo4j CSV 文件
    print("\n正在生成 Neo4j CSV 文件...")
    nodes_file, relationships_file = generate_neo4j_csv(triples, output_dir)

    print("\n" + "=" * 50)
    print("完成！生成的文件:")
    print(f"  1. {nodes_file} - 节点数据")
    print(f"  2. {relationships_file} - 关系数据")
    print(f"  3. {output_dir}/import_to_neo4j.txt - 导入说明")
    print("=" * 50)
