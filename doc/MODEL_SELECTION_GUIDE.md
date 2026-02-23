# OpenAI Model Selection Guide

## Current Status
Your bot is configured to use **`gpt-4o-mini`** (line 22 in `config/__init__.py`), which is excellent for cost optimization.

## Available Models & Pricing (as of 2024)

### 🟢 Cheapest & Effective: `gpt-4o-mini` ⭐ RECOMMENDED
- **Cost**: ~$0.00015 / 1K input tokens, $0.0006 / 1K output tokens
- **Speed**: Very fast
- **Quality**: 90% of GPT-4's capability, perfect for social media
- **Best for**: Tweet generation, replies, DM responses, threads
- **Tradeoff**: Slightly less nuanced reasoning than full GPT-4
- **Example cost**: 1000 tweets = ~$0.60-$1.50

### 🟡 Budget Alternative: `gpt-3.5-turbo`
- **Cost**: ~$0.0005 / 1K input tokens, $0.0015 / 1K output tokens
- **Speed**: Fastest
- **Quality**: 80% of GPT-4's capability
- **Best for**: High-volume operations where speed matters most
- **Tradeoff**: Older model, sometimes generates less creative content
- **Example cost**: 1000 tweets = ~$1.50-$2.00

### 🟣 Balanced: `gpt-4-turbo`
- **Cost**: ~$0.01 / 1K input tokens, $0.03 / 1K output tokens
- **Speed**: Moderate
- **Quality**: 99% of full GPT-4
- **Best for**: When you need premium quality but more affordable than GPT-4
- **Tradeoff**: More expensive than mini/3.5-turbo
- **Example cost**: 1000 tweets = ~$30-$40

### 🔴 Premium: `gpt-4`
- **Cost**: ~$0.03 / 1K input tokens, $0.06 / 1K output tokens
- **Speed**: Slower
- **Quality**: Best available
- **Best for**: Mission-critical responses, complex reasoning
- **Tradeoff**: 100x more expensive than gpt-4o-mini
- **Example cost**: 1000 tweets = ~$90-$120

### ❌ NOT Available (yet): `gpt-5`
- Currently in research/beta phase
- No public API access yet
- Expected sometime in 2025-2026
- When available, likely similar to GPT-4 pricing or higher

## How to Configure

### Option 1: Use Environment Variable (Recommended)
Add to your `.env` file:
```bash
OPENAI_MODEL=gpt-4o-mini  # Default, already optimal
```

Then restart your bot. The configuration automatically loads from `.env`.

### Option 2: Change Default in Code
Edit `config/__init__.py` line 22:
```python
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')  # Change fallback here
```

### Option 3: Set System-Wide (macOS)
```bash
export OPENAI_MODEL=gpt-4o-mini
python main.py
```

## Cost Breakdown for Your Operations

Assuming ~100 operations per day (likes, retweets, replies, tweets):

| Model | Daily Cost | Monthly Cost | Annual Cost |
|-------|-----------|-------------|-----------|
| gpt-4o-mini | ~$0.10 | ~$3 | ~$36 |
| gpt-3.5-turbo | ~$0.30 | ~$9 | ~$108 |
| gpt-4-turbo | ~$3.00 | ~$90 | ~$1080 |
| gpt-4 | ~$10.00 | ~$300 | ~$3600 |

## Recommendation

**Use `gpt-4o-mini` (current default)** because:
1. ✅ Cheapest option available
2. ✅ Still very high quality for social media
3. ✅ OpenAI's recommended model for most use cases
4. ✅ Perfect balance of cost and capability
5. ✅ Fastest besides gpt-3.5-turbo

Your tweets, replies, and DM responses will be nearly indistinguishable from GPT-4, but at 1/100th the cost.

## Monitor Your Usage

Track API costs in OpenAI dashboard:
1. Visit https://platform.openai.com/account/usage/overview
2. Set date range to current month
3. Check actual spending vs. estimates

## Pro Tips

1. **Caching**: For frequently asked questions, implement response caching to reduce API calls
2. **Batching**: Group multiple generations together if possible
3. **Local Models**: Consider Ollama/LLaMA for entirely free local generation (but requires GPU)
4. **Fallbacks**: If API is down, use simple templates or cached responses

## Implementation in Your Code

All AI operations automatically use the configured model:
- `operations/ai_operation.py` - Tweet/reply/thread generation
- `operations/dm_operation.py` - DM responses
- `operations/analytics_operation.py` - Sentiment analysis

Change model in one place (`.env` or `config/__init__.py`), all operations use it.

---

**Status**: ✅ Already optimized with `gpt-4o-mini`  
**Action Required**: None (unless you want to try a different model)  
**Cost for 100 AI ops/day**: ~$3/month with current configuration
