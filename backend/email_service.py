import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
APP_URL = os.getenv("APP_URL", "http://localhost:3000")

def send_email(to_email: str, subject: str, html_content: str):
    """Send email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM_EMAIL
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def send_verification_email(to_email: str, full_name: str, verification_token: str):
    """Send email verification"""
    verification_link = f"{APP_URL}/verify-email?token={verification_token}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 20px; }
            .logo { color: #7c3aed; font-size: 24px; font-weight: bold; }
            .content { margin: 20px 0; }
            .button { display: inline-block; background-color: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">MarketMindAI</div>
            </div>
            <div class="content">
                <h2>Welcome to MarketMindAI!</h2>
                <p>Hi {{ full_name }},</p>
                <p>Thank you for registering with MarketMindAI. Please click the button below to verify your email address:</p>
                <a href="{{ verification_link }}" class="button">Verify Email</a>
                <p>If you didn't create an account, please ignore this email.</p>
                <p>This link will expire in 24 hours.</p>
            </div>
            <div class="footer">
                <p>© 2024 MarketMindAI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(full_name=full_name, verification_link=verification_link)
    
    return send_email(to_email, "Verify Your Email - MarketMindAI", html_content)

def send_password_reset_email(to_email: str, full_name: str, reset_token: str):
    """Send password reset email"""
    reset_link = f"{APP_URL}/reset-password?token={reset_token}"
    
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 20px; }
            .logo { color: #7c3aed; font-size: 24px; font-weight: bold; }
            .content { margin: 20px 0; }
            .button { display: inline-block; background-color: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">MarketMindAI</div>
            </div>
            <div class="content">
                <h2>Password Reset Request</h2>
                <p>Hi {{ full_name }},</p>
                <p>You requested to reset your password. Please click the button below to reset your password:</p>
                <a href="{{ reset_link }}" class="button">Reset Password</a>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>This link will expire in 1 hour.</p>
            </div>
            <div class="footer">
                <p>© 2024 MarketMindAI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(full_name=full_name, reset_link=reset_link)
    
    return send_email(to_email, "Password Reset - MarketMindAI", html_content)

def send_welcome_email(to_email: str, full_name: str):
    """Send welcome email after successful verification"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 20px; }
            .logo { color: #7c3aed; font-size: 24px; font-weight: bold; }
            .content { margin: 20px 0; }
            .button { display: inline-block; background-color: #7c3aed; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">MarketMindAI</div>
            </div>
            <div class="content">
                <h2>Welcome to MarketMindAI!</h2>
                <p>Hi {{ full_name }},</p>
                <p>Your email has been successfully verified! You can now access all features of MarketMindAI.</p>
                <p>Start exploring the best B2B tools and create amazing content.</p>
                <a href="{{ app_url }}" class="button">Get Started</a>
            </div>
            <div class="footer">
                <p>© 2024 MarketMindAI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(full_name=full_name, app_url=APP_URL)
    
    return send_email(to_email, "Welcome to MarketMindAI!", html_content)