"""Phase 2: Entity standardization prompts."""

# ENTITY_RESOLUTION_SYSTEM_PROMPT = """
# You are an expert in entity resolution and knowledge representation.
# Your task is to standardize entity names from a knowledge graph to ensure consistency.
# """
ENTITY_RESOLUTION_SYSTEM_PROMPT = """
你是一名实体解析与知识表示领域的专家。
你的任务是对知识图谱中的实体名称进行标准化，以确保其一致性。
"""


# def get_entity_resolution_user_prompt(entity_list):
#     return f"""
# Below is a list of entity names extracted from a knowledge graph.
# Some may refer to the same real-world entities but with different wording.
#
# Please identify groups of entities that refer to the same concept, and provide a standardized name for each group.
# Return your answer as a JSON object where the keys are the standardized names and the values are arrays of all variant names that should map to that standard name.
# Only include entities that have multiple variants or need standardization.
#
# Entity list:
# {entity_list}
#
# Format your response as valid JSON like this:
# {{
#   \"standardized name 1\": [\"variant 1\", \"variant 2\"],
#   \"standardized name 2\": [\"variant 3\", \"variant 4\", \"variant 5\"]
# }}
# """

def get_entity_resolution_user_prompt(entity_list):
    return f"""
以下是从知识图谱中提取的实体名称列表。
其中部分名称可能指向现实世界中的同一实体，但表述方式不同。

请识别指向同一概念的实体组，并为每组提供一个标准化名称。
请将结果以 JSON 对象形式返回，其中键为标准化名称，值为应映射到该标准名称的所有变体名称数组。
仅包含存在多个变体或需要标准化的实体。

实体列表:
{entity_list}

请将你的回复格式化为有效的 JSON，如下所示：
{{
  \"standardized name 1\": [\"variant 1\", \"variant 2\"],
  \"standardized name 2\": [\"variant 3\", \"variant 4\", \"variant 5\"]
}}
"""
