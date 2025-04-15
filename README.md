# Market AI Agent

A modular Python-based AI agent that runs daily before market open to analyze financial news, sentiment, and market data.

## Overview

The Market AI Agent is a comprehensive system that:

1. Scrapes and analyzes financial news from major sources
2. Tracks macro economic indicators and sentiment
3. Monitors futures volume and open interest
4. Cross-checks professional news sentiment against social media
5. Generates detailed daily reports with actionable insights

## Features

### News & Sentiment Module
- Scrapes news from CNBC, Bloomberg, CoinDesk, WSJ
- Uses NLP to analyze sentiment per article
- Extracts tickers, sectors, crypto tokens, and macro themes
- Prioritizes items from a personal watchlist
- Outputs suggested positions with supporting rationale

### Macro Sentiment Analyzer
- Processes key macro indicators (VIX, CPI, PPI, Treasury Yields, etc.)
- Rates the macro environment (risk-on, risk-off, inflationary, deflationary)
- Suggests long/short bias for S&P 500 E-mini futures (ES)

### CME Volume/Open Interest Tracker
- Pulls open interest and volume data for ES contracts
- Alerts if institutional activity spikes pre-FOMC, earnings, etc.

### Sentiment Cross-check Module
- Analyzes financial Twitter, Reddit, and StockTwits sentiment
- Identifies if social sentiment confirms or contradicts professional news flow

### Summary Report Generation
- Compiles all insights into a markdown or HTML file
- Sections for top bullish/bearish tickers, macro outlook, institutional flow, and sentiment divergences
- Email delivery option

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/market_ai_agent.git
cd market_ai_agent
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Configure the system by editing `config.json`

## Usage

### Basic Usage

Run the full system:
```bash
python main.py --config config.json
```

Run a specific module:
```bash
python main.py --config config.json --module news
```

Available modules:
- `news`: News & Sentiment Module
- `macro`: Macro Sentiment Analyzer
- `cme`: CME Volume/Open Interest Tracker
- `sentiment`: Sentiment Cross-check Module
- `report`: Summary Report Generator
- `all`: Run all modules (default)

### Configuration

The `config.json` file contains all settings for the Market AI Agent. Key sections include:

- General settings (data directories, mock data toggle)
- Module-specific settings (enable/disable, thresholds, sources)
- Email delivery configuration

See the comments in `config.json` for detailed explanations of each setting.

### Scheduling

For instructions on how to schedule the Market AI Agent to run daily before market open, see [SCHEDULING.md](SCHEDULING.md).

## Project Structure

```
market_ai_agent/
├── main.py                 # Main entry point
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── SCHEDULING.md           # Scheduling instructions
├── README.md               # This file
├── modules/                # Module implementations
│   ├── news_sentiment.py   # News & Sentiment Module
│   ├── macro_sentiment.py  # Macro Sentiment Analyzer
│   ├── cme_volume.py       # CME Volume/OI Tracker
│   ├── sentiment_crosscheck.py # Sentiment Cross-check Module
│   └── report_generator.py # Summary Report Generator
├── data/                   # Data storage (created at runtime)
├── reports/                # Generated reports (created at runtime)
└── logs/                   # Log files (created at runtime)
```

## Customization

### Watchlists

Edit the `watchlist` section in `config.json` to customize which stocks, crypto tokens, and sectors you want to track.

### News Sources

Add or remove news sources in the `sources` section of the News & Sentiment Module configuration.

### Report Format

Choose between HTML and Markdown formats for the generated reports by setting the `format` option in the Report Generator configuration.

## Troubleshooting

See the [SCHEDULING.md](SCHEDULING.md) file for troubleshooting tips and common issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [newspaper3k](https://newspaper.readthedocs.io/) for news scraping
- [NLTK](https://www.nltk.org/) and [VADER](https://github.com/cjhutto/vaderSentiment) for sentiment analysis
- [Transformers](https://huggingface.co/transformers/) for advanced NLP
- [Pandas](https://pandas.pydata.org/) for data processing
- [Matplotlib](https://matplotlib.org/) for visualization
