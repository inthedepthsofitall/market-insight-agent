"""
Main module for Market AI Agent

This module integrates all components and provides the main entry point for the system.
"""

import os
import sys
import json
import argparse
import datetime
import logging
from pathlib import Path

# Import modules
from modules.news_sentiment import NewsScraperSentiment
from modules.macro_sentiment import MacroSentimentAnalyzer
from modules.cme_volume import CMEVolumeTracker
from modules.sentiment_crosscheck import SentimentCrossChecker
from modules.report_generator import SummaryReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/market_ai.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("market_ai")

class MarketAIAgent:
    def __init__(self, config_path=None):
        """
        Initialize the Market AI Agent
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "data_dir": "data",
            "reports_dir": "reports",
            "use_mock_data": True,  # Set to False for production
            "modules": {
                "news_sentiment": {
                    "enabled": True,
                    "max_articles_per_source": 10
                },
                "macro_sentiment": {
                    "enabled": True
                },
                "cme_volume": {
                    "enabled": True,
                    "contracts": ["ES", "NQ", "YM"]
                },
                "sentiment_crosscheck": {
                    "enabled": True
                },
                "report_generator": {
                    "enabled": True,
                    "format": "html",  # html or markdown
                    "email": {
                        "enabled": False  # Set to True to enable email delivery
                    }
                }
            }
        }
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                self._update_config(self.config, custom_config)
        
        # Create directories
        os.makedirs(self.config["data_dir"], exist_ok=True)
        os.makedirs(self.config["reports_dir"], exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Initialize module data paths
        self.data_paths = {
            "news_sentiment": os.path.join(self.config["data_dir"], "news_sentiment"),
            "macro_sentiment": os.path.join(self.config["data_dir"], "macro_sentiment"),
            "cme_volume": os.path.join(self.config["data_dir"], "cme_volume"),
            "sentiment_crosscheck": os.path.join(self.config["data_dir"], "sentiment_crosscheck")
        }
        
        # Create data directories
        for path in self.data_paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Initialize modules
        self._init_modules()
    
    def _update_config(self, base_config, new_config):
        """
        Recursively update configuration
        
        Args:
            base_config (dict): Base configuration to update
            new_config (dict): New configuration values
        """
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._update_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def _init_modules(self):
        """Initialize all modules"""
        # News & Sentiment Module
        if self.config["modules"]["news_sentiment"]["enabled"]:
            self.news_sentiment = NewsScraperSentiment()
        else:
            self.news_sentiment = None
        
        # Macro Sentiment Analyzer
        if self.config["modules"]["macro_sentiment"]["enabled"]:
            self.macro_sentiment = MacroSentimentAnalyzer()
        else:
            self.macro_sentiment = None
        
        # CME Volume/Open Interest Tracker
        if self.config["modules"]["cme_volume"]["enabled"]:
            self.cme_volume = CMEVolumeTracker()
        else:
            self.cme_volume = None
        
        # Sentiment Cross-check Module
        if self.config["modules"]["sentiment_crosscheck"]["enabled"]:
            self.sentiment_crosscheck = SentimentCrossChecker()
        else:
            self.sentiment_crosscheck = None
        
        # Summary Report Generator
        if self.config["modules"]["report_generator"]["enabled"]:
            self.report_generator = SummaryReportGenerator()
        else:
            self.report_generator = None
    
    def run_news_sentiment(self):
        """Run News & Sentiment Module"""
        if not self.news_sentiment:
            logger.warning("News & Sentiment Module is disabled")
            return None
        
        logger.info("Running News & Sentiment Module...")
        
        try:
            # Scrape news
            max_articles = self.config["modules"]["news_sentiment"]["max_articles_per_source"]
            articles = self.news_sentiment.scrape_news(max_articles_per_source=max_articles)
            logger.info(f"Scraped {len(articles)} articles")
            
            # Analyze sentiment
            analyzed = self.news_sentiment.analyze_sentiment()
            logger.info(f"Analyzed {len(analyzed)} articles")
            
            # Generate position suggestions
            suggestions = self.news_sentiment.generate_position_suggestions()
            logger.info(f"Generated {len(suggestions['bullish'])} bullish, {len(suggestions['bearish'])} bearish suggestions")
            
            # Save results
            self.news_sentiment.save_results(self.data_paths["news_sentiment"])
            logger.info(f"Saved news sentiment results to {self.data_paths['news_sentiment']}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in News & Sentiment Module: {str(e)}")
            return None
    
    def run_macro_sentiment(self):
        """Run Macro Sentiment Analyzer"""
        if not self.macro_sentiment:
            logger.warning("Macro Sentiment Analyzer is disabled")
            return None
        
        logger.info("Running Macro Sentiment Analyzer...")
        
        try:
            # Run analysis
            use_mock_data = self.config["use_mock_data"]
            analysis = self.macro_sentiment.run_analysis(use_mock_data=use_mock_data)
            
            # Log ES bias
            if self.macro_sentiment.es_bias:
                logger.info(f"ES Bias: {self.macro_sentiment.es_bias['direction']} ({self.macro_sentiment.es_bias['confidence']} confidence)")
            
            # Save results
            self.macro_sentiment.save_results(self.data_paths["macro_sentiment"])
            logger.info(f"Saved macro sentiment results to {self.data_paths['macro_sentiment']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in Macro Sentiment Analyzer: {str(e)}")
            return None
    
    def run_cme_volume(self):
        """Run CME Volume/Open Interest Tracker"""
        if not self.cme_volume:
            logger.warning("CME Volume/Open Interest Tracker is disabled")
            return None
        
        logger.info("Running CME Volume/Open Interest Tracker...")
        
        try:
            # Run analysis
            use_mock_data = self.config["use_mock_data"]
            contracts = self.config["modules"]["cme_volume"]["contracts"]
            results = self.cme_volume.run_analysis(contracts=contracts, use_mock_data=use_mock_data)
            
            # Log alerts
            logger.info(f"Generated {len(self.cme_volume.alerts)} alerts")
            
            # Save results
            self.cme_volume.save_results(self.data_paths["cme_volume"])
            logger.info(f"Saved CME volume results to {self.data_paths['cme_volume']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in CME Volume/Open Interest Tracker: {str(e)}")
            return None
    
    def run_sentiment_crosscheck(self, news_sentiment=None):
        """
        Run Sentiment Cross-check Module
        
        Args:
            news_sentiment (dict): News sentiment data from News & Sentiment Module
        """
        if not self.sentiment_crosscheck:
            logger.warning("Sentiment Cross-check Module is disabled")
            return None
        
        logger.info("Running Sentiment Cross-check Module...")
        
        try:
            # Run analysis
            use_mock_data = self.config["use_mock_data"]
            results = self.sentiment_crosscheck.run_analysis(news_sentiment=news_sentiment, use_mock_data=use_mock_data)
            
            # Log divergences
            if self.sentiment_crosscheck.divergences:
                logger.info(f"Found {len(self.sentiment_crosscheck.divergences)} sentiment divergences")
            else:
                logger.info("No sentiment divergences found")
            
            # Save results
            self.sentiment_crosscheck.save_results(self.data_paths["sentiment_crosscheck"])
            logger.info(f"Saved sentiment cross-check results to {self.data_paths['sentiment_crosscheck']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Sentiment Cross-check Module: {str(e)}")
            return None
    
    def run_report_generator(self):
        """Run Summary Report Generator"""
        if not self.report_generator:
            logger.warning("Summary Report Generator is disabled")
            return None
        
        logger.info("Running Summary Report Generator...")
        
        try:
            # Run report generation
            saved_files = self.report_generator.run(
                data_dir=self.config["data_dir"],
                output_dir=self.config["reports_dir"]
            )
            
            logger.info(f"Report saved to: {saved_files}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Error in Summary Report Generator: {str(e)}")
            return None
    
    def run_all(self):
        """Run all modules in sequence"""
        logger.info("Starting Market AI Agent run...")
        
        # Run News & Sentiment Module
        news_results = self.run_news_sentiment()
        
        # Run Macro Sentiment Analyzer
        macro_results = self.run_macro_sentiment()
        
        # Run CME Volume/Open Interest Tracker
        cme_results = self.run_cme_volume()
        
        # Run Sentiment Cross-check Module
        sentiment_results = self.run_sentiment_crosscheck(news_sentiment=news_results)
        
        # Run Summary Report Generator
        report_files = self.run_report_generator()
        
        logger.info("Market AI Agent run completed successfully")
        
        return {
            "news_results": news_results,
            "macro_results": macro_results,
            "cme_results": cme_results,
            "sentiment_results": sentiment_results,
            "report_files": report_files
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Market AI Agent")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--module", type=str, choices=["news", "macro", "cme", "sentiment", "report", "all"], 
                        default="all", help="Module to run (default: all)")
    args = parser.parse_args()
    
    # Initialize agent
    agent = MarketAIAgent(config_path=args.config)
    
    # Run specified module
    if args.module == "news":
        agent.run_news_sentiment()
    elif args.module == "macro":
        agent.run_macro_sentiment()
    elif args.module == "cme":
        agent.run_cme_volume()
    elif args.module == "sentiment":
        agent.run_sentiment_crosscheck()
    elif args.module == "report":
        agent.run_report_generator()
    else:
        agent.run_all()

if __name__ == "__main__":
    main()
