"""Phase 3 & 4: Relationship inference prompts."""

# RELATIONSHIP_INFERENCE_SYSTEM_PROMPT = """
# You are an expert in knowledge representation and inference.
# Your task is to infer plausible relationships between disconnected entities in a knowledge graph.
# """
#
#
# def get_relationship_inference_user_prompt(entities1, entities2, triples_text):
#     return f"""
# I have a knowledge graph with two disconnected communities of entities.
#
# Community 1 entities: {entities1}
# Community 2 entities: {entities2}
#
# Here are some existing relationships involving these entities:
# {triples_text}
#
# Please infer 2-3 plausible relationships between entities from Community 1 and entities from Community 2.
# Return your answer as a JSON array of triples in the following format:
#
# [
#   {{
#     \"subject\": \"entity from community 1\",
#     \"predicate\": \"inferred relationship\",
#     \"object\": \"entity from community 2\"
#   }},
#   ...
# ]
#
# Only include highly plausible relationships with clear predicates.
# IMPORTANT: The inferred relationships (predicates) MUST be no more than 3 words maximum. Preferably 1-2 words. Never more than 3.
# For predicates, use short phrases that clearly describe the relationship.
# IMPORTANT: Make sure the subject and object are different entities - avoid self-references.
# """
#
#
# WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT = """
# You are an expert in knowledge representation and inference.
# Your task is to infer plausible relationships between semantically related entities that are not yet connected in a knowledge graph.
# """
#
#
# def get_within_community_inference_user_prompt(pairs_text, triples_text):
#     return f"""
# I have a knowledge graph with several entities that appear to be semantically related but are not directly connected.
#
# Here are some pairs of entities that might be related:
# {pairs_text}
#
# Here are some existing relationships involving these entities:
# {triples_text}
#
# Please infer plausible relationships between these disconnected pairs.
# Return your answer as a JSON array of triples in the following format:
#
# [
#   {{
#     \"subject\": \"entity1\",
#     \"predicate\": \"inferred relationship\",
#     \"object\": \"entity2\"
#   }},
#   ...
# ]
#
# Only include highly plausible relationships with clear predicates.
# IMPORTANT: The inferred relationships (predicates) MUST be no more than 3 words maximum. Preferably 1-2 words. Never more than 3.
# IMPORTANT: Make sure that the subject and object are different entities - avoid self-references.
# """

RELATIONSHIP_INFERENCE_SYSTEM_PROMPT = """
你是一名知识表示与推理领域的专家。
你的任务是推断知识图谱中离散实体之间可能存在的合理关系。
"""


def get_relationship_inference_user_prompt(entities1, entities2, triples_text):
    return f"""
我拥有一个包含两个互不连通的实体社群的知识图谱。

社群 1 实体: {entities1}
社群 1 实体: {entities2}

以下是涉及这些实体的一些现有关系：
{triples_text}

请推断社群 1 与社群 2 实体之间 2-3 条合理的可能关系。
请将结果以三元组形式的 JSON 数组返回，格式如下：

[
  {{
    \"subject\": \"entity from community 1\",
    \"predicate\": \"inferred relationship\",
    \"object\": \"entity from community 2\"
  }},
  ...
]

仅包含具有清晰谓词的高度合理关系。
重要提示：推断出的关系（谓词）最多不得超过 3 个单词，最好为 1-2 个单词，绝不能超过 3 个。
对于谓词，请使用能清晰描述关系的简短短语。
重要提示：确保主语和宾语是不同的实体——避免自引用。
"""


WITHIN_COMMUNITY_INFERENCE_SYSTEM_PROMPT = """
你是一名知识表示与推理领域的专家。
你的任务是推断知识图谱中尚未连接但语义相关的实体之间可能存在的合理关系。
"""


def get_within_community_inference_user_prompt(pairs_text, triples_text):
    return f"""
我拥有一个知识图谱，其中包含几个看似语义相关但尚未直接连接的实体。

以下是几组可能相关的实体对：
{pairs_text}

以下是涉及这些实体的一些现有关系：
{triples_text}

请推断这些未连接实体对之间可能存在的合理关系。
请将结果以三元组形式的 JSON 数组返回，格式如下：

[
  {{
    \"subject\": \"entity1\",
    \"predicate\": \"inferred relationship\",
    \"object\": \"entity2\"
  }},
  ...
]

仅包含具有清晰谓词的高度合理关系。
重要提示：推断出的关系（谓词）**最多不得超过 3 个单词**，最好为 1-2 个单词，绝不能超过 3 个。
重要提示：确保主语和宾语是不同的实体——避免自引用。
"""
