"""
Summary Report Generator for Market AI Agent

This module is responsible for:
1. Compiling all insights into a markdown or HTML file
2. Generating sections for top bullish/bearish tickers, macro outlook, etc.
3. Formatting the report for email delivery
"""

import os
import json
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from jinja2 import Template
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication

class SummaryReportGenerator:
    def __init__(self, config_path=None):
        """
        Initialize the Summary Report Generator
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "report": {
                "title": "Daily Market Intelligence Report",
                "sections": [
                    "top_bullish_tickers",
                    "top_bearish_tickers",
                    "macro_outlook",
                    "institutional_flow",
                    "sentiment_divergences"
                ],
                "max_tickers_per_section": 5,
                "format": "html",  # html or markdown
                "include_charts": True
            },
            "email": {
                "enabled": False,  # Set to True to enable email delivery
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "your_email@gmail.com",
                "sender_password": "your_app_password",
                "recipient_email": "recipient@example.com",
                "subject": "Daily Market Intelligence Report - {date}",
                "delivery_time": "07:00",  # 24-hour format
                "time_zone": "America/New_York"  # Eastern Time
            }
        }
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                self.config.update(custom_config)
        
        # Initialize data storage
        self.news_data = None
        self.macro_data = None
        self.cme_data = None
        self.sentiment_data = None
        self.report_content = None
    
    def load_module_data(self, news_data_path=None, macro_data_path=None, 
                        cme_data_path=None, sentiment_data_path=None):
        """
        Load data from all modules
        
        Args:
            news_data_path (str): Path to news sentiment data
            macro_data_path (str): Path to macro sentiment data
            cme_data_path (str): Path to CME volume data
            sentiment_data_path (str): Path to sentiment cross-check data
            
        Returns:
            bool: Whether all data was loaded successfully
        """
        # Load news sentiment data
        if news_data_path and os.path.exists(news_data_path):
            with open(news_data_path, 'r') as f:
                self.news_data = json.load(f)
        
        # Load macro sentiment data
        if macro_data_path and os.path.exists(macro_data_path):
            with open(macro_data_path, 'r') as f:
                self.macro_data = json.load(f)
        
        # Load CME volume data
        if cme_data_path and os.path.exists(cme_data_path):
            with open(cme_data_path, 'r') as f:
                self.cme_data = json.load(f)
        
        # Load sentiment cross-check data
        if sentiment_data_path and os.path.exists(sentiment_data_path):
            with open(sentiment_data_path, 'r') as f:
                self.sentiment_data = json.load(f)
        
        # Check if we have at least some data
        return any([self.news_data, self.macro_data, self.cme_data, self.sentiment_data])
    
    def generate_top_bullish_tickers_section(self):
        """
        Generate the top bullish tickers section
        
        Returns:
            dict: Section data
        """
        section = {
            "title": "Top Bullish Tickers",
            "tickers": [],
            "html": "",
            "markdown": ""
        }
        
        # Check if we have news sentiment data
        if not self.news_data or "bullish" not in self.news_data:
            return section
        
        # Get top bullish tickers
        max_tickers = self.config["report"]["max_tickers_per_section"]
        top_tickers = self.news_data["bullish"][:max_tickers]
        
        # Format ticker data
        for ticker in top_tickers:
            ticker_data = {
                "symbol": ticker["symbol"],
                "type": ticker["type"],
                "confidence": ticker["confidence"],
                "article_count": ticker["article_count"],
                "rationale": ticker["rationale"],
                "supporting_articles": ticker["supporting_articles"]
            }
            section["tickers"].append(ticker_data)
        
        # Generate HTML
        html = "<h2>Top Bullish Tickers</h2>\n"
        if section["tickers"]:
            html += "<table border='1' cellpadding='5' cellspacing='0'>\n"
            html += "<tr><th>Symbol</th><th>Type</th><th>Confidence</th><th>Articles</th><th>Rationale</th></tr>\n"
            
            for ticker in section["tickers"]:
                html += f"<tr><td><b>{ticker['symbol']}</b></td><td>{ticker['type']}</td>"
                html += f"<td>{ticker['confidence']:.1f}%</td><td>{ticker['article_count']}</td>"
                html += f"<td>{ticker['rationale']}</td></tr>\n"
            
            html += "</table>\n"
            
            # Add supporting articles
            html += "<h3>Supporting Articles</h3>\n"
            for ticker in section["tickers"]:
                html += f"<h4>{ticker['symbol']}</h4>\n<ul>\n"
                for article in ticker["supporting_articles"]:
                    html += f"<li><a href='{article['url']}'>{article['title']}</a> ({article['source']}, {article['sentiment']})</li>\n"
                html += "</ul>\n"
        else:
            html += "<p>No bullish tickers found in today's analysis.</p>\n"
        
        section["html"] = html
        
        # Generate Markdown
        markdown = "## Top Bullish Tickers\n\n"
        if section["tickers"]:
            markdown += "| Symbol | Type | Confidence | Articles | Rationale |\n"
            markdown += "|--------|------|------------|----------|----------|\n"
            
            for ticker in section["tickers"]:
                markdown += f"| **{ticker['symbol']}** | {ticker['type']} | {ticker['confidence']:.1f}% | {ticker['article_count']} | {ticker['rationale']} |\n"
            
            markdown += "\n### Supporting Articles\n\n"
            for ticker in section["tickers"]:
                markdown += f"#### {ticker['symbol']}\n\n"
                for article in ticker["supporting_articles"]:
                    markdown += f"- [{article['title']}]({article['url']}) ({article['source']}, {article['sentiment']})\n"
                markdown += "\n"
        else:
            markdown += "No bullish tickers found in today's analysis.\n\n"
        
        section["markdown"] = markdown
        
        return section
    
    def generate_top_bearish_tickers_section(self):
        """
        Generate the top bearish tickers section
        
        Returns:
            dict: Section data
        """
        section = {
            "title": "Top Bearish Tickers",
            "tickers": [],
            "html": "",
            "markdown": ""
        }
        
        # Check if we have news sentiment data
        if not self.news_data or "bearish" not in self.news_data:
            return section
        
        # Get top bearish tickers
        max_tickers = self.config["report"]["max_tickers_per_section"]
        top_tickers = self.news_data["bearish"][:max_tickers]
        
        # Format ticker data
        for ticker in top_tickers:
            ticker_data = {
                "symbol": ticker["symbol"],
                "type": ticker["type"],
                "confidence": ticker["confidence"],
                "article_count": ticker["article_count"],
                "rationale": ticker["rationale"],
                "supporting_articles": ticker["supporting_articles"]
            }
            section["tickers"].append(ticker_data)
        
        # Generate HTML
        html = "<h2>Top Bearish Tickers</h2>\n"
        if section["tickers"]:
            html += "<table border='1' cellpadding='5' cellspacing='0'>\n"
            html += "<tr><th>Symbol</th><th>Type</th><th>Confidence</th><th>Articles</th><th>Rationale</th></tr>\n"
            
            for ticker in section["tickers"]:
                html += f"<tr><td><b>{ticker['symbol']}</b></td><td>{ticker['type']}</td>"
                html += f"<td>{ticker['confidence']:.1f}%</td><td>{ticker['article_count']}</td>"
                html += f"<td>{ticker['rationale']}</td></tr>\n"
            
            html += "</table>\n"
            
            # Add supporting articles
            html += "<h3>Supporting Articles</h3>\n"
            for ticker in section["tickers"]:
                html += f"<h4>{ticker['symbol']}</h4>\n<ul>\n"
                for article in ticker["supporting_articles"]:
                    html += f"<li><a href='{article['url']}'>{article['title']}</a> ({article['source']}, {article['sentiment']})</li>\n"
                html += "</ul>\n"
        else:
            html += "<p>No bearish tickers found in today's analysis.</p>\n"
        
        section["html"] = html
        
        # Generate Markdown
        markdown = "## Top Bearish Tickers\n\n"
        if section["tickers"]:
            markdown += "| Symbol | Type | Confidence | Articles | Rationale |\n"
            markdown += "|--------|------|------------|----------|----------|\n"
            
            for ticker in section["tickers"]:
                markdown += f"| **{ticker['symbol']}** | {ticker['type']} | {ticker['confidence']:.1f}% | {ticker['article_count']} | {ticker['rationale']} |\n"
            
            markdown += "\n### Supporting Articles\n\n"
            for ticker in section["tickers"]:
                markdown += f"#### {ticker['symbol']}\n\n"
                for article in ticker["supporting_articles"]:
                    markdown += f"- [{article['title']}]({article['url']}) ({article['source']}, {article['sentiment']})\n"
                markdown += "\n"
        else:
            markdown += "No bearish tickers found in today's analysis.\n\n"
        
        section["markdown"] = markdown
        
        return section
    
    def generate_macro_outlook_section(self):
        """
        Generate the macro outlook section
        
        Returns:
            dict: Section data
        """
        section = {
            "title": "Macro Outlook (ES Directional Bias)",
            "data": {},
            "html": "",
            "markdown": ""
        }
        
        # Check if we have macro sentiment data
        if not self.macro_data or "environment_rating" not in self.macro_data or "es_bias" not in self.macro_data:
            return section
        
        # Get macro environment rating and ES bias
        environment = self.macro_data["environment_rating"]
        es_bias = self.macro_data["es_bias"]
        indicators = self.macro_data.get("indicators", {})
        
        # Format section data
        section["data"] = {
            "environment": environment,
            "es_bias": es_bias,
            "indicators": {}
        }
        
        # Extract key indicators
        if "vix" in indicators:
            section["data"]["indicators"]["vix"] = {
                "value": indicators["vix"]["value"],
                "interpretation": indicators["vix"]["interpretation"]
            }
        
        if "treasury_yields" in indicators and "values" in indicators["treasury_yields"]:
            yields = indicators["treasury_yields"]["values"]
            section["data"]["indicators"]["yields"] = yields
            section["data"]["indicators"]["yield_curve"] = indicators["treasury_yields"]["interpretation"]
        
        if "economic_data" in indicators and "values" in indicators["economic_data"]:
            econ_data = indicators["economic_data"]["values"]
            section["data"]["indicators"]["economic_data"] = econ_data
        
        # Generate HTML
        html = "<h2>Macro Outlook (ES Directional Bias)</h2>\n"
        
        # ES Bias
        if es_bias:
            direction = es_bias.get("direction", "neutral")
            confidence = es_bias.get("confidence", "low")
            
            # Set color based on direction
            if direction == "long":
                direction_color = "green"
            elif direction == "short":
                direction_color = "red"
            else:
                direction_color = "gray"
            
            html += f"<div style='background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>\n"
            html += f"<h3>S&P 500 E-mini Futures Bias: <span style='color: {direction_color};'>{direction.upper()}</span> ({confidence} confidence)</h3>\n"
            
            if "rationale" in es_bias and es_bias["rationale"]:
                html += "<h4>Rationale:</h4>\n<ul>\n"
                for reason in es_bias["rationale"]:
                    html += f"<li>{reason}</li>\n"
                html += "</ul>\n"
            
            html += "</div>\n"
        
        # Macro Environment
        if environment:
            html += "<h3>Macro Environment Assessment</h3>\n"
            html += "<table border='1' cellpadding='5' cellspacing='0'>\n"
            html += "<tr><th>Factor</th><th>Rating</th></tr>\n"
            
            if "risk_sentiment" in environment:
                html += f"<tr><td>Risk Sentiment</td><td>{environment['risk_sentiment']}</td></tr>\n"
            
            if "inflation_environment" in environment:
                html += f"<tr><td>Inflation Environment</td><td>{environment['inflation_environment']}</td></tr>\n"
            
            if "growth_outlook" in environment:
                html += f"<tr><td>Growth Outlook</td><td>{environment['growth_outlook']}</td></tr>\n"
            
            if "overall_environment" in environment:
                overall = environment['overall_environment']
                color = "green" if overall == "bullish" else ("red" if overall == "bearish" else "gray")
                html += f"<tr><td><b>Overall Environment</b></td><td style='color: {color};'><b>{overall}</b></td></tr>\n"
            
            html += "</table>\n"
        
        # Key Indicators
        html += "<h3>Key Indicators</h3>\n"
        html += "<table border='1' cellpadding='5' cellspacing='0'>\n"
        html += "<tr><th>Indicator</th><th>Value</th><th>Interpretation</th></tr>\n"
        
        # VIX
        if "vix" in section["data"]["indicators"]:
            vix = section["data"]["indicators"]["vix"]
            html += f"<tr><td>VIX</td><td>{vix['value']:.2f}</td><td>{vix['interpretation']}</td></tr>\n"
        
        # Yield Curve
        if "yields" in section["data"]["indicators"]:
            yields = section["data"]["indicators"]["yields"]
            if "10y_2y_spread" in yields:
                spread = yields["10y_2y_spread"]
                color = "red" if spread < 0 else "green"
                html += f"<tr><td>10Y-2Y Spread</td><td style='color: {color};'>{spread:.3f}</td>"
                html += f"<td>{section['data']['indicators'].get('yield_curve', 'N/A')}</td></tr>\n"
            
            if "2y" in yields:
                html += f"<tr><td>2-Year Treasury</td><td>{yields['2y']:.3f}%</td><td>-</td></tr>\n"
           
(Content truncated due to size limit. Use line ranges to read in chunks)