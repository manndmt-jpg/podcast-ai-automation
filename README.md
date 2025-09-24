# 🎧 AI-Powered Podcast Automation

> Automatically transcribe, translate, summarize, and organize your favorite podcasts using Claude AI

A comprehensive automation system that processes podcast RSS feeds, extracts meaningful insights, and creates structured summaries with memorable quotes. Supports multiple languages with automatic translation to English.

## ✨ Features

- **🌍 Multilingual Support**: Auto-detects and translates German, French, Spanish, and 15+ languages
- **🤖 AI-Powered Processing**: Uses Claude Sonnet 4 for high-quality summaries and quote extraction
- **📝 Smart Summaries**: Educational format with key sections, lessons, and reflection questions
- **💬 Inline Quote Integration**: Embeds relevant quotes directly within summary sections
- **📑 Chapter Extraction**: Creates topic-based chapter structure for episodes over 45 minutes
- **🏷️ Auto-Tagging**: Generates topical tags and combines with your custom feed tags
- **📊 Notion Integration**: Pushes summaries to Notion database with full metadata
- **💰 Cost Tracking**: Monitors AI service costs (Claude only - Whisper is free local) with detailed breakdowns
- **⏰ Cron Automation**: Runs automatically every 2 hours to catch new episodes
- **🎯 Duplicate Detection**: Tracks processed episodes to avoid reprocessing
- **🧪 Evaluation Suite**: 9 comprehensive monitoring scripts for health, quality, and performance analysis
- **📈 Automated Monitoring**: Daily evaluation runs with detailed logging and trend analysis

## 🛠️ How It Works

