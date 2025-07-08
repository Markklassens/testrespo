import asyncio
import json
import httpx
import openai
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )
    
    async def generate_content(
        self, 
        prompt: str, 
        content_type: str = "blog",
        model: str = "llama-3.1-70b-versatile",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate content using Groq API"""
        try:
            system_prompts = {
                "blog": "You are an expert B2B content writer. Create engaging, informative blog posts about business tools and technology.",
                "tool_description": "You are a professional product copywriter. Create compelling, accurate descriptions for B2B tools.",
                "seo_content": "You are an SEO expert. Create optimized content for search engines while maintaining readability.",
                "meta_title": "Create compelling, SEO-optimized meta titles under 60 characters.",
                "meta_description": "Create compelling, SEO-optimized meta descriptions under 160 characters."
            }
            
            system_prompt = system_prompts.get(content_type, system_prompts["blog"])
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return {
                "content": content,
                "tokens_used": tokens_used,
                "model": model,
                "provider": "groq"
            }
            
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise Exception(f"Groq API error: {str(e)}")

class ClaudeService:
    """Service for interacting with Claude API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate_content(
        self, 
        prompt: str, 
        content_type: str = "blog",
        model: str = "claude-3-haiku-20240307",
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate content using Claude API"""
        try:
            system_prompts = {
                "blog": "You are an expert B2B content writer. Create engaging, informative blog posts about business tools and technology.",
                "tool_description": "You are a professional product copywriter. Create compelling, accurate descriptions for B2B tools.",
                "seo_content": "You are an SEO expert. Create optimized content for search engines while maintaining readability.",
                "meta_title": "Create compelling, SEO-optimized meta titles under 60 characters.",
                "meta_description": "Create compelling, SEO-optimized meta descriptions under 160 characters."
            }
            
            system_prompt = system_prompts.get(content_type, system_prompts["blog"])
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": model,
                        "max_tokens": max_tokens,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Claude API error: {response.text}")
                
                data = response.json()
                content = data["content"][0]["text"]
                tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                
                return {
                    "content": content,
                    "tokens_used": tokens_used,
                    "model": model,
                    "provider": "claude"
                }
                
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise Exception(f"Claude API error: {str(e)}")

class AIManager:
    """Unified manager for AI services with fallback support"""
    
    def __init__(self):
        self.groq_service = None
        self.claude_service = None
        
        # Admin API keys (fallback)
        self.admin_groq_key = os.getenv("ADMIN_GROQ_API_KEY")
        self.admin_claude_key = os.getenv("ADMIN_CLAUDE_API_KEY")
    
    def set_user_keys(self, groq_key: Optional[str] = None, claude_key: Optional[str] = None):
        """Set user-specific API keys"""
        if groq_key:
            self.groq_service = GroqService(groq_key)
        if claude_key:
            self.claude_service = ClaudeService(claude_key)
    
    def get_admin_services(self):
        """Get admin services for fallback"""
        admin_groq = GroqService(self.admin_groq_key) if self.admin_groq_key else None
        admin_claude = ClaudeService(self.admin_claude_key) if self.admin_claude_key else None
        return admin_groq, admin_claude
    
    async def generate_content(
        self, 
        prompt: str, 
        content_type: str = "blog",
        provider: Optional[str] = None,
        use_admin_fallback: bool = False
    ) -> Dict[str, Any]:
        """Generate content with intelligent provider selection and fallback"""
        
        services_to_try = []
        
        # Determine service order based on provider preference
        if provider == "groq" and self.groq_service:
            services_to_try.append(("groq", self.groq_service))
        elif provider == "claude" and self.claude_service:
            services_to_try.append(("claude", self.claude_service))
        else:
            # Auto selection - try both user services
            if self.groq_service:
                services_to_try.append(("groq", self.groq_service))
            if self.claude_service:
                services_to_try.append(("claude", self.claude_service))
        
        # Add admin fallback services if enabled
        if use_admin_fallback:
            admin_groq, admin_claude = self.get_admin_services()
            if admin_groq:
                services_to_try.append(("groq_admin", admin_groq))
            if admin_claude:
                services_to_try.append(("claude_admin", admin_claude))
        
        # Try services in order
        last_error = None
        for service_name, service in services_to_try:
            try:
                result = await service.generate_content(prompt, content_type)
                result["service_used"] = service_name
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"Service {service_name} failed: {str(e)}")
                continue
        
        # If all services failed
        if last_error:
            raise last_error
        else:
            raise Exception("No AI services available. Please configure API keys.")
    
    async def generate_seo_content(
        self, 
        tool_name: str, 
        tool_description: str, 
        target_keywords: List[str],
        search_engine: str = "google"
    ) -> Dict[str, Any]:
        """Generate SEO-optimized content for tools"""
        
        keywords_text = ", ".join(target_keywords)
        
        prompt = f"""
        Create SEO-optimized content for a B2B tool:
        
        Tool Name: {tool_name}
        Description: {tool_description}
        Target Keywords: {keywords_text}
        Search Engine: {search_engine}
        
        Please generate:
        1. An SEO-optimized meta title (under 60 characters)
        2. An SEO-optimized meta description (under 160 characters)  
        3. A detailed, keyword-rich content section (300-500 words)
        
        Format the response as JSON with keys: meta_title, meta_description, content
        """
        
        try:
            result = await self.generate_content(prompt, "seo_content", use_admin_fallback=True)
            
            # Try to parse JSON response
            try:
                seo_data = json.loads(result["content"])
                return {
                    "meta_title": seo_data.get("meta_title", ""),
                    "meta_description": seo_data.get("meta_description", ""),
                    "content": seo_data.get("content", ""),
                    "optimization_score": self._calculate_seo_score(seo_data, target_keywords),
                    "provider": result["provider"],
                    "tokens_used": result["tokens_used"]
                }
            except json.JSONDecodeError:
                # Fallback: parse unstructured response
                content = result["content"]
                return {
                    "meta_title": self._extract_meta_title(content),
                    "meta_description": self._extract_meta_description(content),
                    "content": content,
                    "optimization_score": 0.7,  # Default score
                    "provider": result["provider"],
                    "tokens_used": result["tokens_used"]
                }
                
        except Exception as e:
            raise Exception(f"Failed to generate SEO content: {str(e)}")
    
    def _calculate_seo_score(self, seo_data: Dict[str, str], keywords: List[str]) -> float:
        """Calculate SEO optimization score based on keyword usage"""
        score = 0.0
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 1.0
        
        content_text = f"{seo_data.get('meta_title', '')} {seo_data.get('meta_description', '')} {seo_data.get('content', '')}".lower()
        
        keywords_found = 0
        for keyword in keywords:
            if keyword.lower() in content_text:
                keywords_found += 1
        
        score = keywords_found / total_keywords
        
        # Bonus points for proper meta lengths
        meta_title = seo_data.get('meta_title', '')
        meta_description = seo_data.get('meta_description', '')
        
        if 30 <= len(meta_title) <= 60:
            score += 0.1
        if 120 <= len(meta_description) <= 160:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_meta_title(self, content: str) -> str:
        """Extract meta title from unstructured content"""
        lines = content.split('\n')
        for line in lines:
            if 'title' in line.lower() and len(line.strip()) <= 70:
                return line.strip().replace('Meta Title:', '').replace('Title:', '').strip()
        return "SEO Optimized Title"
    
    def _extract_meta_description(self, content: str) -> str:
        """Extract meta description from unstructured content"""
        lines = content.split('\n')
        for line in lines:
            if 'description' in line.lower() and 120 <= len(line.strip()) <= 180:
                return line.strip().replace('Meta Description:', '').replace('Description:', '').strip()
        return "SEO optimized description for better search visibility."

# Global AI manager instance
ai_manager = AIManager()