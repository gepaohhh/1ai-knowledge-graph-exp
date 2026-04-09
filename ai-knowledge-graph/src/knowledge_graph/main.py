"""
Knowledge Graph Generator and Visualizer main module.
"""
import argparse
import json
import os
import sys
import pandas as pd

import pandas
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

# Add the parent directory to the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.knowledge_graph.config import load_config
from src.knowledge_graph.llm import call_llm, extract_json_from_text
from src.knowledge_graph.visualization import visualize_knowledge_graph, sample_data_visualization
from src.knowledge_graph.text_utils import chunk_text
from src.knowledge_graph.entity_standardization import standardize_entities, infer_relationships, limit_predicate_length
from src.knowledge_graph.prompts import prompt_factory
from src.knowledge_graph.validatation import flatten_blocks_to_text, validate_triples_against_text
from src.knowledge_graph.entity_standardization import load_stopwords_to_set

def process_with_llm(config, input_text, debug=False):
    """
    Process input text with LLM to extract triples.
    
    Args:
        config: Configuration dictionary
        input_text: Text to analyze
        debug: If True, print detailed debug information
        
    Returns:
        List of extracted triples or None if processing failed
    """
    # Use prompts from the centralized prompt factory
    system_prompt = prompt_factory.get_prompt("main_system")
    user_prompt = prompt_factory.get_prompt("main_user")
    user_prompt += f"```\n{input_text}```\n" 

    # LLM configuration
    model = config["llm"]["model"]
    api_key = config["llm"]["api_key"]
    max_tokens = config["llm"]["max_tokens"]
    temperature = config["llm"]["temperature"]
    base_url = config["llm"]["base_url"]
    
    # Process with LLM
    metadata = {}
    response = call_llm(model, user_prompt, api_key, system_prompt, max_tokens, temperature, base_url)
    
    # Print raw response only if debug mode is on
    if debug:
        print("Raw LLM response:")
        print(response)
        print("\n---\n")
    
    # Extract JSON from the response
    result = extract_json_from_text(response)
    
    if result:
        # Validate and filter triples to ensure they have all required fields
        valid_triples = []
        invalid_count = 0
        
        for item in result:
            if isinstance(item, dict) and "subject" in item and "predicate" in item and "object" in item:
                # Add metadata to valid items
                valid_triples.append(dict(item, **metadata))
            else:
                invalid_count += 1
        
        if invalid_count > 0:
            print(f"Warning: Filtered out {invalid_count} invalid triples missing required fields")
        
        if not valid_triples:
            print("Error: No valid triples found in LLM response")
            return None
        
        # Apply predicate length limit to all valid triples 限制关系长度
        for triple in valid_triples:
            triple["predicate"] = limit_predicate_length(triple["predicate"])
        
        # Print extracted JSON only if debug mode is on
        if debug:
            print("Extracted JSON:")
            print(json.dumps(valid_triples, indent=2))  # Pretty print the JSON
        
        return valid_triples
    else:
        # Always print error messages even if debug is off
        print("\n\nERROR ### Could not extract valid JSON from response: ", response, "\n\n")
        return None


#############################################
# doc文档切块处理 记录文档的  (id,所属的父级标题,文档格式,内容)
#############################################
def docx_table_to_dataframe(table: Table):
    """将表格数据存入panda里，不考虑表头信息"""
    data = []
    for row in table.rows:
        row_data = [cell.text.strip() for cell in row.cells]
        data.append(row_data)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def iter_block_items(path):
    """
    用于遍历.docx文件中的段落和表格，按照文档顺序返回每个段落和表格对象。
    Args: doc文件路径_path
    Returns: Paragraph 或者 Table
    """
    doc = Document(path)
    bodys = doc.element.body
    for child in bodys.iterchildren():
        if isinstance(child, CT_P):
            # 如果是段落节点，封装成 Paragraph 对象并 yield
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            # 如果是表格节点，封装成 Table 对象并 yield
            yield Table(child, doc)

