import requests
import os
from typing import List, Dict, Optional
from schemas import SearchResult, SearchResponse
from dotenv import load_dotenv
import asyncio
import aiohttp
from datetime import datetime
import json

load_dotenv()

class SearchService:
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.bing_api_key = os.getenv("BING_API_KEY")
        
    async def search_google(self, query: str, num_results: int = 10) -> SearchResponse:
        """Search using Google Custom Search Engine API"""
        if not self.google_api_key or not self.google_cse_id:
            # Return mock results if API keys are not configured
            return self._get_mock_google_results(query, num_results)
        
        try:
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": query,
                "num": min(num_results, 10)  # Google CSE max is 10
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            if "items" not in data:
                return SearchResponse(
                    engine="google",
                    query=query,
                    results=[],
                    total_results=0
                )
            
            results = []
            for item in data["items"]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    displayLink=item.get("displayLink", "")
                ))
            
            return SearchResponse(
                engine="google",
                query=query,
                results=results,
                total_results=int(data.get("searchInformation", {}).get("totalResults", 0))
            )
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return self._get_mock_google_results(query, num_results)
    
    async def search_bing(self, query: str, num_results: int = 10) -> SearchResponse:
        """Search using Bing Search API"""
        if not self.bing_api_key:
            # Return mock results if API key is not configured
            return self._get_mock_bing_results(query, num_results)
        
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.bing_api_key
            }
            params = {
                "q": query,
                "count": min(num_results, 50),  # Bing max is 50
                "responseFilter": "Webpages"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            if "webPages" not in data or "value" not in data["webPages"]:
                return SearchResponse(
                    engine="bing",
                    query=query,
                    results=[],
                    total_results=0
                )
            
            results = []
            for item in data["webPages"]["value"]:
                results.append(SearchResult(
                    title=item.get("name", ""),
                    link=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    displayLink=item.get("displayUrl", "")
                ))
            
            return SearchResponse(
                engine="bing",
                query=query,
                results=results,
                total_results=data["webPages"].get("totalEstimatedMatches", 0)
            )
            
        except Exception as e:
            print(f"Bing search error: {str(e)}")
            return self._get_mock_bing_results(query, num_results)
    
    def _get_mock_google_results(self, query: str, num_results: int) -> SearchResponse:
        """Return mock Google search results when API is not configured"""
        mock_results = []
        for i in range(min(num_results, 5)):
            mock_results.append(SearchResult(
                title=f"Google Search Result {i+1} for '{query}'",
                link=f"https://example.com/result-{i+1}",
                snippet=f"This is a mock search result {i+1} for the query '{query}'. In a real implementation, this would be powered by Google Custom Search Engine API.",
                displayLink=f"example.com/result-{i+1}"
            ))
        
        return SearchResponse(
            engine="google",
            query=query,
            results=mock_results,
            total_results=1000000  # Mock total
        )
    
    def _get_mock_bing_results(self, query: str, num_results: int) -> SearchResponse:
        """Return mock Bing search results when API is not configured"""
        mock_results = []
        for i in range(min(num_results, 5)):
            mock_results.append(SearchResult(
                title=f"Bing Search Result {i+1} for '{query}'",
                link=f"https://example.com/bing-result-{i+1}",
                snippet=f"This is a mock Bing search result {i+1} for the query '{query}'. In a real implementation, this would be powered by Bing Search API v7.",
                displayLink=f"example.com/bing-result-{i+1}"
            ))
        
        return SearchResponse(
            engine="bing",
            query=query,
            results=mock_results,
            total_results=2000000  # Mock total
        )
    
    async def combined_search(self, query: str, engines: List[str] = ["google", "bing"], num_results: int = 10) -> Dict[str, any]:
        """Perform search across multiple engines"""
        tasks = []
        results = {}
        errors = {}
        
        if "google" in engines:
            tasks.append(("google", self.search_google(query, num_results)))
        if "bing" in engines:
            tasks.append(("bing", self.search_bing(query, num_results)))
        
        for engine_name, task in tasks:
            try:
                result = await task
                results[engine_name] = result
            except Exception as e:
                errors[engine_name] = str(e)
        
        return {
            **results,
            "errors": errors
        }

# Global search service instance
search_service = SearchService()