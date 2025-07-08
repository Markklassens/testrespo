import requests
import json
import uuid

# Sample tools data
sample_tools = [
    {
        "name": "Slack",
        "description": "Business communication and collaboration platform with channels, direct messaging, and integrations.",
        "short_description": "Team communication and collaboration tool",
        "website_url": "https://slack.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan available, paid plans start at $7.25/month per user",
        "features": '["Real-time messaging", "File sharing", "Video calls", "App integrations", "Search functionality"]',
        "target_audience": "Teams and Organizations",
        "company_size": "All",
        "integrations": '["Google Drive", "Zoom", "Trello", "GitHub", "Salesforce"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-1000+",
        "revenue_range": "1M-100M",
        "location": "San Francisco, USA",
        "is_hot": True,
        "is_featured": True,
        "slug": "slack"
    },
    {
        "name": "Zoom",
        "description": "Video conferencing and communication platform for remote meetings, webinars, and collaboration.",
        "short_description": "Video conferencing platform",
        "website_url": "https://zoom.us",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan for up to 40 minutes, paid plans start at $14.99/month",
        "features": '["HD video calls", "Screen sharing", "Recording", "Breakout rooms", "Webinars"]',
        "target_audience": "Businesses and Education",
        "company_size": "SMB",
        "integrations": '["Slack", "Microsoft Teams", "Google Calendar", "Outlook", "Salesforce"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "11-500",
        "revenue_range": "10M-100M",
        "location": "San Jose, USA",
        "is_hot": True,
        "is_featured": False,
        "slug": "zoom"
    },
    {
        "name": "Salesforce CRM",
        "description": "Complete CRM solution for enterprise businesses with sales automation, marketing tools, and customer service.",
        "short_description": "Enterprise CRM platform",
        "website_url": "https://salesforce.com",
        "pricing_model": "Paid",
        "pricing_details": "Plans start at $25/month per user",
        "features": '["Sales automation", "Lead management", "Customer analytics", "Marketing automation", "Mobile app"]',
        "target_audience": "Sales Teams",
        "company_size": "Enterprise",
        "integrations": '["Slack", "Microsoft Office", "Mailchimp", "DocuSign", "Zoom"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "500+",
        "revenue_range": "100M+",
        "location": "San Francisco, USA",
        "is_hot": False,
        "is_featured": True,
        "slug": "salesforce-crm"
    },
    {
        "name": "HubSpot",
        "description": "Comprehensive marketing, sales, and customer service platform for growing businesses.",
        "short_description": "All-in-one marketing platform",
        "website_url": "https://hubspot.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free tools available, paid plans start at $45/month",
        "features": '["Email marketing", "CRM", "Landing pages", "Analytics", "Live chat"]',
        "target_audience": "Marketing Teams",
        "company_size": "SMB",
        "integrations": '["Salesforce", "WordPress", "Shopify", "Zoom", "Slack"]',
        "category_id": "1",
        "industry": "Marketing",
        "employee_size": "11-200",
        "revenue_range": "1M-10M",
        "location": "Cambridge, USA",
        "is_hot": False,
        "is_featured": True,
        "slug": "hubspot"
    },
    {
        "name": "Asana",
        "description": "Project management and team collaboration software for organizing work and tracking progress.",
        "short_description": "Project management tool",
        "website_url": "https://asana.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free for teams up to 15 members, paid plans start at $10.99/month",
        "features": '["Task management", "Project tracking", "Team collaboration", "Timeline view", "Reporting"]',
        "target_audience": "Project Managers",
        "company_size": "SMB",
        "integrations": '["Slack", "Google Drive", "Adobe Creative Cloud", "Zoom", "Microsoft Teams"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-200",
        "revenue_range": "<1M",
        "location": "San Francisco, USA",
        "is_hot": True,
        "is_featured": False,
        "slug": "asana"
    },
    {
        "name": "Trello",
        "description": "Visual project management tool using boards, lists, and cards for organizing tasks and workflows.",
        "short_description": "Visual project management",
        "website_url": "https://trello.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan available, paid plans start at $5/month per user",
        "features": '["Kanban boards", "Card-based organization", "Team collaboration", "Power-ups", "Mobile app"]',
        "target_audience": "Small Teams",
        "company_size": "Startup",
        "integrations": '["Slack", "Google Drive", "Dropbox", "GitHub", "Jira"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-50",
        "revenue_range": "<1M",
        "location": "New York, USA",
        "is_hot": False,
        "is_featured": False,
        "slug": "trello"
    },
    {
        "name": "Microsoft Teams",
        "description": "Collaboration platform combining workplace chat, meetings, files, and app integration.",
        "short_description": "Microsoft collaboration platform",
        "website_url": "https://teams.microsoft.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free version available, paid plans start at $4/month per user",
        "features": '["Team chat", "Video meetings", "File collaboration", "App integration", "Phone system"]',
        "target_audience": "Enterprise Teams",
        "company_size": "Enterprise",
        "integrations": '["Microsoft Office", "SharePoint", "OneDrive", "Power BI", "Outlook"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "200+",
        "revenue_range": "10M+",
        "location": "Redmond, USA",
        "is_hot": True,
        "is_featured": True,
        "slug": "microsoft-teams"
    },
    {
        "name": "Notion",
        "description": "All-in-one workspace for notes, tasks, wikis, and databases with powerful organization features.",
        "short_description": "All-in-one workspace",
        "website_url": "https://notion.so",
        "pricing_model": "Freemium",
        "pricing_details": "Free for personal use, team plans start at $8/month per user",
        "features": '["Notes and documentation", "Task management", "Databases", "Templates", "Collaboration"]',
        "target_audience": "Knowledge Workers",
        "company_size": "SMB",
        "integrations": '["Slack", "Google Drive", "Figma", "GitHub", "Zapier"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-100",
        "revenue_range": "1M-10M",
        "location": "San Francisco, USA",
        "is_hot": True,
        "is_featured": False,
        "slug": "notion"
    },
    {
        "name": "Figma",
        "description": "Collaborative design tool for creating user interfaces, prototypes, and design systems.",
        "short_description": "Collaborative design tool",
        "website_url": "https://figma.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free for personal use, professional plans start at $12/month per user",
        "features": '["Design collaboration", "Prototyping", "Design systems", "Real-time editing", "Developer handoff"]',
        "target_audience": "Designers and Developers",
        "company_size": "All",
        "integrations": '["Slack", "Jira", "Notion", "Zapier", "Adobe Creative Cloud"]',
        "category_id": "1",
        "industry": "Design",
        "employee_size": "1-500",
        "revenue_range": "1M-100M",
        "location": "San Francisco, USA",
        "is_hot": True,
        "is_featured": True,
        "slug": "figma"
    },
    {
        "name": "Monday.com",
        "description": "Work management platform for teams to plan, organize, and track work across projects.",
        "short_description": "Work management platform",
        "website_url": "https://monday.com",
        "pricing_model": "Paid",
        "pricing_details": "Plans start at $8/month per user",
        "features": '["Project management", "Workflow automation", "Time tracking", "Team collaboration", "Reporting"]',
        "target_audience": "Project Teams",
        "company_size": "SMB",
        "integrations": '["Slack", "Microsoft Teams", "Google Drive", "Zoom", "Salesforce"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "11-200",
        "revenue_range": "1M-10M",
        "location": "Tel Aviv, Israel",
        "is_hot": False,
        "is_featured": False,
        "slug": "monday-com"
    },
    {
        "name": "Canva",
        "description": "Online design platform for creating graphics, presentations, social media content, and marketing materials.",
        "short_description": "Online design platform",
        "website_url": "https://canva.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan available, Pro plans start at $12.99/month",
        "features": '["Drag-and-drop design", "Templates", "Stock photos", "Brand kit", "Team collaboration"]',
        "target_audience": "Marketers and Creators",
        "company_size": "All",
        "integrations": '["Slack", "Google Drive", "Dropbox", "Mailchimp", "HubSpot"]',
        "category_id": "1",
        "industry": "Design",
        "employee_size": "1-1000+",
        "revenue_range": "100M+",
        "location": "Sydney, Australia",
        "is_hot": True,
        "is_featured": True,
        "slug": "canva"
    },
    {
        "name": "Airtable",
        "description": "Cloud collaboration service that combines the simplicity of a spreadsheet with the power of a database.",
        "short_description": "Database-spreadsheet hybrid",
        "website_url": "https://airtable.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan available, paid plans start at $20/month per user",
        "features": '["Database functionality", "Spreadsheet interface", "Automation", "Forms", "API access"]',
        "target_audience": "Data Teams",
        "company_size": "SMB",
        "integrations": '["Slack", "Google Calendar", "Mailchimp", "Zapier", "Figma"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-200",
        "revenue_range": "1M-100M",
        "location": "San Francisco, USA",
        "is_hot": False,
        "is_featured": False,
        "slug": "airtable"
    },
    {
        "name": "Shopify",
        "description": "E-commerce platform for building online stores with payment processing, inventory management, and marketing tools.",
        "short_description": "E-commerce platform",
        "website_url": "https://shopify.com",
        "pricing_model": "Paid",
        "pricing_details": "Plans start at $29/month",
        "features": '["Online store builder", "Payment processing", "Inventory management", "Marketing tools", "Analytics"]',
        "target_audience": "E-commerce Businesses",
        "company_size": "SMB",
        "integrations": '["Facebook", "Google Ads", "Mailchimp", "QuickBooks", "Slack"]',
        "category_id": "1",
        "industry": "Retail",
        "employee_size": "1-200",
        "revenue_range": "1M-100M",
        "location": "Ottawa, Canada",
        "is_hot": True,
        "is_featured": True,
        "slug": "shopify"
    },
    {
        "name": "Zapier",
        "description": "Automation platform that connects different apps and services to automate workflows without coding.",
        "short_description": "Workflow automation platform",
        "website_url": "https://zapier.com",
        "pricing_model": "Freemium",
        "pricing_details": "Free plan available, paid plans start at $19.99/month",
        "features": '["App integrations", "Workflow automation", "Triggers and actions", "Multi-step workflows", "Data formatting"]',
        "target_audience": "Automation Enthusiasts",
        "company_size": "All",
        "integrations": '["Gmail", "Slack", "Trello", "Salesforce", "Google Sheets"]',
        "category_id": "1",
        "industry": "Technology",
        "employee_size": "1-1000+",
        "revenue_range": "10M-100M",
        "location": "San Francisco, USA",
        "is_hot": False,
        "is_featured": False,
        "slug": "zapier"
    },
    {
        "name": "Adobe Creative Cloud",
        "description": "Suite of creative applications including Photoshop, Illustrator, Premiere Pro, and more for professional design.",
        "short_description": "Creative software suite",
        "website_url": "https://adobe.com/creativecloud",
        "pricing_model": "Paid",
        "pricing_details": "Plans start at $20.99/month per app or $52.99/month for all apps",
        "features": '["Photoshop", "Illustrator", "Premiere Pro", "After Effects", "InDesign", "Cloud storage"]',
        "target_audience": "Creative Professionals",
        "company_size": "All",
        "integrations": '["Behance", "Slack", "Microsoft Teams", "Dropbox", "Google Drive"]',
        "category_id": "1",
        "industry": "Design",
        "employee_size": "1-1000+",
        "revenue_range": "100M+",
        "location": "San Jose, USA",
        "is_hot": False,
        "is_featured": True,
        "slug": "adobe-creative-cloud"
    }
]

def add_sample_tools():
    base_url = "http://localhost:8001"
    
    # Login as admin to get access token
    login_data = {
        "email": "admin@marketmindai.com",
        "password": "admin123"
    }
    
    try:
        # Login to get token
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            print("Successfully logged in as admin")
            
            # Add each sample tool
            for tool in sample_tools:
                tool["id"] = str(uuid.uuid4())
                
                response = requests.post(f"{base_url}/api/tools", json=tool, headers=headers)
                if response.status_code == 200:
                    print(f"✅ Added tool: {tool['name']}")
                else:
                    print(f"❌ Failed to add tool: {tool['name']} - {response.status_code}")
                    if response.status_code == 422:
                        print(f"Error details: {response.json()}")
        else:
            print(f"Failed to login: {login_response.status_code}")
            print(login_response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_sample_tools()