"""
News & Sentiment Module for Market AI Agent

This module is responsible for:
1. Scraping news from financial news sources (CNBC, Bloomberg, CoinDesk, WSJ)
2. Analyzing sentiment using NLP
3. Extracting tickers, sectors, crypto tokens, and macro themes
4. Prioritizing items from a personal watchlist
5. Generating position suggestions with supporting rationale
"""

import os
import re
import json
import datetime
import pandas as pd
import newspaper
from newspaper import Article
from bs4 import BeautifulSoup
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

class NewsScraperSentiment:
    def __init__(self, config_path=None):
        """
        Initialize the News Scraper and Sentiment Analyzer
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "sources": {
                "cnbc": "https://www.cnbc.com/finance/",
                "bloomberg": "https://www.bloomberg.com/markets",
                "coindesk": "https://www.coindesk.com/",
                "wsj": "https://www.wsj.com/news/markets"
            },
            "watchlist": {
                "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
                "crypto": ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX"],
                "sectors": ["Technology", "Finance", "Energy", "Healthcare", "Consumer"]
            },
            "macro_themes": [
                "inflation", "rate hike", "rate cut", "recession", "gdp", "unemployment",
                "fed", "federal reserve", "interest rate", "monetary policy", "fiscal policy",
                "supply chain", "earnings", "forecast", "guidance", "outlook"
            ]
        }
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                self.config.update(custom_config)
        
        # Initialize sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize transformers pipeline for more advanced NLP tasks
        self.nlp = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
        
        # Compile regex patterns for ticker symbols
        self.ticker_pattern = re.compile(r'\$([A-Z]{1,5})')
        
        # Load stop words
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize data storage
        self.articles = []
        self.analyzed_data = []
    
    def scrape_news(self, max_articles_per_source=10):
        """
        Scrape news from all configured sources
        
        Args:
            max_articles_per_source (int): Maximum number of articles to scrape per source
            
        Returns:
            list: List of article dictionaries
        """
        all_articles = []
        
        for source_name, url in self.config["sources"].items():
            try:
                print(f"Scraping {source_name} from {url}")
                
                # Build newspaper source
                source = newspaper.build(url, memoize_articles=False)
                
                # Get articles
                count = 0
                for article in source.articles:
                    if count >= max_articles_per_source:
                        break
                    
                    try:
                        article.download()
                        article.parse()
                        
                        # Skip articles without text
                        if not article.text or len(article.text) < 100:
                            continue
                        
                        # Create article dictionary
                        article_dict = {
                            'source': source_name,
                            'url': article.url,
                            'title': article.title,
                            'text': article.text,
                            'publish_date': article.publish_date,
                            'authors': article.authors,
                            'top_image': article.top_image,
                            'scraped_date': datetime.datetime.now()
                        }
                        
                        all_articles.append(article_dict)
                        count += 1
                        
                    except Exception as e:
                        print(f"Error processing article {article.url}: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"Error scraping {source_name}: {str(e)}")
                continue
        
        self.articles = all_articles
        return all_articles
    
    def analyze_sentiment(self):
        """
        Analyze sentiment for all scraped articles
        
        Returns:
            list: List of analyzed article dictionaries
        """
        analyzed_articles = []
        
        for article in self.articles:
            try:
                # Get VADER sentiment
                vader_sentiment = self.vader.polarity_scores(article['text'])
                
                # Get transformer-based sentiment
                transformer_sentiment = self.nlp(article['text'][:512])[0]  # Limit text length for transformer
                
                # Extract tickers mentioned in the article
                tickers_mentioned = self._extract_tickers(article['text'], article['title'])
                
                # Extract sectors mentioned
                sectors_mentioned = self._extract_sectors(article['text'])
                
                # Extract crypto tokens mentioned
                crypto_mentioned = self._extract_crypto(article['text'], article['title'])
                
                # Extract macro themes
                macro_themes = self._extract_macro_themes(article['text'])
                
                # Determine overall sentiment
                compound_score = vader_sentiment['compound']
                if compound_score >= 0.05:
                    sentiment = "bullish"
                elif compound_score <= -0.05:
                    sentiment = "bearish"
                else:
                    sentiment = "neutral"
                
                # Create analyzed article dictionary
                analyzed_article = {
                    'source': article['source'],
                    'url': article['url'],
                    'title': article['title'],
                    'publish_date': article['publish_date'],
                    'scraped_date': article['scraped_date'],
                    'sentiment': sentiment,
                    'sentiment_scores': {
                        'vader': vader_sentiment,
                        'transformer': {
                            'label': transformer_sentiment['label'],
                            'score': transformer_sentiment['score']
                        }
                    },
                    'tickers': tickers_mentioned,
                    'sectors': sectors_mentioned,
                    'crypto': crypto_mentioned,
                    'macro_themes': macro_themes,
                    'watchlist_match': any(ticker in self.config['watchlist']['stocks'] for ticker in tickers_mentioned) or
                                      any(token in self.config['watchlist']['crypto'] for token in crypto_mentioned)
                }
                
                analyzed_articles.append(analyzed_article)
                
            except Exception as e:
                print(f"Error analyzing article {article['url']}: {str(e)}")
                continue
        
        self.analyzed_data = analyzed_articles
        return analyzed_articles
    
    def _extract_tickers(self, text, title):
        """Extract stock ticker symbols from text"""
        # Look for tickers with $ symbol
        dollar_tickers = self.ticker_pattern.findall(text + " " + title)
        
        # Look for tickers in watchlist
        watchlist_tickers = []
        for ticker in self.config['watchlist']['stocks']:
            # Match whole word only
            pattern = r'\b' + re.escape(ticker) + r'\b'
            if re.search(pattern, text + " " + title):
                watchlist_tickers.append(ticker)
        
        # Combine and remove duplicates
        all_tickers = list(set(dollar_tickers + watchlist_tickers))
        
        return all_tickers
    
    def _extract_sectors(self, text):
        """Extract sectors mentioned in text"""
        mentioned_sectors = []
        for sector in self.config['watchlist']['sectors']:
            if sector.lower() in text.lower():
                mentioned_sectors.append(sector)
        return mentioned_sectors
    
    def _extract_crypto(self, text, title):
        """Extract crypto tokens mentioned in text"""
        mentioned_crypto = []
        combined_text = (text + " " + title).lower()
        
        # Check for crypto tokens in watchlist
        for token in self.config['watchlist']['crypto']:
            if token.lower() in combined_text:
                mentioned_crypto.append(token)
        
        # Check for common crypto names
        crypto_names = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "solana": "SOL",
            "ripple": "XRP",
            "cardano": "ADA",
            "dogecoin": "DOGE",
            "avalanche": "AVAX"
        }
        
        for name, symbol in crypto_names.items():
            if name in combined_text and symbol not in mentioned_crypto:
                mentioned_crypto.append(symbol)
        
        return mentioned_crypto
    
    def _extract_macro_themes(self, text):
        """Extract macro themes mentioned in text"""
        text_lower = text.lower()
        mentioned_themes = []
        
        for theme in self.config['macro_themes']:
            if theme.lower() in text_lower:
                mentioned_themes.append(theme)
        
        return mentioned_themes
    
    def prioritize_articles(self):
        """
        Prioritize articles based on watchlist matches and sentiment strength
        
        Returns:
            list: Prioritized list of analyzed articles
        """
        if not self.analyzed_data:
            return []
        
        # Create a copy of the analyzed data
        prioritized = self.analyzed_data.copy()
        
        # Sort by watchlist match (True first) and then by absolute sentiment score
        prioritized.sort(key=lambda x: (
            not x['watchlist_match'],  # Watchlist matches first
            -abs(x['sentiment_scores']['vader']['compound'])  # Then by sentiment strength
        ))
        
        return prioritized
    
    def generate_position_suggestions(self):
        """
        Generate position suggestions based on analyzed articles
        
        Returns:
            dict: Dictionary of position suggestions with supporting rationale
        """
        if not self.analyzed_data:
            return {"bullish": [], "bearish": [], "neutral": []}
        
        # Group articles by ticker and sentiment
        ticker_sentiment = {}
        crypto_sentiment = {}
        
        for article in self.analyzed_data:
            # Process stock tickers
            for ticker in article['tickers']:
                if ticker not in ticker_sentiment:
                    ticker_sentiment[ticker] = {
                        'bullish': 0,
                        'bearish': 0,
                        'neutral': 0,
                        'articles': []
                    }
                
                ticker_sentiment[ticker][article['sentiment']] += 1
                ticker_sentiment[ticker]['articles'].append({
                    'title': article['title'],
                    'url': article['url'],
                    'source': article['source'],
                    'sentiment': article['sentiment'],
                    'score': article['sentiment_scores']['vader']['compound']
                })
            
            # Process crypto tokens
            for token in article['crypto']:
                if token not in crypto_sentiment:
                    crypto_sentiment[token] = {
                        'bullish': 0,
                        'bearish': 0,
                        'neutral': 0,
                        'articles': []
                    }
                
                crypto_sentiment[token][article['sentiment']] += 1
                crypto_sentiment[token]['articles'].append({
                    'title': article['title'],
                    'url': article['url'],
                    'source': article['source'],
                    'sentiment': article['sentiment'],
                    'score': article['sentiment_scores']['vader']['compound']
                })
        
        # Generate position suggestions
        suggestions = {
            'bullish': [],
            'bearish': [],
            'neutral': []
        }
        
        # Process stock suggestions
        for ticker, data in ticker_sentiment.items():
            total_articles = data['bullish'] + data['bearish'] + data['neutral']
            if total_articles < 2:  # Require at least 2 articles to make a suggestion
                continue
            
            # Determine overall sentiment
            if data['bullish'] > data['bearish'] * 1.5:  # Significantly more bullish
                sentiment = 'bullish'
            elif data['bearish'] > data['bullish'] * 1.5:  # Significantly more bearish
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Create suggestion
            suggestion = {
                'symbol': ticker,
                'type': 'stock',
                'sentiment': sentiment,
                'confidence': (data[sentiment] / total_articles) * 100,
                'article_count': total_articles,
                'supporting_articles': sorted(data['articles'], key=lambda x: abs(x['score']), reverse=True)[:3],
                'rationale': f"Based on {total_articles} recent articles with {data[sentiment]} sentiment majority."
            }
            
            suggestions[sentiment].append(suggestion)
        
        # Process crypto suggestions
        for token, data in crypto_sentiment.items():
            total_articles = data['bullish'] + data['bearish'] + data['neutral']
            if total_articles < 2:  # Require at least 2 articles to make a suggestion
                continue
            
            # Determine overall sentiment
            if data['bullish'] > data['bearish'] * 1.5:  # Significantly more bullish
                sentiment = 'bullish'
            elif data['bearish'] > data['bullish'] * 1.5:  # Significantly more bearish
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # Create suggestion
            suggestion = {
                'symbol': token,
                'type': 'crypto',
                'sentiment': sentiment,
                'confidence': (data[sentiment] / total_articles) * 100,
                'article_count': total_articles,
                'supporting_articles': sorted(data['articles'], key=lambda x: abs(x['score']), reverse=True)[:3],
                'rationale': f"Based on {total_articles} recent articles with {data[sentiment]} sentiment majority."
            }
            
            suggestions[sentiment].append(suggestion)
        
        # Sort suggestions by confidence
        for sentiment in suggestions:
            suggestions[sentiment].so
(Content truncated due to size limit. Use line ranges to read in chunks)