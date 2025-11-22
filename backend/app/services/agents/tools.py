from langchain.tools import tool
from app.core.config import settings


@tool
def search_web(query: str) -> str:
    """Search the web using Brave Search API."""
    import requests

    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query}
    headers = {"Accept": "application/json", "X-Subscription-Token": settings.BRAVE_API_KEY}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.text
