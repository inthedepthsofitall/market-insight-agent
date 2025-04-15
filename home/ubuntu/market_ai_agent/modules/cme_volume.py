"""
CME Volume/Open Interest Tracker for Market AI Agent

This module is responsible for:
1. Pulling open interest and volume data for ES contracts
2. Alerting if institutional activity spikes pre-FOMC, earnings, etc.
3. Detecting significant changes in market positioning
"""

import os
import json
import datetime
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class CMEVolumeTracker:
    def __init__(self, config_path=None):
        """
        Initialize the CME Volume/Open Interest Tracker
        
        Args:
            config_path (str): Path to configuration file
        """
        # Default configuration
        self.config = {
            "contracts": {
                "ES": {  # S&P 500 E-mini
                    "name": "E-mini S&P 500",
                    "exchange": "CME",
                    "data_url": "https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.volume.html"
                },
                "NQ": {  # Nasdaq E-mini
                    "name": "E-mini Nasdaq-100",
                    "exchange": "CME",
                    "data_url": "https://www.cmegroup.com/markets/equities/nasdaq/e-mini-nasdaq-100.volume.html"
                },
                "YM": {  # Dow E-mini
                    "name": "E-mini Dow",
                    "exchange": "CBOT",
                    "data_url": "https://www.cmegroup.com/markets/equities/dow/e-mini-dow.volume.html"
                }
            },
            "thresholds": {
                "volume_spike": 1.5,  # 50% above average
                "oi_change": 0.1,     # 10% change in open interest
                "alert_period": 7     # Days to look back for alerts
            },
            "economic_calendar": {
                "fomc_meetings": [
                    "2025-04-30",
                    "2025-06-11",
                    "2025-07-30",
                    "2025-09-17",
                    "2025-11-05",
                    "2025-12-17"
                ],
                "earnings_seasons": [
                    {"start": "2025-04-15", "end": "2025-05-15", "description": "Q1 2025 Earnings"},
                    {"start": "2025-07-15", "end": "2025-08-15", "description": "Q2 2025 Earnings"},
                    {"start": "2025-10-15", "end": "2025-11-15", "description": "Q3 2025 Earnings"},
                    {"start": "2026-01-15", "end": "2026-02-15", "description": "Q4 2025 Earnings"}
                ],
                "economic_releases": [
                    {"date": "2025-04-10", "description": "CPI Release"},
                    {"date": "2025-04-17", "description": "Initial Jobless Claims"},
                    {"date": "2025-04-25", "description": "GDP Release"},
                    {"date": "2025-05-03", "description": "Non-Farm Payrolls"}
                ]
            }
        }
        
        # Load custom configuration if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
                self.config.update(custom_config)
        
        # Initialize data storage
        self.volume_data = {}
        self.oi_data = {}
        self.alerts = []
    
    def fetch_cme_data(self, contract="ES", use_mock_data=True):
        """
        Fetch volume and open interest data for a specific contract
        
        Args:
            contract (str): Contract symbol (e.g., "ES" for S&P 500 E-mini)
            use_mock_data (bool): Whether to use mock data instead of actual scraping
            
        Returns:
            tuple: (volume_df, oi_df) DataFrames containing volume and open interest data
        """
        if contract not in self.config["contracts"]:
            print(f"Contract {contract} not found in configuration")
            return None, None
        
        if use_mock_data:
            # Generate mock data for demonstration
            # In a real implementation, you would scrape the CME website
            
            # Create date range for the past 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
            
            # Generate mock volume data
            base_volume = 2000000 if contract == "ES" else (1500000 if contract == "NQ" else 1000000)
            volume_data = []
            
            for date in date_range:
                # Add some randomness and a slight upward trend
                daily_volume = int(base_volume * (1 + 0.3 * np.random.randn() + 0.01 * (date - start_date).days))
                
                # Add a volume spike for FOMC meetings
                fomc_dates = [datetime.strptime(d, "%Y-%m-%d") for d in self.config["economic_calendar"]["fomc_meetings"]]
                for fomc_date in fomc_dates:
                    if abs((date - fomc_date).days) <= 1:  # Day before or day of FOMC
                        daily_volume = int(daily_volume * 1.8)  # 80% spike
                
                volume_data.append({
                    'date': date,
                    'contract': contract,
                    'volume': daily_volume,
                    'electronic_volume': int(daily_volume * 0.95),  # 95% electronic
                    'open_outcry_volume': int(daily_volume * 0.05)  # 5% open outcry
                })
            
            volume_df = pd.DataFrame(volume_data)
            
            # Generate mock open interest data
            base_oi = 3000000 if contract == "ES" else (2000000 if contract == "NQ" else 1500000)
            oi_data = []
            
            current_oi = base_oi
            for date in date_range:
                # Add some randomness and a slight trend
                daily_change = int(base_oi * 0.02 * np.random.randn())  # 2% random change
                current_oi += daily_change
                
                # Ensure OI doesn't go below a minimum threshold
                current_oi = max(current_oi, base_oi * 0.8)
                
                oi_data.append({
                    'date': date,
                    'contract': contract,
                    'open_interest': current_oi,
                    'change': daily_change
                })
            
            oi_df = pd.DataFrame(oi_data)
            
            # Store the data
            self.volume_data[contract] = volume_df
            self.oi_data[contract] = oi_df
            
            return volume_df, oi_df
        else:
            # In a real implementation, you would scrape the CME website
            # This would require more complex implementation with proper HTML parsing
            # For now, we'll leave this as a placeholder
            print("Real data scraping not implemented, using mock data instead")
            return self.fetch_cme_data(contract, use_mock_data=True)
    
    def detect_volume_spikes(self, contract="ES", lookback_period=10):
        """
        Detect volume spikes for a specific contract
        
        Args:
            contract (str): Contract symbol
            lookback_period (int): Number of days to look back for calculating average
            
        Returns:
            list: List of volume spike events
        """
        if contract not in self.volume_data:
            print(f"No volume data for contract {contract}")
            return []
        
        volume_df = self.volume_data[contract].copy()
        
        # Sort by date
        volume_df = volume_df.sort_values('date')
        
        # Calculate rolling average volume
        volume_df['avg_volume'] = volume_df['volume'].rolling(window=lookback_period, min_periods=1).mean()
        
        # Calculate volume ratio
        volume_df['volume_ratio'] = volume_df['volume'] / volume_df['avg_volume']
        
        # Detect spikes
        threshold = self.config["thresholds"]["volume_spike"]
        spike_df = volume_df[volume_df['volume_ratio'] > threshold].copy()
        
        # Format spike events
        spike_events = []
        for _, row in spike_df.iterrows():
            event = {
                'date': row['date'],
                'contract': contract,
                'volume': row['volume'],
                'avg_volume': row['avg_volume'],
                'ratio': row['volume_ratio'],
                'type': 'volume_spike'
            }
            spike_events.append(event)
        
        return spike_events
    
    def detect_oi_changes(self, contract="ES", threshold=None):
        """
        Detect significant open interest changes for a specific contract
        
        Args:
            contract (str): Contract symbol
            threshold (float): Threshold for significant change (default: from config)
            
        Returns:
            list: List of OI change events
        """
        if contract not in self.oi_data:
            print(f"No open interest data for contract {contract}")
            return []
        
        oi_df = self.oi_data[contract].copy()
        
        # Sort by date
        oi_df = oi_df.sort_values('date')
        
        # Calculate percentage change
        oi_df['pct_change'] = oi_df['change'] / oi_df['open_interest'].shift(1)
        
        # Use default threshold if not provided
        if threshold is None:
            threshold = self.config["thresholds"]["oi_change"]
        
        # Detect significant changes
        change_df = oi_df[abs(oi_df['pct_change']) > threshold].copy()
        
        # Format change events
        change_events = []
        for _, row in change_df.iterrows():
            event = {
                'date': row['date'],
                'contract': contract,
                'open_interest': row['open_interest'],
                'change': row['change'],
                'pct_change': row['pct_change'],
                'type': 'oi_change',
                'direction': 'increase' if row['change'] > 0 else 'decrease'
            }
            change_events.append(event)
        
        return change_events
    
    def check_economic_events(self, date):
        """
        Check if a date is near any significant economic events
        
        Args:
            date (datetime): Date to check
            
        Returns:
            list: List of nearby economic events
        """
        nearby_events = []
        date_str = date.strftime("%Y-%m-%d")
        
        # Check FOMC meetings
        for fomc_date in self.config["economic_calendar"]["fomc_meetings"]:
            days_diff = abs((date - datetime.strptime(fomc_date, "%Y-%m-%d")).days)
            if days_diff <= 3:  # Within 3 days
                nearby_events.append({
                    'type': 'FOMC Meeting',
                    'date': fomc_date,
                    'days_away': days_diff
                })
        
        # Check earnings seasons
        for season in self.config["economic_calendar"]["earnings_seasons"]:
            start_date = datetime.strptime(season["start"], "%Y-%m-%d")
            end_date = datetime.strptime(season["end"], "%Y-%m-%d")
            
            if start_date <= date <= end_date:
                nearby_events.append({
                    'type': 'Earnings Season',
                    'description': season["description"],
                    'start_date': season["start"],
                    'end_date': season["end"]
                })
            elif abs((date - start_date).days) <= 5:  # Within 5 days of start
                nearby_events.append({
                    'type': 'Upcoming Earnings Season',
                    'description': season["description"],
                    'start_date': season["start"],
                    'days_away': (start_date - date).days
                })
        
        # Check economic releases
        for release in self.config["economic_calendar"]["economic_releases"]:
            release_date = datetime.strptime(release["date"], "%Y-%m-%d")
            days_diff = abs((date - release_date).days)
            
            if days_diff <= 2:  # Within 2 days
                nearby_events.append({
                    'type': 'Economic Release',
                    'description': release["description"],
                    'date': release["date"],
                    'days_away': days_diff
                })
        
        return nearby_events
    
    def generate_alerts(self, contracts=None):
        """
        Generate alerts for all contracts
        
        Args:
            contracts (list): List of contract symbols to check (default: all in config)
            
        Returns:
            list: List of alerts
        """
        if contracts is None:
            contracts = list(self.config["contracts"].keys())
        
        all_alerts = []
        
        for contract in contracts:
            # Fetch data if not already available
            if contract not in self.volume_data or contract not in self.oi_data:
                self.fetch_cme_data(contract)
            
            # Detect volume spikes
            volume_spikes = self.detect_volume_spikes(contract)
            
            # Detect OI changes
            oi_changes = self.detect_oi_changes(contract)
            
            # Combine events
            events = volume_spikes + oi_changes
            
            # Sort by date
            events.sort(key=lambda x: x['date'], reverse=True)
            
            # Filter to recent events
            alert_period = self.config["thresholds"]["alert_period"]
            cutoff_date = datetime.now() - timedelta(days=alert_period)
            recent_events = [e for e in events if e['date'] > cutoff_date]
            
            # Check for economic events
            for event in recent_events:
                economic_events = self.check_economic_events(event['date'])
                event['economic_events'] = economic_events
                
                # Create alert message
                alert_message = self._create_alert_message(event)
                
                # Add to alerts
                alert = {
                    'date': event['date'],
                    'contract': contract,
                    'event_type': event['type'],
                    'message': alert_message,
                    'details': event,
                    'economic_context': economic_events
                }
                
                all_alerts.append(alert)
        
        # Store alerts
        self.alerts = all_alerts
        
        return all_alerts
    
    def _create_alert_message(self, event):
        """
        Create alert message for an event
        
        Args:
            event (dict): Event dictionary
            
        Returns:
            str: Alert message
        """
        contract_name = self.config["contracts"][event['contract']]["name"]
        date_str = event['date'].strftime("%Y-%m-%d")
        
        if event['type'] == 'volume_spike':
            message = f"{contract_name} volume spike detected on {date_str}: "
            message += f"{event['volume']:,} contracts traded "
            message += f"({event['ratio']:.1f}x average)"
            
            if event['economic_events']:
                context = event['economic_events'][0]
                if context['type'] == 'FOMC Meeting':
                    message += f" - {context['days_away']} days from FOMC meeting"
                elif context['type'] == 'Earnings Season':
                    message += f" - During {context['description']}"
                elif context['type'] == 'Economic Release':
                    message += f" - Near {context['description']}"
        
        elif event['type'] == 'oi_change':
            direction = "increase" if event['change'] > 0 else "decrease"
  
(Content truncated due to size limit. Use line ranges to read in chunks)