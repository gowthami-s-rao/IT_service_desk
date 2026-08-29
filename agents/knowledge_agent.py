"""
Knowledge Agent — searches the organization's knowledge base (SQLite table
`knowledge_articles`) for articles relevant to the request category/keywords.
"""
from app.models import KnowledgeArticle


def search_knowledge_base(request_text: str, category: str, limit: int = 3) -> list:
    text = request_text.lower()

    query = KnowledgeArticle.query.filter_by(category=category)
    candidates = query.all()

    if not candidates:
        candidates = KnowledgeArticle.query.all()

    scored = []
    for article in candidates:
        score = 0
        keywords = [k.strip().lower() for k in (article.keywords or "").split(",") if k.strip()]
        for kw in keywords:
            if kw in text:
                score += 2
        if article.category == category:
            score += 1
        scored.append((score, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [a for score, a in scored if score > 0][:limit]

    if not top:
        top = [a for _, a in scored[:limit]]

    return [a.to_dict() for a in top]
