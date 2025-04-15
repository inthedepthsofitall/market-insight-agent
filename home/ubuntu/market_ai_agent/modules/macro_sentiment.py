"""
Macro Sentiment Analyzer for Market AI Agent

This module is responsible for:
1. Scraping and processing key macro indicators (VIX, CPI, PPI, Core PCE, Treasury Yields, Fed minutes)
2. Rating the macro environment (risk-on, risk-off, inflationary, deflationary)
3. Suggesting long/short bias for S&P 500 E-mini futures (ES)
"""

import os
import re
import json
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np
from datetime import datetime, timedelta

class MacroSentimentAnalyzer:
    def __init__(self, config_path=None):
        """
        Initialize the Macro Sentiment Analyzer
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "indicators": {
                "vix": {
                    "url": "https://www.cnbc.com/quotes/.VIX",
                    "threshold_low": 15,
                    "threshold_high": 25
                },
                "treasury_yields": {
                    "urls": {
                        "2y": "https://www.cnbc.com/quotes/US2Y",
                        "10y": "https://www.cnbc.com/quotes/US10Y",
                        "30y": "https://www.cnbc.com/quotes/US30Y"
                    },
                    "inversion_threshold": 0
                },
                "economic_data": {
                    "fred_api_key": "YOUR_FRED_API_KEY",  # User should replace this
                    "series": {
                        "cpi": "CPIAUCSL",
                        "core_cpi": "CPILFESL",
                        "ppi": "PPIACO",
                        "core_pce": "PCEPILFE",
                        "unemployment": "UNRATE",
                        "gdp": "GDP"
                    }
                },
                "fed_minutes": {
                    "url": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
                }
            },
            "thresholds": {
                "inflation": {
                    "high": 3.0,  # Annual inflation rate above 3% is considered high
                    "low": 1.0    # Annual inflation rate below 1% is considered low
                },
                "yield_curve": {
                    "inversion": -0.1  # 10Y-2Y spread below -0.1 is considered inverted
                }
            }
        }
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                self.config.update(custom_config)
        
        # Initialize data storage
        self.indicators = {}
        self.environment_rating = {}
        self.es_bias = None
        
    def fetch_vix(self):
        """
        Fetch current VIX value
        
        Returns:
            float: Current VIX value
        """
        try:
            url = self.config["indicators"]["vix"]["url"]
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the VIX value (this selector might need adjustment based on CNBC's HTML structure)
            vix_element = soup.select_one(".QuoteStrip-lastPrice")
            if vix_element:
                vix_value = float(vix_element.text.strip())
                
                # Store the value
                self.indicators["vix"] = {
                    "value": vix_value,
                    "timestamp": datetime.now(),
                    "interpretation": self._interpret_vix(vix_value)
                }
                
                return vix_value
            else:
                print("Could not find VIX value on the page")
                return None
                
        except Exception as e:
            print(f"Error fetching VIX: {str(e)}")
            return None
    
    def _interpret_vix(self, vix_value):
        """
        Interpret VIX value
        
        Args:
            vix_value (float): VIX value
            
        Returns:
            str: Interpretation of VIX value
        """
        threshold_low = self.config["indicators"]["vix"]["threshold_low"]
        threshold_high = self.config["indicators"]["vix"]["threshold_high"]
        
        if vix_value < threshold_low:
            return "low_volatility"
        elif vix_value > threshold_high:
            return "high_volatility"
        else:
            return "normal_volatility"
    
    def fetch_treasury_yields(self):
        """
        Fetch current Treasury yields
        
        Returns:
            dict: Dictionary of Treasury yields
        """
        yields = {}
        
        try:
            for tenor, url in self.config["indicators"]["treasury_yields"]["urls"].items():
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the yield value (this selector might need adjustment based on CNBC's HTML structure)
                yield_element = soup.select_one(".QuoteStrip-lastPrice")
                if yield_element:
                    yield_value = float(yield_element.text.strip())
                    yields[tenor] = yield_value
                else:
                    print(f"Could not find {tenor} Treasury yield on the page")
            
            # Calculate spreads
            if '2y' in yields and '10y' in yields:
                yields['10y_2y_spread'] = yields['10y'] - yields['2y']
            
            if '10y' in yields and '30y' in yields:
                yields['30y_10y_spread'] = yields['30y'] - yields['10y']
            
            # Store the values
            self.indicators["treasury_yields"] = {
                "values": yields,
                "timestamp": datetime.now(),
                "interpretation": self._interpret_yield_curve(yields)
            }
            
            return yields
                
        except Exception as e:
            print(f"Error fetching Treasury yields: {str(e)}")
            return {}
    
    def _interpret_yield_curve(self, yields):
        """
        Interpret yield curve
        
        Args:
            yields (dict): Dictionary of Treasury yields
            
        Returns:
            str: Interpretation of yield curve
        """
        if '10y_2y_spread' in yields:
            spread = yields['10y_2y_spread']
            inversion_threshold = self.config["thresholds"]["yield_curve"]["inversion"]
            
            if spread < inversion_threshold:
                return "inverted"
            elif spread < 0.5:
                return "flat"
            else:
                return "normal"
        else:
            return "unknown"
    
    def fetch_economic_data(self, use_mock_data=True):
        """
        Fetch economic data from FRED
        
        Args:
            use_mock_data (bool): Whether to use mock data instead of actual API calls
            
        Returns:
            dict: Dictionary of economic data
        """
        economic_data = {}
        
        # For demonstration purposes, we'll use mock data
        # In a real implementation, you would use the FRED API with an API key
        if use_mock_data:
            # Mock data for demonstration
            economic_data = {
                "cpi": {
                    "latest": 3.2,
                    "previous": 3.1,
                    "yoy_change": 3.2,
                    "date": "2025-03-15"
                },
                "core_cpi": {
                    "latest": 2.8,
                    "previous": 2.9,
                    "yoy_change": 2.8,
                    "date": "2025-03-15"
                },
                "ppi": {
                    "latest": 2.5,
                    "previous": 2.7,
                    "yoy_change": 2.5,
                    "date": "2025-03-10"
                },
                "core_pce": {
                    "latest": 2.2,
                    "previous": 2.3,
                    "yoy_change": 2.2,
                    "date": "2025-03-01"
                },
                "unemployment": {
                    "latest": 3.8,
                    "previous": 3.7,
                    "mom_change": 0.1,
                    "date": "2025-04-05"
                },
                "gdp": {
                    "latest": 2.1,
                    "previous": 2.3,
                    "qoq_change": -0.2,
                    "date": "2025-03-30"
                }
            }
        else:
            # Use FRED API to fetch actual data
            # This would require an API key and proper implementation
            # For now, we'll leave this as a placeholder
            pass
        
        # Store the data
        self.indicators["economic_data"] = {
            "values": economic_data,
            "timestamp": datetime.now(),
            "interpretation": self._interpret_economic_data(economic_data)
        }
        
        return economic_data
    
    def _interpret_economic_data(self, economic_data):
        """
        Interpret economic data
        
        Args:
            economic_data (dict): Dictionary of economic data
            
        Returns:
            dict: Interpretation of economic data
        """
        interpretation = {}
        
        # Interpret inflation
        if "cpi" in economic_data:
            cpi_yoy = economic_data["cpi"]["yoy_change"]
            high_threshold = self.config["thresholds"]["inflation"]["high"]
            low_threshold = self.config["thresholds"]["inflation"]["low"]
            
            if cpi_yoy > high_threshold:
                interpretation["inflation"] = "high"
            elif cpi_yoy < low_threshold:
                interpretation["inflation"] = "low"
            else:
                interpretation["inflation"] = "moderate"
        
        # Interpret GDP growth
        if "gdp" in economic_data:
            gdp_qoq = economic_data["gdp"]["qoq_change"]
            
            if gdp_qoq < 0:
                interpretation["growth"] = "contracting"
            elif gdp_qoq < 1.0:
                interpretation["growth"] = "slow"
            elif gdp_qoq < 3.0:
                interpretation["growth"] = "moderate"
            else:
                interpretation["growth"] = "strong"
        
        # Interpret unemployment
        if "unemployment" in economic_data:
            unemployment = economic_data["unemployment"]["latest"]
            
            if unemployment < 4.0:
                interpretation["labor_market"] = "tight"
            elif unemployment < 6.0:
                interpretation["labor_market"] = "balanced"
            else:
                interpretation["labor_market"] = "loose"
        
        return interpretation
    
    def fetch_fed_minutes(self, use_mock_data=True):
        """
        Fetch and analyze recent Fed minutes
        
        Args:
            use_mock_data (bool): Whether to use mock data instead of actual scraping
            
        Returns:
            dict: Analysis of Fed minutes
        """
        # For demonstration purposes, we'll use mock data
        # In a real implementation, you would scrape and analyze actual Fed minutes
        if use_mock_data:
            # Mock data for demonstration
            fed_analysis = {
                "latest_meeting": "2025-03-20",
                "next_meeting": "2025-05-01",
                "rate_decision": "hold",
                "key_themes": [
                    "inflation concerns",
                    "labor market strength",
                    "global economic uncertainty"
                ],
                "hawkish_dovish_score": 0.2,  # Positive is hawkish, negative is dovish
                "rate_hike_probability": 0.3,
                "rate_cut_probability": 0.1
            }
        else:
            # Scrape and analyze actual Fed minutes
            # This would require more complex implementation
            # For now, we'll leave this as a placeholder
            pass
        
        # Store the analysis
        self.indicators["fed_minutes"] = {
            "analysis": fed_analysis,
            "timestamp": datetime.now()
        }
        
        return fed_analysis
    
    def rate_macro_environment(self):
        """
        Rate the macro environment based on all indicators
        
        Returns:
            dict: Rating of macro environment
        """
        # Ensure we have all necessary indicators
        if not all(k in self.indicators for k in ["vix", "treasury_yields", "economic_data"]):
            print("Missing indicators, cannot rate macro environment")
            return None
        
        # Initialize rating
        rating = {
            "risk_sentiment": None,
            "inflation_environment": None,
            "growth_outlook": None,
            "overall_environment": None,
            "timestamp": datetime.now()
        }
        
        # Determine risk sentiment
        vix_interp = self.indicators["vix"]["interpretation"]
        yield_curve_interp = self.indicators["treasury_yields"]["interpretation"]
        
        if vix_interp == "low_volatility" and yield_curve_interp != "inverted":
            rating["risk_sentiment"] = "risk_on"
        elif vix_interp == "high_volatility" or yield_curve_interp == "inverted":
            rating["risk_sentiment"] = "risk_off"
        else:
            rating["risk_sentiment"] = "neutral"
        
        # Determine inflation environment
        econ_interp = self.indicators["economic_data"]["interpretation"]
        
        if "inflation" in econ_interp:
            if econ_interp["inflation"] == "high":
                rating["inflation_environment"] = "inflationary"
            elif econ_interp["inflation"] == "low":
                rating["inflation_environment"] = "deflationary"
            else:
                rating["inflation_environment"] = "stable"
        
        # Determine growth outlook
        if "growth" in econ_interp:
            rating["growth_outlook"] = econ_interp["growth"]
        
        # Determine overall environment
        if rating["risk_sentiment"] == "risk_on" and rating["inflation_environment"] != "inflationary":
            rating["overall_environment"] = "bullish"
        elif rating["risk_sentiment"] == "risk_off" or rating["growth_outlook"] == "contracting":
            rating["overall_environment"] = "bearish"
        else:
            rating["overall_environment"] = "neutral"
        
        # Store the rating
        self.environment_rating = rating
        
        return rating
    
    def suggest_es_bias(self):
        """
        Suggest long/short bias for S&P 500 E-mini futures (ES)
        
        Returns:
            dict: Bias suggestion for ES
        """
        # Ensure we have environment rating
        if not self.environment_rating:
            print("Missing environment rating, cannot suggest ES bias")
            return None
        
        # Initialize bias
        bias = {
            "direction": None,
            "confidence": None,
            "rationale": [],
            "timestamp": datetime.now()
        }
        
        # Determine direction based on overall environment
        overall_env = self.environment_rating["overall_environment"]
        
        if overall_env == "bullish":
            bias["direction"] = "long"
            bias["confidence"] = "high"
            bias["rationale"].append("Overall macro environment is bullish")
        elif overall_env == "bearish":
            bias["direction"] = "short"
            bias["confidence"] = "high"
            bias["rationale"].append("Overall macro environment is bearish")
        else:
            # For neutral environment, look at additional factors
            
            # Check yield curve
            yield_curve = se
(Content truncated due to size limit. Use line ranges to read in chunks)