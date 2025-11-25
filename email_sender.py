import os
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Assuming models is defined in quiz_create.models
from quiz_create import models 



SUBSCRIBER_LIST = "brandtgreen97@gmail.com;yunqingli1998@gmail.com"

# This list is what server.sendmail() requires.
RECIPIENTS = [r.strip() for r in SUBSCRIBER_LIST.split(';')]


def send_email(subject: str, html_body: str, to_emails: list[str]):
    """
    Sends an email to a list of recipients.

    Args:
        subject: The email subject line.
        html_body: The HTML content of the email.
        to_emails: A list of email addresses to send the email to.
    """
    from_email = os.getenv("SMTP_USER")
    
    # Create the top-level container (MIMEMultipart)
    msg = MIMEMultipart("alternative")  # allows text + HTML
    msg["Subject"] = subject
    msg["From"] = from_email
    
    # 3. FIX: Set the 'To' header to a comma-separated string for display 
    # in the email client.
    msg["To"] = ", ".join(to_emails)

    # 1) Plain-text fallback (optional but recommended)
    text_fallback = "Your email client does not support HTML. Please open this message in a modern client."

    # 2) Attach parts (order matters: plain first, then HTML)
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Connect and send
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls(context=context)
        server.login(from_email, os.getenv("SMTP_PASS"))
        

        server.sendmail(from_email, to_emails, msg.as_string())


def send_new_quiz_emails(max_emails_to_send:int=5):

    # Query the database for quizzes that have not been emailed yet
    not_sent_quizzes = models.Quiz.get_unsent_quizzes_from_db()

    # Send them
    emails_sent = 0
    for quiz in not_sent_quizzes:
        if emails_sent >= max_emails_to_send:
            break
        
        # Pass the pre-processed list of recipients
        send_email(
            subject=f"New Quiz Available: {quiz.source.subject}",
            html_body=quiz.as_html(),
            to_emails=RECIPIENTS # <--- CHANGE HERE
        )
        emails_sent += 1
        # If email sent successfully, mark quiz as emailed in DB
        quiz.mark_as_emailed_in_db()


if __name__ == "__main__":

    # The commented out block is preserved from your original code
    # try:
    #     import json
    #     from pathlib import Path
    #     
    #     # file = r'C:\Users\BrandtGreen\Desktop\Code\Learning_Machine\data\quizzes\quiz_html\Money_Stuff__2025-10-23__Money_Stuff_The_FBI_Found_Some_Insider_Betting__19a1254f13936902_quiz.html'
    #     # json_file = r'C:\Users\BrandtGreen\Desktop\Code\Learning_Machine\data\quizzes\quiz_json\Money_Stuff__2025-10-23__Money_Stuff_The_FBI_Found_Some_Insider_Betting__19a1254f13936902_quiz.json'
    #     # with open(json_file, "r", encoding="utf-8") as f:
    #     #     quiz_data = json.load(f)
    #     # quiz = models.Quiz.from_cleaned_json(quiz_data)
    #     # with open(file, "r", encoding="utf-8") as f:
    #     #     quiz_content = f.read()
    #     # send_email(subject="First Quiz Sending Test!", html_body=quiz.as_html())
    # except ImportError:
    #     # Only call this if you can't load the necessary files/modules
    #     pass

    send_new_quiz_emails()

    print('Emails sent!')