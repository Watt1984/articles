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

# 1. Récupérer les articles d'actualité sur l'IA (version française)
def fetch_ai_articles_fr(api_key, page_size=12):
    url = "https://newsapi.org/v2/everything"
    
    # Requête plus précise pour l'IA avec des termes spécifiques
    query = """("intelligence artificielle" OR "IA" OR "AI" OR "machine learning" OR "apprentissage automatique" OR "deep learning" OR "apprentissage profond" OR "GPT" OR "ChatGPT" OR "OpenAI" OR "Google AI" OR "Meta AI" OR "Microsoft AI" OR "robots" OR "automatisation" OR "algorithmes" OR "neural networks" OR "réseaux neuronaux") AND NOT ("incendie" OR "feu" OR "catastrophe naturelle" OR "météo" OR "climat" OR "environnement" OR "pollution")"""
    
    params = {
        "q": query,
        "language": "fr",
        "pageSize": page_size,
        "sortBy": "publishedAt",  # Articles les plus récents
        "apiKey": api_key
    }
    response = requests.get(url, params=params)
    articles = response.json().get("articles", [])
    
    # Ajouter la langue à chaque article
    for article in articles:
        article['language'] = 'fr'
    
    return articles

# 2. Résumer un article en français (version améliorée)
def summarize_text_fr(text, openai_api_key, title="", url=""):
    # Vérifier si le texte est valide
    if not text or text.strip() == "" or len(text.strip()) < 10:
        return "Contenu de l'article non disponible"
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Prompt en français pour les articles français
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

# Nouvelle fonction pour valider la pertinence IA d'un article
def validate_ai_relevance(article, openai_api_key):
    """Vérifie si un article traite bien de l'intelligence artificielle"""
    title = article.get('title', '')
    description = article.get('description', '')
    content = article.get('content', '')
    
    # Combiner le titre et la description pour l'analyse
    text_to_analyze = f"{title} {description}"
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    prompt = f"""Analyse ce texte et détermine s'il traite de l'intelligence artificielle (IA), du machine learning, des robots, de l'automatisation, ou de technologies liées à l'IA.

Texte à analyser : "{text_to_analyze}"

Réponds uniquement par "OUI" si l'article traite de l'IA ou de technologies liées, ou "NON" sinon."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1,
        )
        
        result = (response.choices[0].message.content or "").strip().upper()
        return result == "OUI"
    except Exception as e:
        print(f"Erreur lors de la validation IA : {e}")
        # En cas d'erreur, on accepte l'article par défaut
        return True

# 3. Vérifier la qualité technique d'un article
def validate_article_quality(article):
    """Vérifie si un article a un contenu valide techniquement"""
    title = str(article.get('title') or '')
    description = str(article.get('description') or '')
    content = str(article.get('content') or '')
    url = str(article.get('url') or '')
    
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

# 3.5. Supprimer les articles en double
def remove_duplicate_articles(articles):
    """Supprime les articles en double basés sur l'URL et le titre"""
    seen_urls = set()
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        url = article.get('url', '').strip()
        title = article.get('title', '').strip()
        
        # Normaliser le titre pour la comparaison (supprimer les espaces multiples, etc.)
        normalized_title = ' '.join(title.lower().split())
        
        # Vérifier si l'URL ou le titre normalisé a déjà été vu
        if url not in seen_urls and normalized_title not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(normalized_title)
            unique_articles.append(article)
        else:
            print(f"🔄 Article en double supprimé : {title[:50]}...")
    
    print(f"✅ {len(articles) - len(unique_articles)} articles en double supprimés")
    return unique_articles

# 4. Générer le contenu de l'e-mail (version française)
def create_email_content_fr(articles, summaries):
    content = "<h2>Actualités IA - Articles en français</h2><ul>"
    for article, summary in zip(articles, summaries):
        content += f"<li><a href='{article['url']}'>{article['title']}</a><br>{summary}</li><br>"
    content += "</ul>"
    return content

# 5. Envoyer l'e-mail
# Modifié pour accepter une liste de destinataires
def send_email(subject, html_content, sender, recipients, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = sender
    # Si recipients est une liste, joindre avec des virgules
    print("Destinataires :", recipients)
    if isinstance(recipients, list):
        msg['To'] = ', '.join(recipients)
    else:
        msg['To'] = recipients
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(smtp_user, smtp_password)
        server.sendmail(sender, recipients, msg.as_string())

# 6. Orchestration (version française)
def main():
    print("🚀 Démarrage du script de newsletter IA française...")
    
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
    RECIPIENTS = os.environ.get("RECIPIENTS", "")
    RECIPIENTS = [email.strip() for email in RECIPIENTS.split(",") if email.strip()]

    try:
        # Récupérer les articles en français
        print("📰 Récupération des articles français...")
        articles = fetch_ai_articles_fr(NEWSAPI_KEY)
        print(f"✅ Récupéré {len(articles)} articles français")
        
        # Supprimer les articles en double
        print("🔄 Suppression des articles en double...")
        unique_articles = remove_duplicate_articles(articles)
        print(f"✅ {len(unique_articles)} articles uniques après suppression des doublons")
        
        # Filtrer d'abord par qualité technique, puis par pertinence IA
        quality_articles = [article for article in unique_articles if validate_article_quality(article)]
        print(f"✅ {len(quality_articles)} articles de qualité technique après premier filtrage")
        
        # Ensuite filtrer par pertinence IA
        valid_articles = []
        for article in quality_articles:
            print(f"🔍 Validation IA pour : {article['title'][:50]}...")
            if validate_ai_relevance(article, OPENAI_KEY):
                valid_articles.append(article)
                print(f"   ✅ Article validé comme pertinent")
            else:
                print(f"   ❌ Article rejeté (non pertinent)")
        
        print(f"✅ {len(valid_articles)} articles pertinents après validation IA")
        
        if not valid_articles:
            print("❌ Aucun article valide trouvé")
            return
        
        summaries = []
        for i, article in enumerate(valid_articles):
            print(f"📝 Résumé de l'article {i+1}/{len(valid_articles)}...")
            print(f"   Titre: {article['title']}")
            
            # Utiliser description ou content, selon ce qui est disponible
            content = article.get('description', '') or article.get('content', '')
            summary = summarize_text_fr(content, OPENAI_KEY, article['title'], article['url'])
            summaries.append(summary)
            print(f"   Résumé: {summary[:100]}...")
        
        email_content = create_email_content_fr(valid_articles, summaries)
        print("📧 Contenu de l'email généré")
        
        # Envoyer l'email
        send_email("Veille IA quotidienne - Français", email_content, SENDER, RECIPIENTS, SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
        print("✅ Email envoyé avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution : {e}")
        raise

if __name__ == "__main__":
    main() 