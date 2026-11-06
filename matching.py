
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(
    job_description,
    resume_text
):

    if not job_description.strip():
        return 0.0

    if not resume_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    try:

        vectors = vectorizer.fit_transform([
            job_description,
            resume_text
        ])

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        return round(
            float(similarity) * 100,
            2
        )

    except ValueError:
        return 0.0
