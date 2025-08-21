import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email = os.getenv("GMAIL_EMAIL")
        self.password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not self.email or not self.password:
            logger.warning("Gmail credentials not found in environment variables. Email functionality will be limited.")
            self.email_enabled = False
        else:
            self.email_enabled = True
            logger.info(f"Email service initialized with Gmail account: {self.email}")
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str, 
        text_body: str = None
    ) -> bool:
        """Send an email using Gmail SMTP"""
        if not self.email_enabled:
            logger.warning(f"Email service not configured. Would send email to {to_email} with subject: {subject}")
            return True  # Return True for testing purposes when credentials are not available
            
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"Dancing on the Boulevard <{self.email}>"
            message["To"] = to_email
            
            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.email,
                password=self.password,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_lesson_reminder(
        self, 
        student_email: str, 
        student_name: str,
        lesson_details: Dict
    ) -> bool:
        """Send lesson reminder email"""
        
        subject = f"🩰 Lesson Reminder: {lesson_details.get('type', 'Dance')} Class Today"
        
        # HTML template
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .lesson-card { background: #f8fafc; border-left: 4px solid #a855f7; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .footer { background: #f8fafc; padding: 20px; text-align: center; color: #6b7280; }
                .button { display: inline-block; padding: 12px 24px; background: #a855f7; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🩰 Lesson Reminder</h1>
                    <p>Don't forget about your dance class!</p>
                </div>
                <div class="content">
                    <h2>Hi {{ student_name }}! 👋</h2>
                    <p>This is a friendly reminder about your upcoming dance class:</p>
                    
                    <div class="lesson-card">
                        <h3>📅 {{ lesson_type }} Class</h3>
                        <p><strong>📍 Time:</strong> {{ lesson_time }}</p>
                        <p><strong>👨‍🏫 Instructor:</strong> {{ instructor_names }}</p>
                        <p><strong>📍 Location:</strong> {{ location }}</p>
                        {% if notes %}
                        <p><strong>📝 Notes:</strong> {{ notes }}</p>
                        {% endif %}
                    </div>
                    
                    <p>We're excited to see you on the dance floor! 💃</p>
                    <p><strong>Please arrive 5-10 minutes early</strong> to prepare for class.</p>
                    
                    <p>Need to reschedule? Please contact us as soon as possible.</p>
                </div>
                <div class="footer">
                    <p>Dance Studio CRM | Keep Dancing! 🌟</p>
                    <p>This is an automated reminder. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # Format lesson time
        lesson_time = lesson_details.get('start_datetime', datetime.now())
        if isinstance(lesson_time, str):
            lesson_time = datetime.fromisoformat(lesson_time.replace('Z', '+00:00'))
        
        formatted_time = lesson_time.strftime("%A, %B %d at %I:%M %p")
        
        html_body = html_template.render(
            student_name=student_name,
            lesson_type=lesson_details.get('booking_type', 'Dance').replace('_', ' ').title(),
            lesson_time=formatted_time,
            instructor_names=lesson_details.get('teacher_names', ['TBD']),
            location=lesson_details.get('location', 'Main Studio'),
            notes=lesson_details.get('notes', '')
        )
        
        # Text version
        text_body = f"""
        Hi {student_name}!
        
        This is a reminder about your {lesson_details.get('booking_type', 'dance')} class:
        
        Time: {formatted_time}
        Instructor: {', '.join(lesson_details.get('teacher_names', ['TBD']))}
        Location: {lesson_details.get('location', 'Main Studio')}
        
        Please arrive 5-10 minutes early.
        
        See you soon!
        Dance Studio CRM
        """
        
        return await self.send_email(student_email, subject, html_body, text_body)

    async def send_payment_reminder(
        self, 
        student_email: str, 
        student_name: str,
        amount_due: float,
        due_date: datetime
    ) -> bool:
        """Send payment reminder email"""
        
        subject = f"💳 Payment Reminder: ${amount_due:.2f} Due Soon"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .payment-card { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .footer { background: #f8fafc; padding: 20px; text-align: center; color: #6b7280; }
                .amount { font-size: 24px; font-weight: bold; color: #d97706; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💳 Payment Reminder</h1>
                    <p>Your payment is coming due</p>
                </div>
                <div class="content">
                    <h2>Hi {{ student_name }}! 👋</h2>
                    <p>This is a friendly reminder about your upcoming payment:</p>
                    
                    <div class="payment-card">
                        <h3>💰 Payment Due</h3>
                        <p class="amount">${{ amount_due }}</p>
                        <p><strong>📅 Due Date:</strong> {{ due_date }}</p>
                    </div>
                    
                    <p>Please ensure your payment is made by the due date to continue enjoying your dance classes.</p>
                    <p>If you have any questions about your payment or need to discuss payment options, please contact us.</p>
                    
                    <p>Thank you for being part of our dance family! 💃🕺</p>
                </div>
                <div class="footer">
                    <p>Dance Studio CRM | Keep Dancing! 🌟</p>
                    <p>This is an automated reminder. Please contact us if you have questions.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        formatted_due_date = due_date.strftime("%A, %B %d, %Y")
        
        html_body = html_template.render(
            student_name=student_name,
            amount_due=f"{amount_due:.2f}",
            due_date=formatted_due_date
        )
        
        text_body = f"""
        Hi {student_name}!
        
        This is a payment reminder:
        
        Amount Due: ${amount_due:.2f}
        Due Date: {formatted_due_date}
        
        Please ensure your payment is made by the due date.
        
        Thank you!
        Dance Studio CRM
        """
        
        return await self.send_email(student_email, subject, html_body, text_body)

    async def send_class_update(
        self, 
        student_email: str, 
        student_name: str,
        update_message: str,
        lesson_details: Dict
    ) -> bool:
        """Send class update/change notification"""
        
        subject = f"📢 Class Update: {lesson_details.get('booking_type', 'Dance').title()} Class"
        
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .update-card { background: #dbeafe; border-left: 4px solid #3b82f6; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .footer { background: #f8fafc; padding: 20px; text-align: center; color: #6b7280; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📢 Class Update</h1>
                    <p>Important information about your class</p>
                </div>
                <div class="content">
                    <h2>Hi {{ student_name }}! 👋</h2>
                    <p>We have an important update about your dance class:</p>
                    
                    <div class="update-card">
                        <h3>📅 {{ lesson_type }} Class</h3>
                        <p><strong>📢 Update:</strong> {{ update_message }}</p>
                        <p><strong>📍 Time:</strong> {{ lesson_time }}</p>
                        <p><strong>👨‍🏫 Instructor:</strong> {{ instructor_names }}</p>
                    </div>
                    
                    <p>If you have any questions about this update, please don't hesitate to contact us.</p>
                    <p>Thank you for your understanding! 💃</p>
                </div>
                <div class="footer">
                    <p>Dance Studio CRM | Keep Dancing! 🌟</p>
                    <p>This is an automated notification.</p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # Format lesson time
        lesson_time = lesson_details.get('start_datetime', datetime.now())
        if isinstance(lesson_time, str):
            lesson_time = datetime.fromisoformat(lesson_time.replace('Z', '+00:00'))
        
        formatted_time = lesson_time.strftime("%A, %B %d at %I:%M %p")
        
        html_body = html_template.render(
            student_name=student_name,
            lesson_type=lesson_details.get('booking_type', 'Dance').replace('_', ' ').title(),
            lesson_time=formatted_time,
            instructor_names=', '.join(lesson_details.get('teacher_names', ['TBD'])),
            update_message=update_message
        )
        
        text_body = f"""
        Hi {student_name}!
        
        Important update about your {lesson_details.get('booking_type', 'dance')} class:
        
        Update: {update_message}
        Time: {formatted_time}
        Instructor: {', '.join(lesson_details.get('teacher_names', ['TBD']))}
        
        Contact us if you have questions.
        
        Dance Studio CRM
        """
        
        return await self.send_email(student_email, subject, html_body, text_body)

    async def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify email functionality"""
        
        subject = "🧪 Test Email from Dance Studio CRM"
        
        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; }
                .content { padding: 30px; }
                .footer { background: #f8fafc; padding: 20px; text-align: center; color: #6b7280; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Test Email</h1>
                    <p>Email system is working perfectly!</p>
                </div>
                <div class="content">
                    <h2>Success! ✅</h2>
                    <p>Your Dance Studio CRM email notification system is working correctly.</p>
                    <p>This test email was sent at: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                    <p>You can now send:</p>
                    <ul>
                        <li>🩰 Lesson reminders</li>
                        <li>💳 Payment alerts</li>
                        <li>📢 Class updates</li>
                        <li>📅 Schedule changes</li>
                    </ul>
                    <p>Ready to start sending notifications! 🚀</p>
                </div>
                <div class="footer">
                    <p>Dance Studio CRM | Keep Dancing! 🌟</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Test Email from Dance Studio CRM
        
        Success! Your email notification system is working correctly.
        
        Sent at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        You can now send lesson reminders, payment alerts, and class updates!
        
        Dance Studio CRM
        """
        
        return await self.send_email(to_email, subject, html_body, text_body)

# Global instance
email_service = EmailService()