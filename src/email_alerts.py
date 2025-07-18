# src/email_alerts.py
import yagmail
import os

SENDER = "prasunkushwaha02@gmail.com"
RECIPIENTS = ["prasunkushwaha03@gmail.com","harsh.rnhs8055@gmail.com","prachikushwaha26@gmail.com"]  # or a list of emails
SUBJECT = "⚠️ Daily Inventory Shortage Alerts"

def send_email():
    outputs = "outputs"
    alerts_file = os.path.join(outputs, "alerts.csv")
    summary_file = os.path.join(outputs, "summary.html")

    if not os.path.exists(alerts_file):
        print("❌ alerts.csv not found. Run forecast_and_detect.py first.")
        return


    SENDER_EMAIL = "prasunkushwaha02@gmail.com"
    APP_PASSWORD = "ksgb mhbl rpab xwjq"  # Use App Password here

    yag = yagmail.SMTP(SENDER_EMAIL, APP_PASSWORD)
    yag.send(
    to=[RECIPIENTS[0], RECIPIENTS[1],RECIPIENTS[2]],
    subject="Inventory Alert",
    contents="Please check the attached stock alert report.",
    attachments=["outputs/alerts.csv"])

    yag.send(
        to=[RECIPIENTS[0],RECIPIENTS[1],RECIPIENTS[2]],
        subject=SUBJECT,
        contents=[
            "Dear Team,\n\nPlease find attached the latest inventory shortage alerts.\n",
            "📄 See HTML summary below:\n",
            yagmail.inline(summary_file)
        ],
        attachments=[alerts_file]
    )

    print("✅ Email sent to", ", ".join(RECIPIENTS))

if __name__ == "__main__":
    send_email()
