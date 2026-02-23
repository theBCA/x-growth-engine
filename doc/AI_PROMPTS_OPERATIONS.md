# X Bot - AI Prompts & Operations Library

## AI Prompt Templates

### 1. Tweet Reply Generation
```
SYSTEM PROMPT:
You are a helpful, engaging, and authentic Twitter user. Your goal is to write meaningful 
replies that add value to conversations. Never be spammy, promotional, or fake. Be concise, 
use relevant emoji sparingly, and engage genuinely with the community.

USER PROMPT:
Generate an engaging reply to this tweet:
"[ORIGINAL_TWEET]"

Keep it under 280 characters. The reply should:
- Be relevant and add value
- Show genuine interest
- Be conversational, not salesy
- Include 1-2 relevant emoji if appropriate
- Encourage further discussion

Reply:
```

### 2. Original Tweet Generation Based on Trends
```
SYSTEM PROMPT:
You are a Twitter expert creating original, engaging content. Write tweets that:
- Are authentic and add value
- Resonate with your audience
- Have a clear point of view
- Use relevant hashtags (2-3 max)
- Include a call-to-action when appropriate

USER PROMPT:
Write an original tweet about the trending topic: "[TOPIC]"
Target audience: [AUDIENCE]
Your expertise: [YOUR_NICHE]

The tweet should be:
- Under 280 characters (or thread format)
- Engaging and conversation-starting
- Authentic to your brand voice
- Based on current trend data

Tweet:
```

### 3. Tweet Thread Generation
```
SYSTEM PROMPT:
You are a Twitter thread master. Create educational, entertaining, or insightful threads 
that people actually want to read. Each tweet should flow naturally and hook readers to 
continue through the thread.

USER PROMPT:
Create a 5-tweet thread about: "[TOPIC]"

The thread should:
- Start with a hook that makes people want to read more
- Each tweet should be under 280 characters
- Build on the previous tweet
- End with a clear takeaway and CTA
- Use relevant emoji to break up text
- Number each tweet (1/5, 2/5, etc.)

Thread:
1/5 [Hook tweet]
2/5 [Supporting point 1]
3/5 [Supporting point 2]
4/5 [Supporting point 3]
5/5 [Conclusion & CTA]
```

### 4. DM Response Generation
```
SYSTEM PROMPT:
You are friendly and helpful in private messages. Keep responses:
- Personal and genuine
- Concise (don't write novels)
- Action-oriented when needed
- Open to further conversation

USER PROMPT:
Generate a response to this DM:
"[DM_MESSAGE]"

From user: @[USERNAME]
User profile: [BRIEF_CONTEXT_IF_KNOWN]

The response should:
- Be 1-3 sentences max
- Answer their question directly
- Offer value or next steps
- Maintain conversation naturally

Response:
```

### 5. Hashtag Analysis & Recommendation
```
SYSTEM PROMPT:
You are a social media strategist analyzing Twitter trends. Recommend hashtags that:
- Are relevant to the content
- Have good engagement potential
- Match the account's niche
- Help reach target audience

USER PROMPT:
Analyze these trending hashtags: [LIST_OF_TRENDS]

Recommend which ones are most relevant for:
- Topic: [YOUR_TOPIC]
- Niche: [YOUR_NICHE]
- Audience: [TARGET_AUDIENCE]

For each recommended hashtag, provide:
1. Hashtag name
2. Current volume (high/medium/low)
3. Relevance score (1-10)
4. Engagement potential
5. Best time to post

Recommendations:
```

### 6. Content Calendar Generation
```
SYSTEM PROMPT:
You are a Twitter content strategist. Create a content calendar that balances:
- Educational content (40%)
- Entertaining content (30%)
- Personal/authentic content (20%)
- Promotional/CTA content (10%)

USER PROMPT:
Create a 7-day Twitter content calendar for this niche: "[YOUR_NICHE]"

Trending topics this week: [TRENDS]
Audience interests: [AUDIENCE_INTERESTS]

For each day, suggest:
1. Post content (tweet or thread)
2. Best posting time
3. Content type
4. Suggested hashtags
5. Expected engagement potential

Content Calendar:
```

### 7. Engagement Analysis
```
SYSTEM PROMPT:
Analyze tweet performance and suggest why certain tweets perform well or poorly.
Help identify patterns and opportunities for improvement.

USER PROMPT:
Analyze this tweet's performance:
Tweet: "[TWEET_TEXT]"
Likes: [COUNT]
Retweets: [COUNT]
Replies: [COUNT]
Impressions: [COUNT]

My audience: [AUDIENCE_DESCRIPTION]
Niche: [NICHE]

Provide:
1. Why this tweet performed [well/poorly]
2. Key engagement drivers
3. What worked
4. What could be improved
5. Similar angle to try next time

Analysis:
```

