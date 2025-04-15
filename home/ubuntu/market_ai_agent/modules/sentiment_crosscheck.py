"""
Sentiment Cross-check Module for Market AI Agent

This module is responsible for:
1. Pulling recent financial sentiment from Twitter, Reddit (WSB, Investing), and Discord
2. Using LLM to identify if social sentiment confirms or contradicts professional news flow
3. Detecting sentiment divergences that may indicate market turning points
"""

import os
import re
import json
import datetime
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentCrossChecker:
    def __init__(self, config_path=None):
        """
        Initialize the Sentiment Cross-checker
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "sources": {
                "reddit": {
                    "subreddits": ["wallstreetbets", "investing", "stocks", "options"],
                    "timeframe": "day",  # day, week, month
                    "limit": 100  # posts to fetch per subreddit
                },
                "twitter": {
                    "search_terms": ["stocks", "investing", "trading", "market", "SPY", "QQQ", "FOMC"],
                    "influencers": ["jimcramer", "elonmusk", "chamath", "carlicahn", "elerianm"],
                    "limit": 100  # tweets to fetch per term/influencer
                },
                "stocktwits": {
                    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
                    "limit": 30  # messages to fetch per symbol
                }
            },
            "watchlist": {
                "stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA"],
                "indices": ["SPY", "QQQ", "IWM", "DIA"],
                "sectors": ["XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE"],
                "crypto": ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX"]
            },
            "sentiment_thresholds": {
                "divergence": 0.3,  # Minimum difference to flag as divergence
                "consensus": 0.7    # Minimum score to consider strong consensus
            }
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
        
        # Initialize data storage
        self.social_data = {}
        self.sentiment_analysis = {}
        self.divergences = []
        
        # Reference to professional news sentiment (to be provided)
        self.news_sentiment = None
    
    def fetch_reddit_data(self, use_mock_data=True):
        """
        Fetch data from Reddit
        
        Args:
            use_mock_data (bool): Whether to use mock data instead of actual API calls
            
        Returns:
            dict: Dictionary of Reddit data by subreddit
        """
        reddit_data = {}
        
        if use_mock_data:
            # Generate mock data for demonstration
            subreddits = self.config["sources"]["reddit"]["subreddits"]
            
            for subreddit in subreddits:
                posts = []
                
                # Generate different sentiment profiles for different subreddits
                if subreddit == "wallstreetbets":
                    # WSB tends to be more extreme and meme-focused
                    bullish_ratio = 0.6  # 60% bullish
                    bearish_ratio = 0.3  # 30% bearish
                    neutral_ratio = 0.1  # 10% neutral
                    
                    # Common WSB tickers
                    tickers = ["GME", "AMC", "TSLA", "AAPL", "NVDA", "AMD", "PLTR", "SPY", "QQQ"]
                    
                elif subreddit == "investing":
                    # Investing tends to be more balanced and conservative
                    bullish_ratio = 0.4  # 40% bullish
                    bearish_ratio = 0.3  # 30% bearish
                    neutral_ratio = 0.3  # 30% neutral
                    
                    # Common investing tickers
                    tickers = ["VTI", "VOO", "VXUS", "BND", "AAPL", "MSFT", "GOOGL", "AMZN", "BRK.B"]
                    
                else:
                    # Default sentiment distribution
                    bullish_ratio = 0.5  # 50% bullish
                    bearish_ratio = 0.3  # 30% bearish
                    neutral_ratio = 0.2  # 20% neutral
                    
                    # Mix of tickers
                    tickers = self.config["watchlist"]["stocks"] + self.config["watchlist"]["indices"]
                
                # Generate mock posts
                num_posts = min(self.config["sources"]["reddit"]["limit"], 50)  # Cap at 50 for mock data
                
                for i in range(num_posts):
                    # Determine sentiment category
                    rand = np.random.random()
                    if rand < bullish_ratio:
                        sentiment = "bullish"
                    elif rand < bullish_ratio + bearish_ratio:
                        sentiment = "bearish"
                    else:
                        sentiment = "neutral"
                    
                    # Select random tickers
                    post_tickers = np.random.choice(tickers, size=min(3, len(tickers)), replace=False).tolist()
                    
                    # Generate title based on sentiment
                    if sentiment == "bullish":
                        titles = [
                            f"{ticker} is going to the moon! 🚀",
                            f"Why {ticker} is undervalued right now",
                            f"Just bought more {ticker}, here's why",
                            f"{ticker} earnings will crush expectations",
                            f"The bull case for {ticker} that no one is talking about"
                        ]
                    elif sentiment == "bearish":
                        titles = [
                            f"{ticker} is overvalued, change my mind",
                            f"Why I'm shorting {ticker}",
                            f"{ticker} is about to crash, here's why",
                            f"The bear case for {ticker} that everyone is ignoring",
                            f"Just sold all my {ticker}, here's why"
                        ]
                    else:
                        titles = [
                            f"Thoughts on {ticker}?",
                            f"{ticker} analysis - what am I missing?",
                            f"Is {ticker} a good long-term hold?",
                            f"DD on {ticker} - mixed signals",
                            f"Should I buy {ticker} at current levels?"
                        ]
                    
                    title = np.random.choice(titles).replace("{ticker}", np.random.choice(post_tickers))
                    
                    # Generate post data
                    post = {
                        'id': f"mock_{subreddit}_{i}",
                        'subreddit': subreddit,
                        'title': title,
                        'score': int(np.random.exponential(scale=50)),  # Upvotes follow exponential distribution
                        'num_comments': int(np.random.exponential(scale=20)),
                        'created_utc': (datetime.datetime.now() - datetime.timedelta(hours=np.random.randint(1, 24))).timestamp(),
                        'tickers': post_tickers,
                        'url': f"https://reddit.com/r/{subreddit}/mock_{i}"
                    }
                    
                    posts.append(post)
                
                # Sort by score
                posts.sort(key=lambda x: x['score'], reverse=True)
                
                reddit_data[subreddit] = posts
        
        else:
            # In a real implementation, you would use the Reddit API or PRAW
            # This would require proper authentication and API handling
            # For now, we'll leave this as a placeholder
            print("Real Reddit API not implemented, using mock data instead")
            return self.fetch_reddit_data(use_mock_data=True)
        
        # Store the data
        self.social_data["reddit"] = reddit_data
        
        return reddit_data
    
    def fetch_twitter_data(self, use_mock_data=True):
        """
        Fetch data from Twitter
        
        Args:
            use_mock_data (bool): Whether to use mock data instead of actual API calls
            
        Returns:
            dict: Dictionary of Twitter data by search term and influencer
        """
        twitter_data = {
            "search_terms": {},
            "influencers": {}
        }
        
        if use_mock_data:
            # Generate mock data for demonstration
            search_terms = self.config["sources"]["twitter"]["search_terms"]
            influencers = self.config["sources"]["twitter"]["influencers"]
            
            # Generate mock tweets for search terms
            for term in search_terms:
                tweets = []
                
                # Determine sentiment distribution based on term
                if term in ["stocks", "investing", "market"]:
                    # General terms tend to be more balanced
                    bullish_ratio = 0.5
                    bearish_ratio = 0.3
                elif term in ["SPY", "QQQ"]:
                    # Index terms might reflect current market sentiment
                    bullish_ratio = 0.6  # Slightly more bullish for this mock
                    bearish_ratio = 0.3
                else:
                    # Default
                    bullish_ratio = 0.5
                    bearish_ratio = 0.3
                
                neutral_ratio = 1 - bullish_ratio - bearish_ratio
                
                # Generate mock tweets
                num_tweets = min(self.config["sources"]["twitter"]["limit"], 30)  # Cap at 30 for mock data
                
                for i in range(num_tweets):
                    # Determine sentiment category
                    rand = np.random.random()
                    if rand < bullish_ratio:
                        sentiment = "bullish"
                    elif rand < bullish_ratio + bearish_ratio:
                        sentiment = "bearish"
                    else:
                        sentiment = "neutral"
                    
                    # Generate tweet text based on sentiment
                    if sentiment == "bullish":
                        texts = [
                            f"Feeling bullish on {term} today! Markets looking strong.",
                            f"{term} setup looks great, expecting a breakout soon.",
                            f"Just added more {term} to my portfolio. The uptrend is clear.",
                            f"Technical indicators for {term} all pointing up. Let's go!",
                            f"{term} fundamentals are solid. This is just the beginning of the rally."
                        ]
                    elif sentiment == "bearish":
                        texts = [
                            f"Not liking what I'm seeing in {term}. Bearish signals everywhere.",
                            f"{term} looking toppy here. Taking profits and moving to cash.",
                            f"The {term} rally is running out of steam. Be careful out there.",
                            f"Technical breakdown imminent in {term}. Protect your capital.",
                            f"{term} fundamentals deteriorating. This won't end well."
                        ]
                    else:
                        texts = [
                            f"Mixed signals on {term} today. Staying neutral for now.",
                            f"Watching {term} closely but not taking a position yet.",
                            f"{term} at a critical juncture. Could go either way.",
                            f"Need more data before making a call on {term}.",
                            f"Interesting price action in {term} but waiting for confirmation."
                        ]
                    
                    text = np.random.choice(texts)
                    
                    # Generate tweet data
                    tweet = {
                        'id': f"mock_{term}_{i}",
                        'text': text,
                        'likes': int(np.random.exponential(scale=20)),
                        'retweets': int(np.random.exponential(scale=5)),
                        'created_at': (datetime.datetime.now() - datetime.timedelta(hours=np.random.randint(1, 12))).isoformat(),
                        'user': {
                            'username': f"mock_user_{np.random.randint(1000, 9999)}",
                            'followers': int(np.random.exponential(scale=500))
                        },
                        'search_term': term
                    }
                    
                    tweets.append(tweet)
                
                # Sort by engagement (likes + retweets)
                tweets.sort(key=lambda x: x['likes'] + x['retweets'], reverse=True)
                
                twitter_data["search_terms"][term] = tweets
            
            # Generate mock tweets for influencers
            for influencer in influencers:
                tweets = []
                
                # Determine sentiment distribution based on influencer
                if influencer == "jimcramer":
                    # Jim Cramer is known for being contrarian
                    bullish_ratio = 0.7  # Very bullish (which might be a contrarian indicator)
                    bearish_ratio = 0.2
                elif influencer == "elonmusk":
                    # Elon Musk tends to be very bullish
                    bullish_ratio = 0.8
                    bearish_ratio = 0.1
                else:
                    # Default
                    bullish_ratio = 0.6
                    bearish_ratio = 0.3
                
                neutral_ratio = 1 - bullish_ratio - bearish_ratio
                
                # Generate mock tweets
                num_tweets = min(self.config["sources"]["twitter"]["limit"], 10)  # Cap at 10 for mock data
                
                for i in range(num_tweets):
                    # Determine sentiment category
                    rand = np.random.random()
                    if rand < bullish_ratio:
                        sentiment = "bullish"
                    elif rand < bullish_ratio + bearish_ratio:
                        sentiment = "bearish"
                    else:
                        sentiment = "neutral"
                    
                    # Select random tickers
                    tickers = self.config["watchlist"]["stocks"]
                    tweet_tickers = np.random.choice(tickers, size=min(2, len(tickers)), replace=False).tolist()
                    ticker = tweet_tickers[0]
                    
                    # Generate tweet text based on sentiment and influencer
                    if influencer == "jimcramer":
                        if sentiment == "bullish":
                            texts = [
                                f"{ticker} is a BUY BUY BUY! Don't miss this opportunity!",
                                f"I'm pounding the table on {ticker}. This is the 
(Content truncated due to size limit. Use line ranges to read in chunks)