import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Add the parent directory to the path to import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, Category, Subcategory, Tool, Blog
from auth import get_password_hash
from database import DATABASE_URL

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_data():
    db = SessionLocal()
    
    try:
        print("Creating seed data...")
        
        # Create test users with different roles
        users_data = [
            {
                'id': str(uuid.uuid4()),
                'email': 'user@marketmindai.com',
                'username': 'testuser',
                'full_name': 'Test User',
                'hashed_password': get_password_hash('password123'),
                'user_type': 'user',
                'is_active': True,
                'is_verified': True,
                'verification_token': None
            },
            {
                'id': str(uuid.uuid4()),
                'email': 'admin@marketmindai.com',
                'username': 'testadmin',
                'full_name': 'Test Admin',
                'hashed_password': get_password_hash('admin123'),
                'user_type': 'admin',
                'is_active': True,
                'is_verified': True,
                'verification_token': None
            },
            {
                'id': str(uuid.uuid4()),
                'email': 'superadmin@marketmindai.com',
                'username': 'testsuperadmin',
                'full_name': 'Test Super Admin',
                'hashed_password': get_password_hash('superadmin123'),
                'user_type': 'superadmin',
                'is_active': True,
                'is_verified': True,
                'verification_token': None
            }
        ]
        
        for user_data in users_data:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data['email']).first()
            if not existing_user:
                user = User(**user_data)
                db.add(user)
        
        # Create categories
        categories_data = [
            {'id': str(uuid.uuid4()), 'name': 'CRM', 'description': 'Customer Relationship Management tools'},
            {'id': str(uuid.uuid4()), 'name': 'Marketing', 'description': 'Marketing automation and analytics tools'},
            {'id': str(uuid.uuid4()), 'name': 'Communication', 'description': 'Team communication and collaboration tools'},
            {'id': str(uuid.uuid4()), 'name': 'Analytics', 'description': 'Business intelligence and analytics platforms'},
            {'id': str(uuid.uuid4()), 'name': 'HR', 'description': 'Human resources management systems'},
            {'id': str(uuid.uuid4()), 'name': 'Productivity', 'description': 'Productivity and project management tools'}
        ]
        
        category_objects = {}
        for cat_data in categories_data:
            existing_cat = db.query(Category).filter(Category.name == cat_data['name']).first()
            if not existing_cat:
                category = Category(**cat_data)
                db.add(category)
                category_objects[cat_data['name']] = category
            else:
                category_objects[cat_data['name']] = existing_cat
        
        db.commit()
        
        # Create subcategories
        subcategories_data = [
            {'id': str(uuid.uuid4()), 'name': 'Sales CRM', 'description': 'CRM focused on sales processes', 'category_id': category_objects['CRM'].id},
            {'id': str(uuid.uuid4()), 'name': 'Customer Service', 'description': 'CRM for customer support', 'category_id': category_objects['CRM'].id},
            {'id': str(uuid.uuid4()), 'name': 'Email Marketing', 'description': 'Email campaign management', 'category_id': category_objects['Marketing'].id},
            {'id': str(uuid.uuid4()), 'name': 'Social Media', 'description': 'Social media management tools', 'category_id': category_objects['Marketing'].id},
            {'id': str(uuid.uuid4()), 'name': 'Team Chat', 'description': 'Real-time team messaging', 'category_id': category_objects['Communication'].id},
            {'id': str(uuid.uuid4()), 'name': 'Video Conferencing', 'description': 'Video meeting platforms', 'category_id': category_objects['Communication'].id}
        ]
        
        subcategory_objects = {}
        for subcat_data in subcategories_data:
            existing_subcat = db.query(Subcategory).filter(
                Subcategory.name == subcat_data['name'],
                Subcategory.category_id == subcat_data['category_id']
            ).first()
            if not existing_subcat:
                subcategory = Subcategory(**subcat_data)
                db.add(subcategory)
                subcategory_objects[subcat_data['name']] = subcategory
            else:
                subcategory_objects[subcat_data['name']] = existing_subcat
        
        db.commit()
        
        # Create sample tools
        tools_data = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Salesforce CRM',
                'description': 'World\'s #1 CRM platform for sales, service, and marketing. Salesforce helps businesses connect with customers in a whole new way.',
                'short_description': 'Complete CRM solution for enterprise businesses',
                'website_url': 'https://salesforce.com',
                'pricing_model': 'Paid',
                'pricing_details': 'Starting at $25/user/month',
                'features': '["Lead Management", "Sales Pipeline", "Analytics", "Mobile App", "Custom Dashboards"]',
                'target_audience': 'Enterprise',
                'company_size': 'Large',
                'integrations': '["Gmail", "Outlook", "Slack", "Microsoft Teams", "DocuSign"]',
                'rating': 4.5,
                'total_reviews': 1234,
                'views': 5678,
                'trending_score': 95.5,
                'category_id': category_objects['CRM'].id,
                'subcategory_id': subcategory_objects['Sales CRM'].id,
                'slug': 'salesforce-crm',
                'meta_title': 'Salesforce CRM - World\'s #1 CRM Platform',
                'meta_description': 'Discover why Salesforce is the world\'s #1 CRM platform. Complete solution for sales, service, and marketing teams.'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'HubSpot Marketing Hub',
                'description': 'All-in-one marketing software to attract, engage, and delight customers. Grow your business with HubSpot\'s comprehensive marketing platform.',
                'short_description': 'Comprehensive marketing automation platform',
                'website_url': 'https://hubspot.com',
                'pricing_model': 'Freemium',
                'pricing_details': 'Free plan available, paid plans start at $45/month',
                'features': '["Email Marketing", "Social Media", "Landing Pages", "Analytics", "Lead Scoring"]',
                'target_audience': 'SMB',
                'company_size': 'Medium',
                'integrations': '["Salesforce", "Gmail", "WordPress", "Shopify", "Zoom"]',
                'rating': 4.3,
                'total_reviews': 987,
                'views': 3456,
                'trending_score': 88.2,
                'category_id': category_objects['Marketing'].id,
                'subcategory_id': subcategory_objects['Email Marketing'].id,
                'slug': 'hubspot-marketing-hub',
                'meta_title': 'HubSpot Marketing Hub - All-in-One Marketing Software',
                'meta_description': 'Grow your business with HubSpot\'s comprehensive marketing platform. Email marketing, social media, and more.'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Slack',
                'description': 'Team collaboration platform that brings teams together. Slack is where work flows - connect with colleagues, share files, and get work done.',
                'short_description': 'Business communication and collaboration tool',
                'website_url': 'https://slack.com',
                'pricing_model': 'Freemium',
                'pricing_details': 'Free plan available, paid plans start at $6.67/user/month',
                'features': '["Messaging", "File Sharing", "Video Calls", "Integrations", "Workflow Automation"]',
                'target_audience': 'All',
                'company_size': 'All',
                'integrations': '["Google Drive", "Zoom", "Trello", "GitHub", "Salesforce"]',
                'rating': 4.7,
                'total_reviews': 2567,
                'views': 8901,
                'trending_score': 92.8,
                'category_id': category_objects['Communication'].id,
                'subcategory_id': subcategory_objects['Team Chat'].id,
                'slug': 'slack',
                'meta_title': 'Slack - Team Communication Platform',
                'meta_description': 'Transform how your team communicates with Slack. The collaboration hub for work.'
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Zoom',
                'description': 'Video-first communications platform for video meetings, webinars, and phone calls. Connect with anyone, anywhere, on any device.',
                'short_description': 'Video conferencing and communication platform',
                'website_url': 'https://zoom.us',
                'pricing_model': 'Freemium',
                'pricing_details': 'Free plan available, paid plans start at $14.99/month/license',
                'features': '["Video Meetings", "Webinars", "Phone", "Chat", "Whiteboard"]',
                'target_audience': 'All',
                'company_size': 'All',
                'integrations': '["Slack", "Microsoft Teams", "Google Calendar", "Outlook", "Salesforce"]',
                'rating': 4.4,
                'total_reviews': 1876,
                'views': 6543,
                'trending_score': 89.1,
                'category_id': category_objects['Communication'].id,
                'subcategory_id': subcategory_objects['Video Conferencing'].id,
                'slug': 'zoom',
                'meta_title': 'Zoom - Video Communications Platform',
                'meta_description': 'Connect with anyone, anywhere with Zoom. Video meetings, webinars, and phone calls made simple.'
            }
        ]
        
        for tool_data in tools_data:
            existing_tool = db.query(Tool).filter(Tool.slug == tool_data['slug']).first()
            if not existing_tool:
                tool = Tool(**tool_data)
                db.add(tool)
        
        # Get user for blog posts
        admin_user = db.query(User).filter(User.username == 'testadmin').first()
        
        # Create sample blog posts
        blogs_data = [
            {
                'id': str(uuid.uuid4()),
                'title': 'How to Choose the Right CRM for Your Business in 2024',
                'content': '''# How to Choose the Right CRM for Your Business in 2024

Choosing the right Customer Relationship Management (CRM) system is crucial for business growth and customer satisfaction. In 2024, the CRM landscape offers numerous options, each with unique features and benefits.

## Key Factors to Consider

### 1. Business Size and Scale
- **Small businesses**: Look for user-friendly, cost-effective solutions
- **Medium businesses**: Focus on scalability and integration capabilities
- **Large enterprises**: Prioritize customization and advanced analytics

### 2. Core Features
- Contact management
- Sales pipeline tracking
- Marketing automation
- Customer service tools
- Analytics and reporting

### 3. Integration Capabilities
Ensure your CRM can integrate with:
- Email platforms
- Marketing tools
- Accounting software
- E-commerce platforms

## Top CRM Recommendations

### Salesforce
Perfect for large enterprises with complex needs. Offers extensive customization and powerful analytics.

### HubSpot
Great for small to medium businesses. Excellent free tier and user-friendly interface.

### Pipedrive
Ideal for sales-focused teams with its intuitive pipeline management.

## Conclusion

The right CRM depends on your specific business needs, budget, and growth plans. Take advantage of free trials to test different platforms before making a decision.''',
                'excerpt': 'A comprehensive guide to selecting the perfect CRM system for your business needs in 2024.',
                'status': 'published',
                'author_id': admin_user.id if admin_user else users_data[1]['id'],
                'category_id': category_objects['CRM'].id,
                'subcategory_id': subcategory_objects['Sales CRM'].id,
                'views': 1234,
                'likes': 89,
                'reading_time': 8,
                'published_at': datetime.utcnow(),
                'slug': 'how-to-choose-right-crm-2024',
                'meta_title': 'How to Choose the Right CRM for Your Business in 2024',
                'meta_description': 'Complete guide to selecting the perfect CRM system for your business. Compare features, pricing, and find the best solution.'
            },
            {
                'id': str(uuid.uuid4()),
                'title': 'Top 10 Marketing Automation Tools for Small Businesses',
                'content': '''# Top 10 Marketing Automation Tools for Small Businesses

Marketing automation has become essential for small businesses looking to scale their marketing efforts efficiently. Here are the top 10 tools that can help streamline your marketing processes.

## 1. HubSpot Marketing Hub
- **Best for**: All-in-one marketing
- **Pricing**: Free plan available
- **Key features**: Email marketing, social media, landing pages

## 2. Mailchimp
- **Best for**: Email marketing
- **Pricing**: Free up to 2,000 contacts
- **Key features**: Email campaigns, audience segmentation

## 3. ActiveCampaign
- **Best for**: Advanced automation
- **Pricing**: Starting at $9/month
- **Key features**: Email marketing, CRM, sales automation

## 4. ConvertKit
- **Best for**: Content creators
- **Pricing**: Free up to 1,000 subscribers
- **Key features**: Email sequences, landing pages

## 5. Drip
- **Best for**: E-commerce
- **Pricing**: Starting at $19/month
- **Key features**: E-commerce integration, visual automation

## 6. GetResponse
- **Best for**: Complete marketing suite
- **Pricing**: Starting at $15/month
- **Key features**: Email marketing, webinars, landing pages

## 7. Pardot (Salesforce)
- **Best for**: B2B marketing
- **Pricing**: Starting at $1,250/month
- **Key features**: Lead scoring, ROI reporting

## 8. Marketo
- **Best for**: Enterprise marketing
- **Pricing**: Custom pricing
- **Key features**: Lead management, revenue attribution

## 9. Sendinblue
- **Best for**: SMS + Email marketing
- **Pricing**: Free plan available
- **Key features**: Email, SMS, chat

## 10. Autopilot
- **Best for**: Visual marketing journeys
- **Pricing**: Starting at $49/month
- **Key features**: Visual journey builder, multi-channel

## Conclusion

Choose a marketing automation tool that aligns with your business size, budget, and specific needs. Start with a free trial to ensure the platform meets your requirements.''',
                'excerpt': 'Discover the best marketing automation tools for small businesses to scale their marketing efforts effectively.',
                'status': 'published',
                'author_id': admin_user.id if admin_user else users_data[1]['id'],
                'category_id': category_objects['Marketing'].id,
                'subcategory_id': subcategory_objects['Email Marketing'].id,
                'views': 2567,
                'likes': 156,
                'reading_time': 12,
                'published_at': datetime.utcnow(),
                'slug': 'top-10-marketing-automation-tools-small-business',
                'meta_title': 'Top 10 Marketing Automation Tools for Small Businesses',
                'meta_description': 'Compare the best marketing automation tools for small businesses. Find the perfect solution to scale your marketing efforts.'
            }
        ]
        
        for blog_data in blogs_data:
            existing_blog = db.query(Blog).filter(Blog.slug == blog_data['slug']).first()
            if not existing_blog:
                blog = Blog(**blog_data)
                db.add(blog)
        
        db.commit()
        
        print("✅ Seed data created successfully!")
        print("\n🔑 Test User Credentials:")
        print("User Account:")
        print("  Email: user@marketmindai.com")
        print("  Password: password123")
        print("  Role: user")
        print("\nAdmin Account:")
        print("  Email: admin@marketmindai.com")
        print("  Password: admin123")
        print("  Role: admin")
        print("\nSuper Admin Account:")
        print("  Email: superadmin@marketmindai.com")
        print("  Password: superadmin123")
        print("  Role: superadmin")
        
    except Exception as e:
        print(f"❌ Error creating seed data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()