1. **Feed Monitoring**: Checks RSS feeds for new episodes
2. **Audio Download**: Downloads MP3 files locally
3. **Transcription**: Uses local faster-whisper with automatic language detection (FREE)
4. **Translation**: Translates non-English content to English using Claude
5. **Quote Integration**: Embeds memorable quotes directly in relevant sections
6. **Chapter Creation**: Generates topic-based chapter structure for long episodes (45+ minutes)
7. **Summarization**: Creates educational summaries with Claude Sonnet 4
8. **Auto-Tagging**: Generates relevant topic tags
9. **Cost Tracking**: Logs detailed AI service costs and usage
10. **Notion Publishing**: Creates formatted pages with metadata
11. **Progress Tracking**: Marks episodes as processed

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- [Anthropic API key](https://console.anthropic.com/)
- [Notion integration](https://developers.notion.com/) (optional)
- macOS/Linux (Windows with WSL)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/podcast-automation.git
   cd podcast-automation
   ```

2. **Install dependencies**
   ```bash
   pip install anthropic faster-whisper feedparser langdetect
   # For Notion integration:
   pip install notion-client
   ```

3. **Set up configuration**
   ```bash
   # Copy example files
   cp .env.example .env
   cp config/feeds.example.json config/feeds.json
   cp run_cron.example.sh run_cron.sh

   # Edit with your settings
   nano .env
   nano config/feeds.json
   nano run_cron.sh
   ```

4. **Configure environment variables**
   ```bash
   # Required
   ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE"

   # Optional - for Notion integration
   NOTION_TOKEN="ntn_YOUR_TOKEN_HERE"
   NOTION_DATABASE_ID="YOUR_DATABASE_ID"
   ```

5. **Test the setup**
   ```bash
   python3 automation/pipeline.py
   ```

### Adding Podcasts

Edit `config/feeds.json`:

```json
[
  {
    "name": "Your Favorite Podcast",
    "rss": "https://example.com/podcast/rss",
    "tags": ["technology", "AI", "business"]
  }
]
```

### Scheduling Automation

Set up cron jobs for automation and monitoring:

```bash
crontab -e
# Add these lines:
0 */2 * * * /path/to/your/run_cron.sh
0 10 * * * cd /path/to/your/project && python3 evals/eval_runner.py --daily >> logs/eval_runner.log 2>&1
```

The first job runs the main pipeline every 2 hours, the second runs daily evaluations at 10 AM.

## 📁 Project Structure

```
podcast-automation/
├── automation/
│   └── pipeline.py          # Main orchestration script
├── scripts/
│   ├── fetch_feed.py        # RSS feed parsing
│   ├── download_audio.py    # MP3 downloading
│   ├── transcribe.py        # Whisper transcription
│   ├── translate.py         # Claude translation
│   ├── extract_quotes.py    # Quote extraction (standalone)
│   ├── extract_chapters.py  # Chapter structure extraction
│   ├── summarise_with_quotes.py  # Enhanced summarization
│   └── push_to_notion.py    # Notion integration
├── utils/
│   └── cost_tracker.py      # Cost tracking and analysis
├── evals/                   # Evaluation & monitoring suite
│   ├── eval_runner.py       # Centralized evaluation runner
│   ├── feed_health.py       # RSS feed health monitoring
│   ├── quality_check.py     # Content quality analysis
│   ├── processing_stats.py  # Performance metrics & efficiency
│   ├── view_costs.py        # Enhanced cost reporting
│   ├── duplicate_analysis.py # Duplicate episode detection
│   ├── view_eval_logs.py    # Evaluation log viewer
│   ├── explain_warnings.py  # Issue troubleshooting helper
│   └── test_cost_tracking.py # Cost tracking validation
├── config/
│   ├── feeds.json           # Your podcast subscriptions
│   └── feeds.example.json   # Example configuration
├── data/                    # Local storage (gitignored)
│   ├── audio/              # Downloaded MP3 files
│   ├── transcripts/        # Original & translated transcripts
│   └── summaries/          # Final summaries & quotes
└── logs/                   # Execution logs (gitignored)
    ├── cron.log            # Pipeline execution logs
    ├── costs.log           # Detailed cost breakdown
    ├── daily_costs.json    # Daily/monthly cost totals
    ├── eval_runner.log     # Daily evaluation results
    └── eval_*.log          # Individual evaluation logs
```

## 🌍 Language Support

**Primary Testing**: English, German

**Full Support**: French, Spanish, Italian, Portuguese, Dutch, Polish, Russian, Japanese, Korean, Chinese (Simplified/Traditional), Arabic, Hindi

**Process**: Automatic language detection → transcription in original language → translation to English → summarization

## 🧪 Evaluation Suite

The system includes comprehensive monitoring and evaluation scripts to track health, quality, and performance:

### **Available Evaluations:**

```bash
# Daily health check
python3 evals/feed_health.py

# Content quality analysis
python3 evals/quality_check.py --recent 5

# Performance metrics
python3 evals/processing_stats.py --days 7

# Cost analysis
python3 evals/view_costs.py

# Duplicate detection
python3 evals/duplicate_analysis.py

# Run all evaluations
python3 evals/eval_runner.py --daily
```

### **Key Features:**
- **Feed Health**: Monitor RSS feed availability and content validation
- **Quality Analysis**: Check transcript/summary quality and detect issues
- **Performance Stats**: Analyze processing efficiency and success rates
- **Cost Monitoring**: Track AI service usage and spending patterns
- **Duplicate Detection**: Identify and resolve duplicate processing issues
- **Automated Logging**: Daily evaluation results with trend analysis

See `evals/README.md` for detailed documentation and usage examples.

## 💰 Cost Tracking

The system automatically tracks costs for all AI services used:

### **Tracked Services:**
- **Whisper Transcription**: FREE (using local faster-whisper)
- **Claude Translation**: Haiku model (~$0.00025 per 1K tokens)
- **Claude Summarization**: Sonnet 4 model (~$0.015 per 1K input tokens)
- **Claude Auto-tagging**: Haiku model for tag generation

### **Cost Reports:**

```bash
# View detailed cost breakdown
python3 evals/view_costs.py

# View last 10 episodes
python3 evals/view_costs.py --tail 10

# View cost summary
python3 evals/view_costs.py --summary
```

### **Example Output:**
```
=== AI Cost Summary ===
Total Today: $2.45
Total This Month: $47.83

Recent Episodes:
- Lenny's Podcast: AI Leadership ($0.47)
  - Whisper: $0.00 (70.3 min, local)
  - Translation: $0.08 (Haiku)
  - Summary: $0.35 (Sonnet-4)
  - Tagging: $0.04 (Haiku)

Average per episode: $0.73
Estimated monthly: $54.75 (75 episodes)
```

### **Cost Files:**
- `logs/costs.log` - Detailed per-operation costs
- `logs/daily_costs.json` - Daily/monthly aggregates

## 📊 System Monitoring & Evaluation

The system includes comprehensive evaluation tools to monitor pipeline health, quality, and performance:

### **Evaluation Suite:**

```bash
# Run daily health checks
python3 evals/eval_runner.py --daily

# Weekly comprehensive analysis
python3 evals/eval_runner.py --weekly

# View evaluation results and trends
python3 evals/view_eval_logs.py summary
```

### **Available Evaluations:**
- **Feed Health**: Monitor RSS feeds for availability and content issues
- **Quality Check**: Analyze transcript and summary quality metrics
- **Performance Stats**: Track processing efficiency and success rates
- **Duplicate Detection**: Find and resolve duplicate episode processing
- **Cost Analysis**: Monitor AI service usage and spending trends

### **Evaluation Logs:**
- `logs/eval_health.log` - Feed availability and content validation
- `logs/eval_quality.log` - Content quality analysis results
- `logs/eval_performance.log` - Processing statistics and efficiency metrics
- `logs/eval_duplicates.log` - Duplicate detection and cleanup suggestions
- `logs/eval_summary.json` - Historical trends and aggregated metrics

### **Understanding Warnings:**

```bash
# Explain any warning you encounter
python3 evals/explain_warnings.py date_parsing

# Auto-detect warning type from message
python3 evals/explain_warnings.py "Could not parse date..."

# See all possible warning types
python3 evals/explain_warnings.py
```

### **Individual Evaluation Scripts:**

```bash
# Check RSS feed health
python3 evals/feed_health.py --verbose

# Analyze content quality
python3 evals/quality_check.py --recent 10

# Review processing performance
python3 evals/processing_stats.py --days 7

# Check for duplicates
python3 evals/duplicate_analysis.py --cleanup
```

For detailed documentation on all evaluation tools, see `evals/README.md`.

## 💬 Quote Integration

Quotes are embedded directly within relevant sections:

```markdown
### Product Development Strategy

Building on the discussion of market validation, the conversation shifts to execution strategies. The key insight here revolves around speed versus perfection.

- Focus on rapid iteration cycles
- Prioritize user feedback over internal opinions
- Build the minimum viable solution first

**"The biggest mistake founders make is building features nobody wants"** —**Guest Name**

**Why this matters:** Speed to market often trumps perfect execution in competitive landscapes.
```

## 📊 Example Output

Your summaries will include:

- **Episode Overview**: Comprehensive 1-minute summary (200-300 words)
- **Episode Structure**: Topic-based chapter outline for long episodes (45+ minutes)
- **Inline Quotes**: Memorable quotes embedded directly in relevant sections
- **Key Sections**: Detailed breakdown with inline quotes and smooth transitions
- **Top 5 Lessons**: Actionable takeaways
- **Reflection Questions**: For deeper learning

## 🔧 Customization

### Modify Summary Style

Edit the prompt in `scripts/summarise_with_quotes.py` to change the summary format.

### Add New Languages

The system automatically handles 15+ languages. To add custom language handling, modify `scripts/translate.py`.

### Custom Quote Integration

Modify the inline quote instructions in the `build_prompt()` function within `scripts/summarise_with_quotes.py`.

### Cost Tracking Configuration

Adjust cost rates in `utils/cost_tracker.py` if API pricing changes. View tracked costs with `python3 evals/view_costs.py`.

### Different AI Models

Change models in the respective scripts:
- Transcription: Modify `model_size` in `scripts/transcribe.py`
- Translation: Change model in `scripts/translate.py`
- Summarization: Update `MODEL` in `scripts/summarise_with_quotes.py`

## 🐛 Troubleshooting

### Common Issues

**API Authentication Errors**
- Ensure your Anthropic API key starts with `sk-ant-api03-`
- Check that environment variables are loaded correctly

**Whisper Installation Issues**
```bash
pip install --upgrade faster-whisper
# On Apple Silicon Macs:
pip install --upgrade torch torchvision torchaudio
```

**RSS Feed Not Found**
- Verify RSS URLs are accessible
- Check for typos in `feeds.json`
- Some feeds may require user-agent headers

**Notion Integration Issues**
- Ensure your Notion integration has write permissions
- Verify database ID is correct
- Check that all required properties exist in your database

### Getting Help

1. Check the [Issues](https://github.com/yourusername/podcast-automation/issues) page
2. Enable verbose logging by adding debug prints
3. Test individual scripts in isolation

## 📋 Requirements

See requirements in the installation section. Key dependencies:

- `anthropic` - Claude AI API
- `faster-whisper` - Local speech-to-text
- `feedparser` - RSS feed parsing
- `langdetect` - Language detection
- `notion-client` - Notion integration (optional)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is designed for personal and educational use. Please respect:

- **Podcast creators' rights**: Only process content you have the right to use
- **Terms of service**: Comply with podcast platforms' terms
- **Fair use**: Use summaries for personal learning, not redistribution
- **API limits**: Respect rate limits for all services used

The creators of this tool are not responsible for how it is used. Please use responsibly and in accordance with applicable laws and terms of service.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com/) for Claude AI
- [OpenAI](https://openai.com/) for Whisper
- [Notion](https://notion.so/) for the excellent API
- The podcast community for creating amazing content

---

**Made with ❤️ for podcast enthusiasts and AI automation lovers**