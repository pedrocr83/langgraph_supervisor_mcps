from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web using Brave Search API."""
    import requests
    import os

    api_key = "BSA0Sm5MOtdGsEu1KkB53vNSleblKSx"
    url = "https://api.search.brave.com/res/v1/web/search"

    params = {"q": query}
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.text