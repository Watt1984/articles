import requests
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
load_dotenv()  # charge les variables du fichier .env

import os
OS_NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
OS_OPENAI_KEY = os.environ.get("OPENAI_KEY")
OS_GMAIL_USER = os.environ.get("GMAIL_USER")
OS_GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

# 1. Récupérer les articles d'actualité sur l'IA
def fetch_ai_articles(api_key, query="artificial intelligence", languages=["fr", "en"], page_size=5):
    all_articles = []
    for language in languages:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "apiKey": api_key
        }
        response = requests.get(url, params=params)
        articles = response.json().get("articles", [])
        # Ajouter la langue à chaque article pour les identifier
        for article in articles:
            article['language'] = language
        all_articles.extend(articles)
    return all_articles

# 2. Résumer un article
def summarize_text(text, openai_api_key, title="", url=""):
    # Vérifier si le texte est valide
    if not text or text.strip() == "" or len(text.strip()) < 10:
        return "Contenu de l'article non disponible"
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Améliorer le prompt avec plus de contexte
    prompt = f"""Résume cet article en 2-3 phrases maximum. 
    
Titre de l'article : {title}
URL : {url}

Contenu à résumer :
{text}

Résumé :"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3,  # Réduire la température pour plus de cohérence
        )
        
        # Vérifier que la réponse n'est pas None avant d'appeler strip()
        if response.choices[0].message.content is not None:
            return response.choices[0].message.content.strip()
        else:
            return "Résumé non disponible"
    except Exception as e:
        print(f"Erreur lors du résumé : {e}")
        return "Erreur lors de la génération du résumé"

# 3. Générer le contenu de l'e-mail
def create_email_content(articles, summaries):
    content = "<h2>Articles récents sur l'IA</h2><ul>"
    for article, summary in zip(articles, summaries):
        content += f"<li><a href='{article['url']}'>{article['title']}</a><br>{summary}</li><br>"
    content += "</ul>"
    return content

# 4. Envoyer l'e-mail
def send_email(subject, html_content, sender, recipient, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(sender, recipient, msg.as_string())

# 5. Orchestration
def main():
    NEWSAPI_KEY = OS_NEWSAPI_KEY
    OPENAI_KEY = OS_OPENAI_KEY
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USER = OS_GMAIL_USER
    SMTP_PASSWORD = OS_GMAIL_PASSWORD
    SENDER = SMTP_USER
    RECIPIENT = "benoit.v1cent@gmail.com"

    articles = fetch_ai_articles(NEWSAPI_KEY)
    print(f"✅ Récupéré {len(articles)} articles")
    
    summaries = []
    for i, article in enumerate(articles):
        print(f"📝 Résumé de l'article {i+1}/{len(articles)}...")
        print(f"   Titre: {article['title']}")
        content = article['description'] or article['content'] or ""
        summary = summarize_text(content, OPENAI_KEY, article['title'], article['url'])
        summaries.append(summary)
    
    email_content = create_email_content(articles, summaries)
    print("📧 Contenu de l'email généré")
    
    # Mode test : afficher le contenu au lieu d'envoyer
    TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
    if TEST_MODE:
        print("\n" + "="*50)
        print("MODE TEST - Contenu de l'email :")
        print("="*50)
        print(email_content)
        print("="*50)
    else:
        send_email("Veille IA quotidienne", email_content, SENDER, RECIPIENT, SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
        print("✅ Email envoyé avec succès !")

if __name__ == "__main__":
    main()