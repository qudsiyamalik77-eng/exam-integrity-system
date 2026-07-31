from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple


def max_similarity_against_peers(candidate_answer: str, peer_answers: List[str]) -> Tuple[float, int]:
    if not candidate_answer or not peer_answers:
        return 0.0, -1

    documents = [candidate_answer] + peer_answers
    vectorizer = TfidfVectorizer().fit_transform(documents)
    vectors = vectorizer.toarray()

    candidate_vector = vectors[0:1]
    peer_vectors = vectors[1:]

    similarities = cosine_similarity(candidate_vector, peer_vectors)[0]
    max_index = int(similarities.argmax())
    max_score = float(similarities[max_index])

    return max_score, max_index