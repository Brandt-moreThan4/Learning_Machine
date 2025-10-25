import os
import smtplib, ssl
from email.mime.text import MIMEText
from pathlib import Path

import os, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# from quiz_create import models




def send_email(subject: str, html_body: str, to_email: str = "brandtgreen97@gmail.com"):
    from_email = os.getenv("SMTP_USER")
    msg = MIMEMultipart("alternative")  # allows text + HTML
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    # 1) Plain-text fallback (optional but recommended)
    # If you don’t have a text version, you can keep it minimal:
    text_fallback = "Your email client does not support HTML. Please open this message in a modern client."

    # 2) Attach parts (order matters: plain first, then HTML)
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        server.login(from_email, os.getenv("SMTP_PASS"))
        server.sendmail(from_email, [to_email], msg.as_string())



if __name__ == "__main__":

    file = r'C:\Users\BrandtGreen\Desktop\Code\Learning_Machine\data\quizzes\quiz_html\Money_Stuff__2025-10-23__Money_Stuff_The_FBI_Found_Some_Insider_Betting__19a1254f13936902_quiz.html'
    with open(file, "r", encoding="utf-8") as f:
        quiz_content = f.read()
    
    send_email(subject="First Quiz Sending Test!", html_body=quiz_content)

    print('Emails sent!')