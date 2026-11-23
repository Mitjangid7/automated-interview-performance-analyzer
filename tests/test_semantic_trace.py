from modules.semantic_analysis import (
    build_semantic_trace,
    calculate_keypoint_coverage,
    load_embedding_model,
)


def test_semantic_trace_exposes_preprocessing_and_similarity(monkeypatch):
    import modules.semantic_analysis as semantic

    monkeypatch.setattr(semantic, "load_embedding_model", lambda: None)
    trace = build_semantic_trace(
        "A model learns patterns from training data.",
        "Machine learning models learn patterns from training examples.",
    )

    assert trace["candidate_preprocessing"]["cleaned_text"]
    assert trace["candidate_preprocessing"]["tokens"]
    assert trace["reference_preprocessing"]["tokens"]
    assert trace["similarity"]["analysis_status"] == "fallback_tfidf"
    assert trace["embedding_available"] is False
    assert trace["vectorization_method"] == "TF-IDF sparse term vectors (fallback)"


def test_sentence_transformer_loads_and_produces_dense_trace():
    """Verify all-MiniLM-L6-v2 model initializes and produces 384-dimensional dense vectors."""
    model = load_embedding_model()
    assert model is not None, "Sentence Transformer all-MiniLM-L6-v2 should load successfully"

    trace = build_semantic_trace(
        "Lists are mutable sequences in Python.",
        "In Python, lists are mutable while tuples are immutable.",
    )

    assert trace["embedding_available"] is True
    assert trace["embedding_dimensions"] == 384
    assert len(trace["candidate_embedding_preview"]) == 8
    assert trace["similarity"]["analysis_status"] == "success"
    assert trace["similarity"]["model_name"] == "all-MiniLM-L6-v2"
    assert "dense embeddings" in trace["vectorization_method"].lower()


def test_keypoint_coverage_requires_textual_evidence_for_hashability():
    """Key-point coverage must NOT award coverage for hashability without textual evidence."""
    key_points = [
        "Lists are mutable; tuples are immutable",
        "Syntax differences: square brackets for lists and parentheses for tuples",
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable",
        "Appropriate practical use cases for both lists and tuples",
    ]
    concept_synonyms = {
        "Lists are mutable; tuples are immutable": [
            "mutable", "immutable", "can be modified", "cannot be modified"
        ],
        "Syntax differences: square brackets for lists and parentheses for tuples": [
            "square brackets", "parentheses", "[]", "()"
        ],
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable": [
            "hashable", "unhashable", "dictionary keys", "dict keys", "keys in a dict", "set elements", "hash function", "hash"
        ],
        "Appropriate practical use cases for both lists and tuples": [
            "use cases", "dynamic collection", "fixed records"
        ],
    }

    # Answer explicitly omits hashability / dictionary keys
    answer_without_hashability = (
        "Lists and tuples are sequences in Python. Lists are mutable and can be modified in place, "
        "while tuples are immutable and cannot be changed. Lists use square brackets and tuples use parentheses."
    )

    res = calculate_keypoint_coverage(
        answer_without_hashability,
        key_points,
        concept_synonyms=concept_synonyms,
    )

    hash_kp = "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable"
    assert hash_kp in res["missing_essential_points"], (
        f"Hashability must be marked missing when unmentioned. Got covered={res['covered_essential_points']}, "
        f"partial={res['partially_covered_essential_points']}"
    )
    assert hash_kp not in res["covered_essential_points"]
    assert hash_kp not in res["partially_covered_essential_points"]

    # When hashability IS explicitly mentioned
    answer_with_hashability = (
        "Lists are mutable while tuples are immutable. "
        "Because tuples are immutable, they are hashable and can be used as dictionary keys."
    )
    res_covered = calculate_keypoint_coverage(
        answer_with_hashability,
        key_points,
        concept_synonyms=concept_synonyms,
    )
    assert hash_kp in res_covered["covered_essential_points"]


def test_keypoint_coverage_requires_textual_evidence_for_use_cases():
    """Practical use-case concepts must require evidence explaining when/why to use, not just properties."""
    key_points = [
        "Lists are mutable; tuples are immutable",
        "Syntax differences: square brackets for lists and parentheses for tuples",
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable",
        "Appropriate practical use cases for both lists and tuples",
    ]
    concept_synonyms = {
        "Lists are mutable; tuples are immutable": [
            "mutable", "immutable", "can be modified", "cannot be modified"
        ],
        "Syntax differences: square brackets for lists and parentheses for tuples": [
            "square brackets", "parentheses", "[]", "()"
        ],
        "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable": [
            "hashable", "unhashable", "dictionary keys", "dict keys", "keys in a dict", "set elements", "hash function", "hash"
        ],
        "Appropriate practical use cases for both lists and tuples": [
            "use cases", "when to use", "dynamic collection", "coordinates", "rgb", "return multiple values", "shopping cart", "fixed records"
        ],
    }

    # User test answer: only mentions properties and syntax ("use square brackets", "use parentheses")
    answer_props_only = "Lists are mutable collections and use square brackets. Tuples are immutable and use parentheses."
    res = calculate_keypoint_coverage(answer_props_only, key_points, concept_synonyms=concept_synonyms)

    use_case_kp = "Appropriate practical use cases for both lists and tuples"
    hash_kp = "Tuples are hashable (can be dictionary keys or set elements); lists are unhashable"

    assert use_case_kp in res["missing_essential_points"], (
        f"Use cases must be MISSING when answer only mentions properties/syntax. Got covered: {res['covered_essential_points']}"
    )
    assert hash_kp in res["missing_essential_points"], "Hashability must be MISSING"
    assert "Lists are mutable; tuples are immutable" in res["covered_essential_points"]
    assert "Syntax differences: square brackets for lists and parentheses for tuples" in res["covered_essential_points"]

    # When practical use cases ARE explicitly explained
    answer_with_use_cases = (
        "Lists are mutable and tuples are immutable. Use lists for dynamic shopping cart items that change, "
        "and tuples for fixed records like geographic coordinates."
    )
    res_uc = calculate_keypoint_coverage(answer_with_use_cases, key_points, concept_synonyms=concept_synonyms)
    assert use_case_kp in res_uc["covered_essential_points"]