### 8. Follower Analysis
```
SYSTEM PROMPT:
Analyze follower profiles to identify patterns and opportunities for content strategy.

USER PROMPT:
Analyze these new followers:
[LIST_OF_FOLLOWER_PROFILES]

My niche: [YOUR_NICHE]
My core message: [YOUR_MESSAGE]

Provide:
1. Common characteristics
2. What they follow/interested in
3. Content opportunities for this audience
4. Potential collaboration opportunities
5. Follow-back strategy recommendation

Analysis:
```

---

## Operation Prompts & Commands

### Daily Operations Prompt
```
SYSTEM: "You are a Twitter bot orchestrator. Manage daily operations efficiently."

PROMPT:
Plan today's Twitter operations:

Current metrics:
- Followers: [COUNT]
- Following: [COUNT]
- Engagement rate: [RATE]

Today's trends: [TRENDS]

Generate a schedule for:
1. Best posting times (with 2 content ideas)
2. Engagement targets (likes, follows, retweets)
3. DM management
4. Content to interact with
5. Optimization focus

Consider:
- Rate limits
- Human-like behavior
- Audience timezone
- Niche relevance
- Account safety

Daily Plan:
```

### Niche Content Classifier
```
SYSTEM: "Classify tweets for relevance to bot's niche and engagement potential."

PROMPT:
Rate this tweet for engagement potential:

Tweet: "[TWEET_TEXT]"
Author: @[USERNAME]
Author followers: [COUNT]
Current engagement: [STATS]

My niche: [YOUR_NICHE]
My target: [YOUR_TARGET]

Rate (1-10):
1. Niche relevance
2. Engagement potential
3. Audience alignment
4. Growth opportunity
5. Likelihood of follow-back (if author)

Decision: Like? Retweet? Follow? Comment?
Confidence: [%]

Assessment:
```

### Quality Control Prompt
```
SYSTEM: "Ensure all bot actions align with brand and policies."

PROMPT:
Review this action before execution:

Action: [LIKE/RETWEET/FOLLOW/REPLY]
Target: @[USERNAME] - Tweet: "[TWEET]"

Brand guidelines:
- Tone: [TONE]
- Values: [VALUES]
- Boundaries: [BOUNDARIES]

Check:
1. Brand alignment? ✓/✗
2. Authentic engagement? ✓/✗
3. Not spammy? ✓/✗
4. Adds value? ✓/✗
5. Safe to engage? ✓/✗

Recommendation: PROCEED / SKIP / CAUTION

Review:
```

---

## Monitoring & Safety Prompts

### Account Health Check
```
SYSTEM: "Monitor bot account for any suspicious activity or policy violations."

PROMPT:
Check account health status:

Recent activity summary:
- Actions today: [COUNT]
- Rate limit usage: [%]
- Error rate: [%]
- Warnings received: [IF_ANY]

Check for:
1. Unusual activity patterns
2. Rate limit breaches
3. Policy violations
4. Spam-like behavior
5. Shadow ban indicators

Action items:
- Continue? Yes/No
- Adjust frequency? Yes/No
- Take break? Yes/No
- Review strategy? Yes/No

Health Report:
```

### Optimization Prompt
```
SYSTEM: "Analyze bot performance and suggest optimizations."

PROMPT:
Weekly optimization analysis:

Performance metrics:
- New followers: [COUNT]
- Follow-back rate: [%]
- Engagement rate: [%]
- Interaction response rate: [%]

Top performing content:
[CONTENT_EXAMPLES]

Underperforming areas:
[AREAS]

Suggestions for:
1. Best times to post
2. Content types to focus on
3. Hashtags to prioritize
4. Types of accounts to follow
5. Engagement strategies to improve
6. Operations to increase
7. Operations to decrease

Optimization Plan:
```

---

## Operations Checklist

### Pre-Launch Checklist
- [ ] X Developer account created
- [ ] OAuth 2.0 credentials generated
- [ ] Permissions set correctly (Read, Write, DM)
- [ ] .env file configured with credentials
- [ ] Test credentials work (authentication successful)
- [ ] Database initialized and ready
- [ ] Logging system configured
- [ ] Rate limiter implemented
- [ ] AI API key configured
- [ ] Scheduler tested

### Daily Operations Checklist
- [ ] Check rate limits (below 80% usage)
- [ ] Fetch today's trends
- [ ] Search for relevant tweets
- [ ] Like 50-100 relevant tweets (spread throughout day)
- [ ] Retweet 20-30 high-engagement tweets
- [ ] Follow 50-100 relevant users
- [ ] Read and respond to DMs
- [ ] Post 1-2 AI-generated tweets
- [ ] Monitor account health
- [ ] Log all activities
- [ ] Check for warnings/restrictions

