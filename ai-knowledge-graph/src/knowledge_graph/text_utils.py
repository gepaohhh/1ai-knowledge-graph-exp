"""
Text processing utilities for the knowledge graph generator.
"""

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split a text into chunks of words with overlap.
    
    Args:
        text: The input text to chunk
        chunk_size: The size of each chunk in words
        overlap: The number of words to overlap between chunks
        
    Returns:
        List of text chunks
        1 text存储的是block内容
        2 是对bolck进行重新拼接
    """
    # If text is smaller than chunk size, return it as a single chunk
    if len(text) <= chunk_size:
        return text
    
    # Create chunks with overlap
    start = 0
    chunks = []
    while start < len(text):
        # Calculate end position for this chunk
        end = min(start + chunk_size, len(text))
            
        chunk = ""
        coverage = text[start:end]
        heading_ids = [heading_id for _, heading_id, _, _ in coverage] # 存储heading_id，避免重复添加heading
        for i, (index, heading_id, style, content) in enumerate(coverage):
            content = str(content).strip()
            if i == 0: # 如果是第一个 在heading_ids中没有heading_id，因此直接判断即可
                if index == heading_id:
                    chunk += f"##{content}##" + "\n"
                    continue
                chunk += f"##{text[heading_id][3]}##" + "\n"
                chunk += content + "\n"
                continue
            if heading_id != heading_ids[i-1]:
                if index == heading_id:
                    chunk += f"##{content}##" + "\n"
                    continue
                chunk += f"##{text[heading_id][3]}##" + "\n"
                chunk += content + "\n"
                continue
            chunk += content + "\n"
        chunks.append(chunk) # 将处理后的chunk存入chunks中
        
        '''根据overlap和chunksize 计算start位置，实现内容的平移'''
        start = end - overlap
        
        ''' 当切块到结束时，将剩余的文字添加到chunks中 '''
        if start < len(text) and start + chunk_size - overlap >= len(text):
            final_chunk = ""
            coverage = text[start:]
            heading_ids = [heading_id for _, heading_id, _, _ in coverage]
            for i, (index, heading_id, style, content) in enumerate(coverage):
                if i == 0:
                    if index == heading_id:
                        final_chunk += f"##{content}##" + "\n"
                        continue
                    final_chunk += f"##{text[heading_id][3]}##" + "\n" + content + "\n"
                if heading_id != heading_ids[i-1]:
                    if index == heading_id:
                        final_chunk += f"##{content}##" + "\n"
            chunks.append(final_chunk)
            break
    return chunks