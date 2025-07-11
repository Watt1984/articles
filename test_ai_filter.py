#!/usr/bin/env python3
"""
Script de test pour vérifier le système de filtrage IA
"""

import os
from articles_batch_fr_server import fetch_ai_articles_fr, validate_article_quality, validate_ai_relevance

def test_ai_filtering():
    """Test du système de filtrage IA"""
    
    # Vérifier les variables d'environnement
    newsapi_key = os.environ.get("NEWSAPI_KEY")
    openai_key = os.environ.get("OPENAI_KEY")
    
    if not newsapi_key or not openai_key:
        print("❌ Variables d'environnement manquantes (NEWSAPI_KEY, OPENAI_KEY)")
        return
    
    print("🧪 Test du système de filtrage IA...")
    
    try:
        # Récupérer les articles
        print("📰 Récupération des articles...")
        articles = fetch_ai_articles_fr(newsapi_key, page_size=5)
        print(f"✅ Récupéré {len(articles)} articles")
        
        # Afficher les titres récupérés
        print("\n📋 Articles récupérés :")
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Titre manquant')
            print(f"{i}. {title}")
        
        # Test du filtrage par qualité
        print("\n🔍 Test du filtrage par qualité technique...")
        quality_articles = [article for article in articles if validate_article_quality(article)]
        print(f"✅ {len(quality_articles)} articles de qualité technique")
        
        # Test du filtrage par pertinence IA
        print("\n🤖 Test du filtrage par pertinence IA...")
        ai_articles = []
        for article in quality_articles:
            title = article.get('title', 'Titre manquant')
            print(f"🔍 Validation de : {title[:60]}...")
            
            if validate_ai_relevance(article, openai_key):
                ai_articles.append(article)
                print(f"   ✅ Pertinent pour l'IA")
            else:
                print(f"   ❌ Non pertinent pour l'IA")
        
        print(f"\n📊 Résultats finaux :")
        print(f"   - Articles récupérés : {len(articles)}")
        print(f"   - Articles de qualité : {len(quality_articles)}")
        print(f"   - Articles pertinents IA : {len(ai_articles)}")
        
        if ai_articles:
            print(f"\n✅ Articles pertinents retenus :")
            for i, article in enumerate(ai_articles, 1):
                title = article.get('title', 'Titre manquant')
                print(f"{i}. {title}")
        else:
            print("❌ Aucun article pertinent trouvé")
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")

if __name__ == "__main__":
    test_ai_filtering() 