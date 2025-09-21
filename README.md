# 🎧 AI-Powered Podcast Automation

> Automatically transcribe, translate, summarize, and organize your favorite podcasts using Claude AI

A comprehensive automation system that processes podcast RSS feeds, extracts meaningful insights, and creates structured summaries with memorable quotes. Supports multiple languages with automatic translation to English.

## ✨ Features

- **🌍 Multilingual Support**: Auto-detects and translates German, French, Spanish, and 15+ languages
- **🤖 AI-Powered Processing**: Uses Claude Sonnet 4 for high-quality summaries and quote extraction
- **📝 Smart Summaries**: Educational format with key sections, lessons, and reflection questions
- **💬 Inline Quote Integration**: Embeds relevant quotes directly within summary sections
- **📑 Chapter Extraction**: Creates timestamped chapters for episodes over 45 minutes
- **🏷️ Auto-Tagging**: Generates topical tags and combines with your custom feed tags
- **📊 Notion Integration**: Pushes summaries to Notion database with full metadata
- **⏰ Cron Automation**: Runs automatically every 2 hours to catch new episodes
- **🎯 Duplicate Detection**: Tracks processed episodes to avoid reprocessing

## 🛠️ How It Works

1. **Feed Monitoring**: Checks RSS feeds for new episodes
2. **Audio Download**: Downloads MP3 files locally
3. **Transcription**: Uses Whisper AI with automatic language detection
4. **Translation**: Translates non-English content to English using Claude
5. **Quote Integration**: Embeds memorable quotes directly in relevant sections
6. **Chapter Creation**: Generates timestamped chapters for long episodes (45+ minutes)
7. **Summarization**: Creates educational summaries with Claude Sonnet 4
8. **Auto-Tagging**: Generates relevant topic tags
9. **Notion Publishing**: Creates formatted pages with metadata
10. **Progress Tracking**: Marks episodes as processed

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

Set up a cron job to run every 2 hours:

```bash
crontab -e
# Add this line:
0 */2 * * * /path/to/your/run_cron.sh
```

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
│   ├── extract_chapters.py  # Chapter extraction with timestamps
│   ├── summarise_with_quotes.py  # Enhanced summarization
│   └── push_to_notion.py    # Notion integration
├── config/
│   ├── feeds.json           # Your podcast subscriptions
│   └── feeds.example.json   # Example configuration
├── data/                    # Local storage (gitignored)
│   ├── audio/              # Downloaded MP3 files
│   ├── transcripts/        # Original & translated transcripts
│   └── summaries/          # Final summaries & quotes
└── logs/                   # Execution logs (gitignored)
```

## 🌍 Language Support

**Primary Testing**: English, German

**Full Support**: French, Spanish, Italian, Portuguese, Dutch, Polish, Russian, Japanese, Korean, Chinese (Simplified/Traditional), Arabic, Hindi

**Process**: Automatic language detection → transcription in original language → translation to English → summarization

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
- **Episode Chapters**: Timestamped sections for long episodes (45+ minutes)
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