def operate_doc(path):
    """ 读取.docx文件，提取其中的段落和表格内容，并将它们存储在一个列表中返回。
        每个列表项是一个元组，包含块的索引、类型（段落或表格）和内容（段落文本或表格数据）。"""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    block_list = []
    heading_id = -1
    # 使用生成器按顺序遍历
    for index, block in enumerate(iter_block_items(path)):
        if isinstance(block, Paragraph):
            # 如果是标题，更新当前标题ID
            if block.style.name.startswith('Heading'):
                heading_id = index
        if isinstance(block, Paragraph): # 文本
            # 存入段落内容 标题 文本等
            block_list.append(
                (index, heading_id, block.style.name, block.text)
            )
        if isinstance(block, Table): # 表格
            # 遍历表格的行和单元格
            block_list.append(
                (index, heading_id, "table", docx_table_to_dataframe(block))
            )
    return block_list
#############################################
#############################################


def process_text_in_chunks(config, full_text, debug=False):
    """
        Process a large text by breaking it into chunks with overlap,
        and then processing each chunk separately.
        
        Args:
            config: Configuration dictionary
            full_text: The complete text to process 存储的文件路径
            debug: If True, print detailed debug information
        
        Returns:
            List of all extracted triples from all chunks
    """
    # Get chunking parameters from config
    chunk_size = config.get("chunking", {}).get("chunk_size", 500)
    overlap = config.get("chunking", {}).get("overlap", 50)

    # # 处理doc文档
    # text_list = full_text

    # Split text into chunks 将文本块进行前后关联
    text_chunks = chunk_text(full_text, chunk_size, overlap)
    # # 打印文档分块信息
    for chunk in text_chunks:
        print(chunk)
        print("*" * 50)

    # #################################################################################
    print("=" * 50)
    print("PHASE 1: INITIAL TRIPLE EXTRACTION 初始三元组提取")
    print("=" * 50)
    print(f"Processing text in {len(text_chunks)} chunks (size: {chunk_size} words, overlap: {overlap} words)")
    
    # Process each chunk 进行实体关系类别抽取
    all_results = []
    for i, chunk in enumerate(text_chunks):
        print(f"处理文本块 {i+1}/{len(text_chunks)} ({len(chunk.split())} 字)")
        print(chunk)
        
        # Process the chunk with LLM
        chunk_results = process_with_llm(config, chunk, debug)
        print(chunk_results)
        if chunk_results:
            # Add chunk information to each triple
            for item in chunk_results:
                item["chunk"] = i + 1
            
            # Add to overall results
            all_results.extend(chunk_results)
        else:
            print(f"Warning: Failed to extract triples from chunk {i+1}")
    
    print(f"\nExtracted a total of {len(all_results)} triples from all chunks")

    # #################################################################################
    # Apply entity standardization if enabled 实体标准化
    if config.get("standardization", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 2: ENTITY STANDARDIZATION 实体标准化")
        print("="*50)
        print(f"Starting with {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")
        
        all_results = standardize_entities(all_results, config)
        
        print(f"After standardization: {len(all_results)} triples and {len(get_unique_entities(all_results))} unique entities")

    # #################################################################################
    # Apply relationship inference if enabled 关系推理
    if config.get("inference", {}).get("enabled", False):
        print("\n" + "="*50)
        print("PHASE 3: RELATIONSHIP INFERENCE")
        print("="*50)
        print(f"Starting with {len(all_results)} triples")
        
        # Count existing relationships
        relationship_counts = {}
        for triple in all_results:
            relationship_counts[triple["predicate"]] = relationship_counts.get(triple["predicate"], 0) + 1
        
        print("Top 5 relationship types before inference: 推理前关系类型")
        for pred, count in sorted(relationship_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        all_results = infer_relationships(all_results, config)
        
        # Count relationships after inference
        relationship_counts_after = {}
        for triple in all_results:
            relationship_counts_after[triple["predicate"]] = relationship_counts_after.get(triple["predicate"], 0) + 1
        
        print("\nTop 5 relationship types after inference 推理后前5的关系推理:")
        for pred, count in sorted(relationship_counts_after.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {pred}: {count} occurrences")
        
        # Count inferred relationships
        inferred_count = sum(1 for triple in all_results if triple.get("inferred", False))
        print(f"\nAdded {inferred_count} inferred relationships")
        print(f"Final knowledge graph: {len(all_results)} triples")
    
    return all_results

def get_unique_entities(triples):
    """
    Get the set of unique entities from the triples.
    
    Args:
        triples: List of triple dictionaries
        
    Returns:
        Set of unique entity names
    """
    entities = set()
    for triple in triples:
        if not isinstance(triple, dict):
            continue
        if "subject" in triple:
            entities.add(triple["subject"])
        if "object" in triple:
            entities.add(triple["object"])
    return entities

def main():
    """Main entry point for the knowledge graph generator."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Knowledge Graph Generator and Visualizer')
    # 用于生成测试的知识图谱
    parser.add_argument('--test', action='store_true', help='Generate a test visualization with sample data')
    parser.add_argument('--config', type=str, default='config.toml', help='Path to configuration file')
    parser.add_argument('--output', type=str, default='knowledge_graph.html', help='Output HTML file path')
    parser.add_argument('--input', type=str, required=False, help='Path to input text file (required unless --test is used)')
    # 用于控制LLM的提示词和提取的json结果
    parser.add_argument('--debug', action='store_true', help='Enable debug output (raw LLM responses and extracted JSON)')
    # 禁用实体标准化
    parser.add_argument('--no-standardize', action='store_true', help='Disable entity standardization')
    # 禁用关系推理
    parser.add_argument('--no-inference', action='store_true', help='Disable relationship inference')
    parser.add_argument('--validate-alignment', action='store_true', help='Validate triple/text alignment and export a validation report')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if not config:
        print(f"Failed to load configuration from {args.config}. Exiting.")
        return
    
    # If test flag is provided, generate a sample visualization
    if args.test:
        print("Generating sample data visualization...")
        sample_data_visualization(args.output, config=config)
        print(f"\nSample visualization saved to {args.output}")
        print(f"To view the visualization, open the following file in your browser:")
        print(f"file://{os.path.abspath(args.output)}")
        return
    
    # For normal processing, input file is required
    if not args.input:
        print("Error: --input is required unless --test is used")
        parser.print_help()
        return
    
    # Override configuration settings with command line arguments
    if args.no_standardize:
        config.setdefault("standardization", {})["enabled"] = False
    if args.no_inference:
        config.setdefault("inference", {})["enabled"] = False
        
        
    #######################################################
    # 加载文档 进行切块 抽取 分析
    #######################################################
    # Load input text from file 
    try:
        # with open(args.input, 'r', encoding='utf-8') as f:
        #     input_text = f.read()
        input_text = operate_doc(args.input) # 读取doc文档，对 标题 段落 表格 分开处理
        print(f"Using input text from file: {args.input}")
    except Exception as e:
        print(f"Error reading input file {args.input}: {e}")
        return
    
    # Process text in chunks 代码核心位置 按文本块处理所有文本，得到三元组列表 
    result = process_text_in_chunks(config, input_text, args.debug)
    
    # Validate triple alignment against source text if requested
    validation_enabled = args.validate_alignment or config.get("validation", {}).get("enabled", False)
    if validation_enabled and result:
        threshold = config.get("validation", {}).get("support_threshold", 0.6)
        min_sentence_length = config.get("validation", {}).get("min_sentence_length", 20)
        validation_report = validate_triples_against_text(
            result,
            flatten_blocks_to_text(input_text),
            threshold=threshold,
            min_sentence_length=min_sentence_length,
        )

        validation_output = args.output.replace('.html', '.validation.json')
        try:
            with open(validation_output, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, ensure_ascii=False, indent=2)
            print(f"Saved validation report to {validation_output}")
            print(
                f"Validation summary: supported {validation_report['supported_triples']}/"
                f"{validation_report['total_triples']} triples "
                f"(ratio={validation_report['support_ratio']}, avg_score={validation_report['avg_score']})"
            )
        except Exception as e:
            print(f"Warning: Could not save validation report to {validation_output}: {e}")
    
    #######################################################
    # 将抽取结果进行数据保存和可视化展示
    #######################################################
    if result:
        # Save the raw data as JSON for potential reuse
        json_output = args.output.replace('.html', '.json')
        try:
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Saved raw knowledge graph data to {json_output}")
        except Exception as e:
            print(f"Warning: Could not save raw data to {json_output}: {e}")
        
        # Visualize the knowledge graph
        stats = visualize_knowledge_graph(result, args.output, config=config)
        print("\nKnowledge Graph Statistics:")
        print(f"Nodes: {stats['nodes']}")
        print(f"Edges: {stats['edges']}")
        print(f"Communities: {stats['communities']}")
        
        # Provide command to open the visualization in a browser
        print("\nTo view the visualization, open the following file in your browser:")
        print(f"file://{os.path.abspath(args.output)}")
    else:
        print("Knowledge graph generation failed due to errors in LLM processing.")

if __name__ == "__main__":
    main() 