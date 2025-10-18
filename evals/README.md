# 📊 Evaluation Scripts

This directory contains evaluation scripts to monitor and analyze the podcast processing pipeline performance, quality, and health.

## Available Scripts

### 💰 `view_costs.py` - Cost Analysis
Monitor AI service costs and usage patterns.

```bash
# View cost summary
python3 evals/view_costs.py

# View last 10 episodes
python3 evals/view_costs.py --tail 10
```

**Output**: Daily/monthly cost summaries, per-episode breakdowns, recent processing costs.

### 🧪 `test_cost_tracking.py` - Cost Tracking Test
Test the cost tracking functionality with sample data.

```bash
python3 evals/test_cost_tracking.py
```

**Output**: Validation that cost tracking is working correctly.

### 📝 `quality_check.py` - Content Quality Analysis
Analyze transcript and summary quality, detect potential issues.

```bash
# Analyze all episodes
python3 evals/quality_check.py

# Analyze recent 5 episodes
python3 evals/quality_check.py --recent 5
```

**Features**:
- Transcript quality metrics (word count, duration, repeated phrases)
- Summary structure analysis (sections, quotes, formatting)
- Metadata completeness checking
- Issue detection and recommendations

### 🏥 `feed_health.py` - RSS Feed Health Monitor
Monitor RSS feeds for availability and content issues.

```bash
# Basic health check
python3 evals/feed_health.py

# Verbose output with details
python3 evals/feed_health.py --verbose
```

**Features**:
- RSS feed availability checking
- Content validation (MP3 URLs, titles, dates)
- Processing status for each feed
- Feed-specific issue detection

### ⚡ `processing_stats.py` - Processing Efficiency Analysis
Analyze pipeline performance and identify bottlenecks.

```bash
# Analyze last 7 days
python3 evals/processing_stats.py

# Analyze last 30 days
python3 evals/processing_stats.py --days 30
```

**Features**:
- Success rates and error analysis
- Processing times and efficiency metrics
- Feed activity patterns
- Performance recommendations
- Cost analysis integration

### 🔍 `duplicate_analysis.py` - Duplicate Detection
Analyze the seen.json file for potential duplicate processing issues.

```bash
# Basic duplicate analysis
python3 evals/duplicate_analysis.py

# Include cleanup suggestions
python3 evals/duplicate_analysis.py --cleanup
```

**Features**:
- Exact and near-duplicate episode detection
- Cross-feed duplicate identification
- Episode ID pattern analysis
- Cleanup recommendations

### 🚀 `eval_runner.py` - Centralized Evaluation Runner
Run all evaluations and log results to dedicated files (like costs.log).

```bash
# Daily evaluation suite
python3 evals/eval_runner.py --daily

# Weekly comprehensive check
python3 evals/eval_runner.py --weekly

# Manual run (all evaluations)
python3 evals/eval_runner.py
```

**Features**:
- Runs all evaluation scripts automatically
- Logs results to dedicated files in `logs/eval_*.log`
- Tracks trends over time in `logs/eval_summary.json`
- Provides consolidated summary of issues

### 📋 `view_eval_logs.py` - Evaluation Log Viewer
View logged evaluation results and analyze trends.

```bash
# List available logs
python3 evals/view_eval_logs.py

# View summary with trends
python3 evals/view_eval_logs.py summary

# View specific log type
python3 evals/view_eval_logs.py health
```

**Features**:
- Easy log viewing with trend analysis
- Historical performance tracking
- Issue frequency analysis
- Recent entries with --tail option

### ❓ `explain_warnings.py` - Warning Explanation Helper
Understand what evaluation warnings mean and how to fix them.

```bash
# Show all warning types
python3 evals/explain_warnings.py

# Explain specific warning
python3 evals/explain_warnings.py date_parsing

# Auto-detect from warning text
python3 evals/explain_warnings.py "Could not parse date..."
```

**Features**:
- Detailed explanations of all warning types
- Impact assessment (Low/Medium/High)
- Specific solutions for each warning type
- Auto-detection from warning text

## Recommended Usage

### Daily Monitoring
```bash
# Quick health check
python3 evals/feed_health.py
python3 evals/quality_check.py --recent 3
```

### Weekly Analysis
```bash
# Comprehensive analysis
python3 evals/processing_stats.py --days 7
python3 evals/view_costs.py
python3 evals/duplicate_analysis.py
```

### Monthly Review
```bash
# Full system evaluation
python3 evals/processing_stats.py --days 30
python3 evals/quality_check.py
python3 evals/duplicate_analysis.py --cleanup
```

## Integration Tips

### Cron Integration
Add to your crontab for automated monitoring:

```bash
# Daily health check at 8 AM
0 8 * * * cd /path/to/project && python3 evals/feed_health.py >> logs/health_check.log 2>&1

# Weekly analysis on Sundays at 9 AM  
0 9 * * 0 cd /path/to/project && python3 evals/processing_stats.py --days 7 >> logs/weekly_analysis.log 2>&1
```

### Alerting
Pipe outputs to monitoring systems:

```bash
# Check for issues and send alerts
python3 evals/processing_stats.py --days 1 | grep -E "❌|⚠️" && echo "Issues detected!" | mail -s "Podcast Pipeline Alert" admin@example.com
```

### Troubleshooting Workflow

1. **Performance Issues**: Run `processing_stats.py` to identify bottlenecks
2. **Quality Problems**: Use `quality_check.py` to find content issues  
3. **Feed Problems**: Check `feed_health.py` for RSS feed issues
4. **Duplicate Issues**: Analyze with `duplicate_analysis.py --cleanup`
5. **Cost Concerns**: Monitor with `view_costs.py`

## Understanding Output

### Status Icons
- ✅ **Good**: No issues detected
- ⚠️ **Warning**: Minor issues that should be monitored
- ❌ **Error**: Critical issues requiring attention
- 🔍 **Investigation**: Suspicious patterns detected

### Common Issues

**High Skip Rate**: Most episodes are being skipped (already processed)
- *Normal*: Indicates feeds aren't publishing new content frequently
- *Problem*: May indicate episode ID detection issues

**Missing Quotes**: Summaries contain no quotes
- Check if transcripts are in correct format
- Verify quote extraction is working properly

**Feed Errors**: RSS feeds returning errors
- Check feed URLs are still valid
- Verify network connectivity
- Some feeds may have temporary issues

**High Costs**: Processing costs are higher than expected
- Review which episodes are using expensive models
- Check if translation is needed for more episodes
- Consider optimizing model usage

## Adding New Evaluations

To add a new evaluation script:

1. Create the script in this directory
2. Follow the naming convention: `descriptive_name.py`
3. Include proper argument parsing and help text
4. Add documentation to this README
5. Make script executable: `chmod +x script_name.py`
6. Test thoroughly before deploying

## Troubleshooting

### Common Script Issues

**ImportError**: Make sure you're running from project root
```bash
cd /path/to/podcast_summary_project
python3 evals/script_name.py
```

**File Not Found**: Check that data directories exist
```bash
mkdir -p data/summaries data/transcripts logs
```

**Permission Denied**: Make scripts executable
```bash
chmod +x evals/*.py
```

---

*For more information about the podcast processing pipeline, see the main project README.*