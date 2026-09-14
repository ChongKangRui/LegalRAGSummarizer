
def precision_at_k(retrieved_ids : list, relevant_ids : list , k : int)->float:

    """Of the top-k things we actually retrieved, how many were correct?

    Measures noise: a low score means the LLM is being handed a lot of
    irrelevant clauses alongside whatever's actually right.
    """
    slice_retrieved_id = retrieved_ids[0 : k]

    found = set(slice_retrieved_id) & set(relevant_ids)

    return len(found) / k


def recall_at_k(retrieved_ids : list, relevant_ids : list , k : int)->float:
    """Of everything that was actually correct, how much did we find?

    Measures completeness: a low score means we missed a clause that
    should have been retrieved. Same slicing as precision, different
    denominator — that's the only difference between the two.
    """
    slice_retrieved_id = retrieved_ids[0 : k]
    
    found = set(slice_retrieved_id) & set(relevant_ids)
    
    return len(found) / len(relevant_ids)

def reciprocal_rank(retrieved_ids : list, relevant_ids : list)->float:
    """How far down the ranked list is the first correct answer?

    Doesn't slice to k and doesn't count every match — only cares about
    the position of the FIRST hit. Rank 1 (top of the list) scores 1.0;
    rank 2 scores 0.5; rank 3 scores 0.33, and so on. This is the only
    one of the three that's sensitive to ordering, not just presence.
    """
    for i,retrieved in enumerate(retrieved_ids):
        if retrieved in relevant_ids:
            return 1/(i + 1)

    return 0