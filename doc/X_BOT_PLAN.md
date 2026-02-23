# X (Twitter) Bot Growth Plan - Organic Follower Strategy

## Table of Contents
1. [Setup & Prerequisites](#setup--prerequisites)
2. [Phase 1: Foundation (Week 1)](#phase-1-foundation-week-1)
3. [Phase 2: Core Operations (Week 2-3)](#phase-2-core-operations-week-2-3)
4. [Phase 3: AI Integration (Week 4)](#phase-3-ai-integration-week-4)
5. [Available X API Operations](#available-x-api-operations)
6. [Bot Algorithm](#bot-algorithm)
7. [Implementation Steps](#implementation-steps)

---

## Setup & Prerequisites

### 1. X Developer Account Setup
```
1. Go to console.x.com
2. Sign in with the existing X account
3. Create a new app (or use existing)
4. Set app type: "Automated App / Bot"
5. Generate credentials:
   - API Key & Secret (OAuth 1.0a)
   - Access Token & Secret (user-context)
   - Bearer Token (app-only)
6. Request elevated access if needed
7. Enable Read + Write + DM permissions
8. Store credentials securely in .env file
```

### 2. Required Permissions
- **OAuth 2.0** (Recommended for new projects)
- Scopes needed:
  - `tweet.read` - Read tweets
  - `tweet.write` - Create tweets
  - `like.write` - Like tweets
  - `retweet.write` - Retweet tweets
  - `follow.write` - Follow users
  - `users.read` - Read user data
  - `users.search.read` - Search users
  - `direct_messages.read` - Read DMs
  - `direct_messages.write` - Send DMs

### 3. Tech Stack
- **Language**: Node.js / TypeScript or Python
- **Libraries**: 
  - `tweepy` (Python) or `@twitter/api-sdk` (TypeScript)
  - `dotenv` for credentials
  - `axios` for HTTP requests
  - AI API: OpenAI, Anthropic, or xAI
- **Database**: SQLite or MongoDB (track operations, avoid duplicates)
- **Scheduler**: Node-cron or APScheduler (Python)

---

## Phase 1: Foundation (Week 1)

### Step 1.1: Authentication Module
Create secure login system:
```
- Load credentials from environment variables
- Test OAuth2 authentication
- Validate token expiration and refresh
- Log authentication events
```

### Step 1.2: Core API Wrapper
```
- Wrapper functions for all X API endpoints
- Error handling with retry logic
- Rate limit management (X API has strict rate limits)
- Request logging for debugging
```

### Step 1.3: Database Setup
```
- Track followers (ID, username, follow status)
- Track liked tweets (tweet ID, author, timestamp)
- Track retweeted tweets (tweet ID, timestamp)
- Track responses to avoid duplicates
- Track API usage for cost tracking
```

### Step 1.4: Testing
```
- Test authentication
- Test fetching account info
- Test rate limits
- Test error handling
```

---

## Phase 2: Core Operations (Week 2-3)

### Step 2.1: Trend Discovery
```
Algorithm:
1. Fetch trending topics by location (WOEID)
2. Filter by relevance and engagement
3. Store trends in database with timestamp
4. Identify niches matching account focus
```

### Step 2.2: Search & Find Relevant Posts
```
Algorithm:
1. Search for tweets using trending hashtags
2. Filter by:
   - Language (English)
   - Engagement (likes, retweets, replies)
   - Author followers (target accounts with 100-50k followers)
   - Tweet recency (last 7 days)
   - No spam indicators
3. Prioritize tweets with high engagement potential
```

### Step 2.3: Like Strategy
```
Daily Operations:
- Like 50-100 relevant tweets from trending hashtags
- Like tweets from accounts you want to follow
- Space out likes (1 like every 30-60 seconds to avoid bot detection)
- Target tweets with 100-5000 engagement for better algorithm push
- Stop after 4 hours of activity (avoid looking like bot)
```

### Step 2.4: Retweet Strategy
```
Daily Operations:
- Retweet 20-30 high-quality tweets
- Filter: high engagement, relevant content
- Add comment to retweets when possible
- Avoid retweeting controversial topics
- Space out operations (1 retweet every 5-10 minutes)
```

### Step 2.5: Follow Strategy
```
Daily Operations:
- Follow 50-100 relevant users
- Source: 
  - Likers of popular tweets in your niche
  - Followers of similar accounts
  - Tweeters of trending hashtags
- Check follow-back ratio before following
- Space out follows (1 follow every 2-5 minutes)
```

### Step 2.6: Unfollow Strategy (Optional)
```
Weekly:
- Track follow-backs after 2 weeks
- Unfollow non-followers to maintain ratio
- Keep followers of your niche even if they don't follow back
```

---

## Phase 3: AI Integration (Week 4)

### Step 3.1: Content Generation
```
Use OpenAI/xAI API to:
- Generate tweet replies to popular posts in your niche
- Create original tweets based on trends
- Generate tweet threads from topics
- Create witty comments to increase engagement

Prompt template:
"Write an engaging reply to this tweet about [topic]. 
Keep it under 280 characters, be helpful and original, 
add relevant emoji. Tweet: [tweet text]"
```

### Step 3.2: DM Reading & Responses
```
Daily:
- Read new DMs
- Filter: questions, inquiries, DM engagement
- Use AI to generate contextual responses
- Send replies to increase engagement and relationship
- Don't spam - only reply when appropriate
```

### Step 3.3: Hashtag Analysis
```
Use AI to:
- Analyze trending hashtags
- Identify emerging trends early
- Predict trending topics
- Suggest relevant hashtags for your niche
```

---

## Available X API Operations

### Posts API
| Operation | Endpoint | Use Case |
|-----------|----------|----------|
| Create Post | `POST /2/tweets` | Post updates, replies |
| Get Post | `GET /2/tweets/{id}` | Fetch tweet details |
| Search Posts | `GET /2/tweets/search/recent` | Find relevant tweets |
| Post Like | `POST /2/users/{id}/likes` | Like tweets |
| Get Likes | `GET /2/tweets/{id}/liked_by` | Find who liked |
| Retweet | `POST /2/users/{id}/retweets` | Retweet tweets |
| Get Retweets | `GET /2/tweets/{id}/retweeted_by` | Find who retweeted |

### Users API
| Operation | Endpoint | Use Case |
|-----------|----------|----------|
| Follow User | `POST /2/users/{id}/following` | Follow users |
| Get Following | `GET /2/users/{id}/following` | Get following list |
| Search Users | `GET /2/users/search` | Find users by query |
| Get User Info | `GET /2/users/{id}` | Fetch user details |
| Get Followers | `GET /2/users/{id}/followers` | Get followers list |

### Trends API
| Operation | Endpoint | Use Case |
|-----------|----------|----------|
| Get Trends | `GET /1.1/trends/place` | Fetch trending topics |
| Get Trend Info | Various | Analyze trending data |

### Direct Messages API
| Operation | Endpoint | Use Case |
|-----------|----------|----------|
| Create DM | `POST /2/dm_conversations/{id}/messages` | Send DM |
| Get DMs | `GET /2/dm_conversations` | Read received DMs |
| Get Messages | `GET /2/dm_conversations/{id}/messages` | Read conversation |

### Lists API (Bonus)
| Operation | Endpoint | Use Case |
|-----------|----------|----------|
| Create List | `POST /2/lists` | Create curated lists |
| Add to List | `POST /2/lists/{id}/members` | Organize users |

---

## Bot Algorithm

### Main Loop (Runs Daily)
```
WHILE account_is_active:
    
    MORNING ROUTINE (6 AM):
    ├─ Fetch trending topics for location
    ├─ Filter trends by relevance
    ├─ Search for relevant tweets under trends
    └─ Store tweet candidates in database
    
    MID-DAY ROUTINE (12 PM):
    ├─ Like Phase:
    │  ├─ Get 50-100 candidate tweets
    │  ├─ Filter already liked tweets
    │  ├─ Like each tweet (wait 30-60s between)
    │  └─ Log in database
    │
    ├─ Retweet Phase:
    │  ├─ Get 20-30 high-engagement tweets
    │  ├─ Filter already retweeted tweets
    │  ├─ Generate AI comment if enabled
    │  ├─ Retweet with comment (wait 5-10m between)
    │  └─ Log in database
    │
    └─ Follow Phase:
       ├─ Get likers from popular tweets
       ├─ Get followers of relevant accounts
       ├─ Check not already following
       ├─ Follow users (wait 2-5m between)
       └─ Log in database
    
    EVENING ROUTINE (6 PM):
    ├─ Read new DMs
    ├─ Filter spam/bot DMs
    ├─ Use AI to generate responses
    ├─ Reply to engaging messages
    └─ Log interactions
    
    NIGHT ROUTINE (10 PM):
    ├─ Post AI-generated tweet or thread
    ├─ Wait 1-2 hours between posts
    ├─ Monitor engagement on posted content
    └─ Log metrics
    
    SAFETY CHECKS (Every hour):
    ├─ Check rate limits
    ├─ Check for account warnings
    ├─ Reset daily counters at midnight
    ├─ Pause if unusual activity detected
    └─ Log all events
```

### Rate Limiting Strategy
```
- X API has strict rate limits (usually 300-450 requests per 15 mins)
- Spread operations throughout the day
- Never burst operations (looks like bot)
- Monitor /2/usage API endpoint
- Pause if approaching limits
- Keep operation logs for analysis
```

### Anti-Bot Detection Strategy
```
✓ Space out all operations (don't do 100 things in 1 second)
✓ Vary timing randomly (don't follow at exact 5-minute intervals)
✓ Mix operation types (don't just like, also reply, retweet)
✓ Only active 8-10 hours per day (rest account)
✓ Add human-like delay patterns
✓ Sometimes skip opportunities (don't interact with EVERYTHING)
✓ Label account as automated in X settings
✓ Follow X's automation rules and policies
✓ Limit operations per day:
  - Likes: 100-150 per day
  - Follows: 50-100 per day
  - Retweets: 20-30 per day
  - Posts: 2-5 per day
```

---

## Implementation Steps

### Step 1: Setup Project Structure
```
x-bot/
├── src/
│   ├── auth/
│   │   ├── oauth.ts          # OAuth 2.0 authentication
│   │   └── credentials.ts    # Credential management
│   ├── api/
│   │   ├── posts.ts          # Posts operations
│   │   ├── users.ts          # Users operations
│   │   ├── trends.ts         # Trends operations
│   │   └── dms.ts            # Direct messages
│   ├── db/
│   │   ├── models.ts         # Database schemas
│   │   └── queries.ts        # Database queries
│   ├── ai/
│   │   ├── openai.ts         # OpenAI integration
│   │   └── prompts.ts        # AI prompts
│   ├── scheduler/
│   │   └── jobs.ts           # Scheduled tasks
│   ├── utils/
│   │   ├── logger.ts         # Logging
│   │   ├── rateLimiter.ts    # Rate limiting
│   │   └── helpers.ts        # Helper functions
│   └── index.ts              # Main entry point
├── .env.example
├── package.json
└── README.md
```

### Step 2: Core Implementation Order
1. **Authentication** - Get login working first
2. **API Wrappers** - Create functions for all operations
3. **Database** - Track all actions to avoid duplicates
4. **Trend Discovery** - Get trending topics
5. **Search Module** - Find relevant tweets
6. **Like Engine** - Start liking
7. **Retweet Engine** - Add retweet capability
8. **Follow Engine** - Start following
9. **Scheduler** - Automate operations
10. **AI Integration** - Add content generation
11. **DM Module** - Read and respond to DMs
12. **Monitoring** - Track metrics and stats

### Step 3: Testing Checklist
- [ ] Can authenticate with X API
- [ ] Can fetch account info
- [ ] Can search for tweets
- [ ] Can like a tweet
- [ ] Can retweet a tweet
- [ ] Can follow a user
- [ ] Can read DMs
- [ ] Rate limits work correctly
- [ ] Database tracking works
- [ ] AI generation works
- [ ] Scheduler runs without errors
- [ ] No bot detection triggers

---

## Security & Best Practices

### Credential Management
```yaml
DO:
✓ Use environment variables (.env file, .gitignore)
✓ Regenerate tokens regularly
✓ Rotate API keys monthly
✓ Use separate app for testing vs production
✓ Enable 2FA on X account

DON'T:
✗ Hardcode credentials in code
✗ Commit .env file to git
✗ Share credentials
✗ Use same tokens across multiple bots
✗ Ignore X's terms of service
```

### API Cost Optimization
```
X API uses pay-per-usage model:
- Posts API: ~$2 per 1000 reads
- Users API: ~$1 per 1000 reads
- Trends API: Lower cost
- DM API: Higher cost

Estimate for bot:
- 100 likes per day × 30 days = 3000 reads (~$6)
- 30 retweets per day × 30 days = 900 reads (~$2)
- 5 posts per day × 30 days = 150 writes (~$5)
- Monthly DM ops: ~$10
Total estimated: $20-50/month for moderate bot activity
```

---

## Key Metrics to Track

1. **Growth Metrics**
   - Followers gained per day
   - Follow-back rate
   - Engagement rate

2. **Activity Metrics**
   - Likes per day
   - Retweets per day
   - Follows per day
   - Posts per day

3. **Engagement Metrics**
   - Replies received
   - Likes on posts
   - Retweets of posts
   - DMs received

4. **Health Metrics**
   - API response times
   - Rate limit usage
   - Error rate
   - Bot detection triggers

---

## Phase 4+: Optimization

After the first month:
- Analyze which trends drive most engagement
- Identify best posting times
- Find optimal follow/unfollow ratio
- Refine AI prompt templates
- A/B test different content styles
- Scale up successful strategies

---

## Important X API Limits

```
Rate Limits (per 15 minutes):
- Search Posts: 300-450 requests
- Get User: 300-450 requests
- Post Creation: 50 requests
- Like: 300 requests
- Follow: 300 requests
- DM: 200 requests (varies by endpoint)

Daily Limits (self-imposed for safety):
- Follow: 100-200 per day
- Unfollow: 100-200 per day
- Like: 100-150 per day
- Post: 5-10 per day
- DM: 30-50 per day
```

---

## Next Steps

1. **Week 1**: Create project structure + auth module
2. **Week 2**: Build API wrappers + database
3. **Week 3**: Implement core operations (like, retweet, follow)
4. **Week 4**: Add scheduler + AI integration
5. **Week 5+**: Test, monitor, optimize, scale

Ready to build? Start with Step 1 in the Implementation section!
