def calculate_h_index(citations: List[int]) -> int:
    """Calculate h-index from citation counts"""
    if not citations:
        return 0
    
    sorted_citations = sorted(citations, reverse=True)
    h_index = 0
    
    for i, citation_count in enumerate(sorted_citations):
        if citation_count >= i + 1:
            h_index = i + 1
        else:
            break
    
    return h_index

def calculate_i10_index(citations: List[int]) -> int:
    """Calculate i10-index (papers with 10+ citations)"""
    return sum(1 for c in citations if c >= 10)