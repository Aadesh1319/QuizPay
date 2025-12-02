import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_utils import EMAIL_HOST, EMAIL_PORT, EMAIL_ADDRESS, EMAIL_PASSWORD

def send_quiz_email(to_email, username, amount, score, total):
    try:
        subject = "QuizPay – Wallet Update & Quiz Result"
        
        body = f"""
Hello {username},

🎉 Your quiz attempt has been successfully recorded!

💰 Amount Added to Wallet: ₹{amount}
📊 Your Quiz Result: {score}/{total}

Thank you for using QuizPay!

Regards,
QuizPay Team
"""

        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()

        print("Email sent successfully")
    except Exception as e:
        print("Email Error:", str(e))
