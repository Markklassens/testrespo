#!/usr/bin/env python3
"""
Script to add sample free tools to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base, FreeTool
import uuid

# Create database tables
Base.metadata.create_all(bind=engine)

def create_sample_tools():
    db = SessionLocal()
    
    sample_tools = [
        {
            "name": "Google Search",
            "description": "Search the web using Google's powerful search engine. Find information, websites, images, and more across billions of web pages.",
            "short_description": "Google's web search engine",
            "slug": "google-search",
            "category": "Search",
            "icon": "🔍",
            "color": "#4285f4",
            "website_url": "https://www.google.com",
            "features": "Web search, Image search, News search, Shopping search, Maps integration",
            "meta_title": "Google Search - Find Information Online",
            "meta_description": "Use Google Search to find information across the web quickly and efficiently."
        },
        {
            "name": "Bing Search",
            "description": "Microsoft's search engine providing web search, images, videos, and news. Get rewards for searching and discover relevant content.",
            "short_description": "Microsoft's search engine",
            "slug": "bing-search",
            "category": "Search",
            "icon": "🔎",
            "color": "#0078d4",
            "website_url": "https://www.bing.com",
            "features": "Web search, Image search, Video search, News search, Rewards program",
            "meta_title": "Bing Search - Microsoft Search Engine",
            "meta_description": "Search the web with Bing and earn rewards while finding relevant information."
        },
        {
            "name": "SEO Analyzer",
            "description": "Analyze websites for SEO performance using both Google and Bing search results. Get insights on keyword rankings, backlinks, and optimization opportunities.",
            "short_description": "SEO analysis tool",
            "slug": "seo-analyzer",
            "category": "SEO",
            "icon": "📊",
            "color": "#10b981",
            "website_url": "https://example.com/seo-analyzer",
            "features": "Keyword analysis, SERP tracking, Backlink analysis, Site audit, Competitor analysis",
            "meta_title": "SEO Analyzer - Website SEO Analysis Tool",
            "meta_description": "Analyze your website's SEO performance and get actionable insights to improve search rankings."
        },
        {
            "name": "Competitor Research",
            "description": "Research your competitors using search data from multiple engines. Discover their top-performing content, keywords, and strategies.",
            "short_description": "Competitor analysis tool",
            "slug": "competitor-research",
            "category": "Marketing",
            "icon": "🎯",
            "color": "#f59e0b",
            "website_url": "https://example.com/competitor-research",
            "features": "Competitor analysis, Keyword research, Content analysis, Market research, SERP analysis",
            "meta_title": "Competitor Research - Analyze Your Competition",
            "meta_description": "Research your competitors and discover their strategies using advanced search analysis."
        },
        {
            "name": "Keyword Finder",
            "description": "Find profitable keywords for your content and SEO strategy. Search across multiple engines to discover trending topics and search volumes.",
            "short_description": "Keyword research tool",
            "slug": "keyword-finder",
            "category": "SEO",
            "icon": "🔑",
            "color": "#8b5cf6",
            "website_url": "https://example.com/keyword-finder",
            "features": "Keyword research, Search volume analysis, Keyword difficulty, Trend analysis, Long-tail keywords",
            "meta_title": "Keyword Finder - Discover Profitable Keywords",
            "meta_description": "Find the best keywords for your content and SEO campaigns with our advanced keyword research tool."
        },
        {
            "name": "Content Ideas Generator",
            "description": "Generate content ideas based on trending searches and popular topics. Use search data to create engaging content that resonates with your audience.",
            "short_description": "Content ideation tool",
            "slug": "content-ideas-generator",
            "category": "Content",
            "icon": "💡",
            "color": "#ef4444",
            "website_url": "https://example.com/content-ideas",
            "features": "Content ideation, Trending topics, Search trends, Content planning, Topic research",
            "meta_title": "Content Ideas Generator - Create Engaging Content",
            "meta_description": "Generate fresh content ideas based on trending searches and popular topics."
        },
        {
            "name": "SERP Checker",
            "description": "Check search engine results pages (SERPs) for any keyword across Google and Bing. Analyze rankings, featured snippets, and SERP features.",
            "short_description": "SERP analysis tool",
            "slug": "serp-checker",
            "category": "SEO",
            "icon": "📈",
            "color": "#06b6d4",
            "website_url": "https://example.com/serp-checker",
            "features": "SERP analysis, Ranking tracking, Featured snippets, Local results, Mobile vs desktop",
            "meta_title": "SERP Checker - Analyze Search Results",
            "meta_description": "Check and analyze search engine results pages for any keyword across multiple search engines."
        },
        {
            "name": "Trend Analyzer",
            "description": "Analyze search trends and discover what people are searching for. Track trending topics and seasonal patterns across different search engines.",
            "short_description": "Search trend analysis",
            "slug": "trend-analyzer",
            "category": "Analytics",
            "icon": "📊",
            "color": "#84cc16",
            "website_url": "https://example.com/trend-analyzer",
            "features": "Trend analysis, Seasonal patterns, Geographic trends, Historical data, Forecast predictions",
            "meta_title": "Trend Analyzer - Discover Search Trends",
            "meta_description": "Analyze search trends and discover what people are searching for across different regions and time periods."
        }
    ]
    
    try:
        for tool_data in sample_tools:
            # Check if tool already exists
            existing_tool = db.query(FreeTool).filter(FreeTool.slug == tool_data["slug"]).first()
            if existing_tool:
                print(f"Tool '{tool_data['name']}' already exists, skipping...")
                continue
            
            # Create new tool
            tool = FreeTool(
                id=str(uuid.uuid4()),
                **tool_data
            )
            db.add(tool)
            print(f"Created tool: {tool_data['name']}")
        
        db.commit()
        print(f"Successfully created {len(sample_tools)} sample free tools!")
        
    except Exception as e:
        print(f"Error creating sample tools: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_tools()