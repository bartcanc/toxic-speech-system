import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv


load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")

if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("[SYSTEM] Brak danych logowania w pliku .env!")
    raise RuntimeError("Brak konfiguracji e-mail!")
    
def send_reset_email(receiver_email: str, reset_code: str):
    """Wysyła e-mail z kodem resetowania hasła."""
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = "SafeSound - prośba o zmianę hasła"
    
    # Treść wiadomości
    body = f"""
    <html>
        <body>
            <h2>Witaj!</h2>
            <p>Otrzymaliśmy prośbę o zmianę hasła do Twojego konta.</p>
            <p>Twój kod weryfikacyjny to: <b>{reset_code}</b></p>
            <p><i>Kod jest ważny przez 15 minut. Jeśli to nie ty poprosiłeś/aś o zmianę hasła, zignoruj tę wiadomość.</i></p>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        print(f"E-mail wysłany do {receiver_email}")
        
    except Exception as e:
        print(f"Błąd podczas wysyłania e-maila: {e}")
        
    finally:
        server.quit()

if __name__ == "__main__":
    send_reset_email("bartekr2002@gmail.com", "X7B9A2")