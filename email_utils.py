import smtplib
from email.mime.text import MIMEText

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USER = "sakshiitnare92@gmail.com"
EMAIL_PASSWORD = "apkk xysr bsvr htdm"   # Gmail App Password

def send_wallet_email(to_email, amount, score, subject_name):
    message = f"""
Hello,

Your quiz attempt for subject: {subject_name}

Score: {score}
Wallet Amount Added: ₹{amount}

Thank you for using QuizPay!
"""

    msg = MIMEText(message)
    msg["Subject"] = "QuizPay – Wallet Amount Added"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Email sending failed:", e)
