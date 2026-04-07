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
    elements =[]
    headings = []
    for _, (i, type, content) in enumerate(text):
        if type != 'Body Text' and type != 'table':
            if type == 'Normal':
                continue
            headings.append(content)
        if type == 'Body Text':
            elements.append(
                headings[-1] + '\n' + content
            )
        if type == 'table':
            elements.append(
                headings[-1] + '\n' + str(content)
            )
    # Split text into words
    # words = text.split()
    # If text is smaller than chunk size, return it as a single chunk
    if len(elements) <= chunk_size:
        return elements
    
    # Create chunks with overlap
    start = 0
    chunks = []
    while start < len(elements):
        # Calculate end position for this chunk
        end = min(start + chunk_size, len(elements))
        
        # Join words for this chunk
        chunk = '\n'.join(elements[start:end])
        chunks.append(chunk)
        
        # Move start position for next chunk, accounting for overlap
        start = end - overlap
        
        # If we're near the end and the last chunk would be too small, just exit
        if start < len(elements) and start + chunk_size - overlap >= len(elements):
            # Add remaining words as the final chunk
            final_chunk = ' '.join(elements[start:])
            chunks.append(final_chunk)
            break
    return chunks