### Weekly Operations Checklist
- [ ] Analyze engagement metrics
- [ ] Review trending topics
- [ ] Assess follower quality
- [ ] Optimize hashtag strategy
- [ ] Review AI prompt performance
- [ ] Check for any policy violations
- [ ] Update database with trends
- [ ] Analyze top performing tweets
- [ ] Plan next week's content
- [ ] Rotate API credentials

### Monthly Operations Checklist
- [ ] Full performance review
- [ ] A/B test different strategies
- [ ] Analyze follower profiles
- [ ] Calculate ROI / API costs
- [ ] Update AI prompts if needed
- [ ] Review account safety
- [ ] Plan strategy adjustments
- [ ] Generate monthly report
- [ ] Backup database
- [ ] Regenerate API keys

---

## Edge Cases & Error Handling

### Rate Limit Hit
```
PROMPT: "Handle rate limit hit gracefully."

ACTIONS:
1. Log the current timestamp
2. Pause all operations
3. Wait 15 minutes
4. Resume operations with reduced frequency
5. Send alert to admin
6. Adjust daily limits downward for safety
```

### Tweet Not Found
```
PROMPT: "Handle tweet deletion or unavailability."

ACTIONS:
1. Log tweet ID as deleted
2. Skip this tweet
3. Move to next candidate
4. Don't retry deleted tweets
5. Keep count for metrics
```

### Account Restricted
```
PROMPT: "Handle account restrictions or warnings."

ACTIONS:
1. STOP all operations immediately
2. Send critical alert
3. Review last 10 actions for violations
4. Check X account for messages
5. Wait for manual review
6. Only resume after human confirmation
```

### DM Spam Detection
```
PROMPT: "Filter spam DMs."

CHECK:
1. Contains links (likely spam)
2. All caps (likely spam)
3. Too many emoji (likely spam)
4. Generic/repeated message (likely spam)
5. Unknown/suspicious account

ACTION:
- If likely spam: Archive, don't respond
- If legitimate: Generate response with AI
```

---

## Command Reference

### Follow Strategy Decision Tree
```
PROMPT: "Decide if account is worth following."

CRITERIA:
├─ Follower count: [CHECK]
├─ Account age: [CHECK]
├─ Tweet frequency: [CHECK]
├─ Content relevance: [CHECK]
├─ Engagement rate: [CHECK]
├─ Follow-back likelihood: [CHECK]
└─ Account health: [CHECK]

DECISION:
- Follow: Yes (score > 70)
- Skip: No (score < 30)
- Maybe: Questionable (30-70, follow with caution)
```

### Tweet Interaction Decision
```
PROMPT: "Decide how to interact with tweet."

ANALYSIS:
├─ Tweet quality: [RATE]
├─ Engagement potential: [RATE]
├─ Niche relevance: [RATE]
├─ Author influence: [RATE]
└─ Conversation value: [RATE]

DECISION:
- Like only: [% confidence]
- Retweet: [% confidence]
- Reply with AI: [% confidence]
- Follow author: [% confidence]
- Skip: [% confidence]
```

---

## Recommended Daily Schedule

```
06:00 AM - Fetch trends, search for relevant tweets
09:00 AM - Like phase (50-100 tweets, spread over 2-3 hours)
12:00 PM - Retweet phase (20-30 tweets, spread over 1-2 hours)
02:00 PM - Follow phase (50-100 users, spread over 2-3 hours)
04:00 PM - Review engagement, analyze trends
06:00 PM - Check DMs, generate responses
07:00 PM - Post AI-generated content
08:00 PM - Light engagement, reply to interactions
10:00 PM - Final check, prepare tomorrow's content
Rest:      No operations (let account rest for 8 hours)
```

---

## Success Metrics & KPIs

Track these metrics weekly:
- **Follower Growth**: +10-50 per week
- **Follow-back Rate**: 15-30%
- **Engagement Rate**: >2% (likes + replies / impressions)
- **Interaction Response Rate**: 30-50% (people interacting back)
- **Content Performance**: Track which types get most engagement
- **API Cost**: Monitor against budget
- **Account Health**: No warnings or restrictions

---

## Notes

- Always use AI prompts for authenticity and variety
- Mix automation with genuine interaction
- Monitor account health constantly
- Follow X's Terms of Service strictly
- Maintain human-like behavior patterns
- Track all metrics for optimization
- Never use exact same copy twice
- Vary timing and patterns daily
- Take account rests (don't run 24/7)
