import os
import asyncio
from typing import Optional, Dict, Any
from groq import Groq
import logging

logger = logging.getLogger(__name__)

class GroqAIService:
    def __init__(self):
        self.api_key = os.getenv('ADMIN_GROQ_API_KEY')
        if not self.api_key:
            logger.warning("Groq API key not found in environment variables")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """Check if Groq service is available"""
        return self.client is not None and self.api_key is not None
    
    async def generate_blog_content(
        self, 
        prompt: str, 
        content_type: str = "full_post",
        existing_content: str = "",
        title: str = "",
        category: str = "",
        tone: str = "professional",
        length: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate blog content using Groq API
        
        Args:
            prompt: The main prompt for content generation
            content_type: Type of content (full_post, continuation, introduction, body, conclusion)
            existing_content: Existing content for continuation
            title: Blog title
            category: Blog category
            tone: Writing tone (professional, casual, technical, friendly)
            length: Content length (short, medium, long)
        """
        if not self.is_available():
            raise Exception("Groq API service is not available. Please check your API key.")
        
        try:
            # Create system message based on content type and parameters
            system_message = self._create_system_message(content_type, tone, length, category)
            
            # Create user message based on content type
            user_message = self._create_user_message(
                content_type, prompt, existing_content, title, category
            )
            
            # Make API call to Groq
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # Using Llama 3 8B model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2048,
                temperature=0.7,
                top_p=0.9
            )
            
            generated_content = response.choices[0].message.content
            
            # Extract word count for reading time calculation
            word_count = len(generated_content.split())
            reading_time = max(1, round(word_count / 200))
            
            return {
                "success": True,
                "content": generated_content,
                "word_count": word_count,
                "reading_time": reading_time,
                "content_type": content_type,
                "model_used": "llama3-8b-8192"
            }
            
        except Exception as e:
            logger.error(f"Error generating content with Groq: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "word_count": 0,
                "reading_time": 0
            }
    
    def _create_system_message(self, content_type: str, tone: str, length: str, category: str) -> str:
        """Create system message based on parameters"""
        
        tone_instructions = {
            "professional": "Write in a professional, authoritative tone suitable for business audiences.",
            "casual": "Write in a casual, conversational tone that's easy to read and engaging.",
            "technical": "Write in a technical tone with detailed explanations and industry-specific terminology.",
            "friendly": "Write in a friendly, approachable tone that feels personal and welcoming."
        }
        
        length_instructions = {
            "short": "Keep the content concise, around 300-500 words.",
            "medium": "Write medium-length content, around 800-1200 words.",
            "long": "Create comprehensive, detailed content, around 1500-2500 words."
        }
        
        base_instruction = f"""You are an expert blog writer specializing in B2B content and {category} topics. 
{tone_instructions.get(tone, tone_instructions['professional'])}
{length_instructions.get(length, length_instructions['medium'])}

Guidelines:
- Create engaging, valuable content that provides real insights
- Use clear headings and subheadings for better readability
- Include actionable tips and practical advice
- Ensure the content is SEO-friendly with natural keyword usage
- Write in a way that establishes authority and builds trust
- Use markdown formatting for better structure (##, ###, **bold**, *italic*)
"""
        
        if content_type == "full_post":
            return base_instruction + """
Your task is to write a complete blog post including:
1. An engaging introduction that hooks the reader
2. Well-structured main content with clear sections
3. A compelling conclusion with key takeaways
4. Natural inclusion of relevant keywords throughout
"""
        elif content_type == "introduction":
            return base_instruction + """
Your task is to write an engaging blog post introduction that:
1. Hooks the reader with an interesting opening
2. Clearly states what the post will cover
3. Explains why the topic matters to the reader
4. Sets up the main content that will follow
"""
        elif content_type == "body":
            return base_instruction + """
Your task is to write the main body content that:
1. Delivers on the promises made in the introduction
2. Provides detailed, actionable information
3. Uses clear headings and subheadings
4. Includes practical examples and insights
"""
        elif content_type == "conclusion":
            return base_instruction + """
Your task is to write a strong conclusion that:
1. Summarizes the key points covered
2. Provides clear takeaways for the reader
3. Includes a call-to-action when appropriate
4. Ends on a compelling note that encourages engagement
"""
        elif content_type == "continuation":
            return base_instruction + """
Your task is to continue the existing content naturally and seamlessly:
1. Maintain the same tone and style as the existing content
2. Build upon the ideas already presented
3. Add value with new insights or expanded explanations
4. Ensure smooth flow from the existing content
"""
        
        return base_instruction
    
    def _create_user_message(
        self, 
        content_type: str, 
        prompt: str, 
        existing_content: str, 
        title: str, 
        category: str
    ) -> str:
        """Create user message based on content type"""
        
        if content_type == "full_post":
            return f"""Please write a complete blog post with the following details:

Title: {title if title else 'Generate an appropriate title'}
Category: {category}
Topic/Prompt: {prompt}

Please create a comprehensive blog post that covers this topic thoroughly and provides real value to readers in the {category} space."""
        
        elif content_type == "continuation":
            return f"""Please continue this existing blog content naturally:

Current Title: {title}
Category: {category}
Existing Content:
{existing_content}

Continuation Request: {prompt}

Please continue this content seamlessly, maintaining the same tone and style while adding valuable information based on the request."""
        
        elif content_type in ["introduction", "body", "conclusion"]:
            context = f"Title: {title}\nCategory: {category}\n" if title or category else ""
            return f"""{context}Please write a {content_type} for a blog post about:

{prompt}

Make sure it fits well as a {content_type} section and provides value to readers interested in {category} topics."""
        
        return prompt
    
    async def generate_blog_title(self, topic: str, category: str = "") -> Dict[str, Any]:
        """Generate blog title suggestions"""
        if not self.is_available():
            raise Exception("Groq API service is not available.")
        
        try:
            system_message = """You are an expert at creating compelling blog titles. Generate 5 different title options that are:
- Engaging and click-worthy
- SEO-friendly with relevant keywords
- Professional but attention-grabbing
- Specific and valuable to the target audience

Return only the titles, one per line, without numbering or bullets."""
            
            user_message = f"Generate blog title options for this topic: {topic}"
            if category:
                user_message += f" (Category: {category})"
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            titles = response.choices[0].message.content.strip().split('\n')
            titles = [title.strip() for title in titles if title.strip()]
            
            return {
                "success": True,
                "titles": titles[:5]  # Ensure max 5 titles
            }
            
        except Exception as e:
            logger.error(f"Error generating titles with Groq: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "titles": []
            }
    
    async def improve_content(self, content: str, improvement_type: str = "enhance") -> Dict[str, Any]:
        """Improve existing content"""
        if not self.is_available():
            raise Exception("Groq API service is not available.")
        
        improvement_instructions = {
            "enhance": "Enhance this content by making it more engaging, adding more details, and improving the flow while maintaining the original meaning.",
            "simplify": "Simplify this content to make it more accessible and easier to understand while keeping the key information.",
            "professional": "Make this content more professional and polished while maintaining its core message.",
            "expand": "Expand this content with additional details, examples, and insights to make it more comprehensive."
        }
        
        try:
            system_message = f"""You are an expert content editor. Your task is to improve the provided content.

Instruction: {improvement_instructions.get(improvement_type, improvement_instructions['enhance'])}

Guidelines:
- Maintain the original intent and key information
- Improve readability and engagement
- Use proper markdown formatting
- Ensure the content flows naturally
- Keep the same general length unless expanding"""
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Please improve this content:\n\n{content}"}
                ],
                max_tokens=2048,
                temperature=0.5
            )
            
            improved_content = response.choices[0].message.content
            
            return {
                "success": True,
                "content": improved_content,
                "improvement_type": improvement_type
            }
            
        except Exception as e:
            logger.error(f"Error improving content with Groq: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": content
            }

# Global service instance
groq_service = GroqAIService()