from langchain.tools import tool
from app.core.config import settings
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


@tool
def search_web(query: str) -> str:
    """Search the web using Brave Search API with automatic retry on rate limits.
    
    This tool automatically handles rate limiting (429 errors) by retrying with
    exponential backoff. Users will be notified of any delays.
    
    Args:
        query: The search query string
        
    Returns:
        Search results as JSON string
    """
    import requests

    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query}
    headers = {"Accept": "application/json", "X-Subscription-Token": settings.BRAVE_API_KEY}

    # Retry configuration
    max_retries = 5
    base_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Brave Search API request (attempt {attempt + 1}/{max_retries}): {query}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            logger.info(f"Brave Search API request successful on attempt {attempt + 1}")
            return response.text
            
        except requests.exceptions.HTTPError as e:
            # Check if it's a rate limit error (429)
            if e.response.status_code == 429:
                if attempt < max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Rate limit hit (429). Retrying in {delay} seconds... "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    
                    # Notify user about the delay
                    notification_msg = (
                        f"⏳ Brave Search API rate limit reached. "
                        f"Waiting {delay} seconds before retry {attempt + 2}/{max_retries}..."
                    )
                    logger.info(notification_msg)
                    
                    time.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    error_msg = (
                        f"❌ Brave Search API rate limit exceeded after {max_retries} attempts. "
                        f"Please try again in a few minutes. Query: {query}"
                    )
                    logger.error(error_msg)
                    return error_msg
            else:
                # Other HTTP errors - don't retry
                error_msg = f"Brave Search API error ({e.response.status_code}): {str(e)}"
                logger.error(error_msg)
                return error_msg
                
        except requests.exceptions.RequestException as e:
            # Network errors, timeouts, etc.
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Network error: {str(e)}. Retrying in {delay} seconds... "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                continue
            else:
                error_msg = f"Brave Search API network error after {max_retries} attempts: {str(e)}"
                logger.error(error_msg)
                return error_msg
    
    # This should never be reached, but just in case
    return f"Brave Search API failed after {max_retries} attempts. Please try again later."
