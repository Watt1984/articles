import requests
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# Variables d'environnement (définies par le serveur)
OS_NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
OS_OPENAI_KEY = os.environ.get("OPENAI_KEY")
OS_GMAIL_USER = os.environ.get("GMAIL_USER")
OS_GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

# Vérification des variables d'environnement
def check_environment():
    required_vars = ["NEWSAPI_KEY", "OPENAI_KEY", "GMAIL_USER", "GMAIL_PASSWORD"]
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables d'environnement manquantes : {', '.join(missing_vars)}")
        return False
    
    print("✅ Toutes les variables d'environnement sont configurées")
    return True

# 1. Récupérer les articles d'actualité sur l'IA (version anglaise)
def fetch_ai_articles_en(api_key, query="artificial intelligence", page_size=8):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "pageSize": page_size,
        "sortBy": "publishedAt",  # Articles les plus récents
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])
    
    # Ajouter la langue à chaque article
    for article in articles:
        article['language'] = 'en'
    
    return articles

# 2. Résumer un article en anglais (version améliorée)
def summarize_text_en(text, openai_api_key, title="", url=""):
    # Vérifier si le texte est valide
    if not text or text.strip() == "" or len(text.strip()) < 10:
        return "Article content not available"
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Prompt en anglais pour les articles anglais
    prompt = f"""Summarize this article in 2-3 sentences maximum. 
    
Article title: {title}
URL: {url}

Content to summarize:
{text}

Summary:"""
    
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
            return "Summary not available"
    except Exception as e:
        print(f"Error during summarization: {e}")
        return "Error generating summary"

# 3. Vérifier la qualité d'un article
def validate_article(article):
    """Vérifie si un article a un contenu valide"""
    title = article.get('title', '') or ''
    description = article.get('description', '') or ''
    content = article.get('content', '') or ''
    url = article.get('url', '') or ''
    
    # Nettoyer les chaînes
    title = title.strip()
    description = description.strip()
    content = content.strip()
    url = url.strip()
    
    # Vérifier que l'article a au moins un titre et une URL
    if not title or not url:
        return False
    
    # Vérifier qu'il y a du contenu à résumer
    if not description and not content:
        return False
    
    return True

# 4. Générer le contenu de l'e-mail (version anglaise)
def create_email_content_en(articles, summaries):
    content = "<h2>Latest AI News - English Articles</h2><ul>"
    for article, summary in zip(articles, summaries):
        content += f"<li><a href='{article['url']}'>{article['title']}</a><br>{summary}</li><br>"
    content += "</ul>"
    return content

# 5. Envoyer l'e-mail
def send_email(subject, html_content, sender, recipient, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(sender, recipient, msg.as_string())

# 6. Orchestration (version anglaise)
def main():
    print("🚀 Starting English AI newsletter script...")
    
    # Vérifier l'environnement
    if not check_environment():
        return
    
    NEWSAPI_KEY = OS_NEWSAPI_KEY
    OPENAI_KEY = OS_OPENAI_KEY
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    SMTP_USER = OS_GMAIL_USER
    SMTP_PASSWORD = OS_GMAIL_PASSWORD
    SENDER = SMTP_USER
    RECIPIENT = "benoit.v1cent@gmail.com"

    try:
        # Récupérer les articles en anglais
        print("📰 Fetching English articles...")
        articles = fetch_ai_articles_en(NEWSAPI_KEY)
        print(f"✅ Retrieved {len(articles)} English articles")
        
        # Filtrer les articles valides
        valid_articles = [article for article in articles if validate_article(article)]
        print(f"✅ {len(valid_articles)} valid articles after filtering")
        
        if not valid_articles:
            print("❌ No valid articles found")
            return
        
        summaries = []
        for i, article in enumerate(valid_articles):
            print(f"📝 Summarizing article {i+1}/{len(valid_articles)}...")
            print(f"   Title: {article['title']}")
            
            # Utiliser description ou content, selon ce qui est disponible
            content = article.get('description', '') or article.get('content', '')
            summary = summarize_text_en(content, OPENAI_KEY, article['title'], article['url'])
            summaries.append(summary)
            print(f"   Summary: {summary[:100]}...")
        
        email_content = create_email_content_en(valid_articles, summaries)
        print("📧 Email content generated")
        
        # Envoyer l'email
        send_email("Daily AI News - English", email_content, SENDER, RECIPIENT, SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
        print("✅ Email sent successfully!")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        raise

if __name__ == "__main__":
    main() 