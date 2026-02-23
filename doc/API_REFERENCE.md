# X API Operations - Complete Reference

## API Endpoints Overview

### Authentication Endpoints

#### OAuth 2.0 Authorization
```
GET https://twitter.com/i/oauth2/authorize
- client_id (required)
- redirect_uri (required)
- response_type=code (required)
- scope (required) - space-separated
- state (recommended) - CSRF protection
```

#### Token Exchange
```
POST https://api.x.com/2/oauth2/token
Headers:
  Content-Type: application/x-www-form-urlencoded

Body:
  client_id=YOUR_CLIENT_ID
  client_secret=YOUR_CLIENT_SECRET
  redirect_uri=YOUR_REDIRECT_URI
  grant_type=authorization_code
  code=AUTHORIZATION_CODE

Response:
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 7200,
  "scope": "string"
}
```

---

## Posts Operations

### Search Recent Tweets
```
GET /2/tweets/search/recent
Parameters:
  query (required) - search query, supports operators
  max_results (optional) - 10-100, default 10
  start_time (optional) - RFC3339 format
  end_time (optional) - RFC3339 format
  tweet.fields (optional) - public_metrics,created_at,author_id
  expansions (optional) - author_id,geo.place_id

Example:
GET /2/tweets/search/recent?query=bitcoin&max_results=100&tweet.fields=public_metrics,author_id
```

#### Search Operators
```
Query Operators:
  keyword                    - exact phrase
  "exact phrase"             - quoted phrase
  lang:en                    - English language
  has:images                 - tweets with images
  has:videos                 - tweets with videos
  has:links                  - tweets with links
  from:@username             - from specific user
  to:@username               - replies to user
  -word                      - exclude word
  min_faves:100              - minimum likes
  min_retweets:50            - minimum retweets
  until:2023-01-01           - before date
  since:2023-01-01           - after date

Examples:
  bitcoin has:images lang:en  (Bitcoin tweets with images, English)
  python from:@PythonOrg      (Python tweets from @PythonOrg)
  #AI -bot                    (AI hashtag, exclude bot mentions)
  crypto min_faves:1000       (Crypto with 1k+ likes)
```

---

### Create Tweet
```
POST /2/tweets
Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
  Content-Type: application/json

Body:
{
  "text": "Your tweet text here (max 280 chars)"
}

Response:
{
  "data": {
    "id": "1234567890",
    "text": "Your tweet text here"
  }
}

Errors:
  - 429: Rate limited
  - 400: Invalid text/too long
  - 401: Invalid credentials
```

---

### Like Tweet
```
POST /2/users/{id}/likes
Path Parameters:
  id - Your user ID

Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
  Content-Type: application/json

Body:
{
  "tweet_id": "tweet_id_to_like"
}

Response:
{
  "data": {
    "liking": true
  }
}

Rate Limit: 300 per 15 minutes
```

---

### Retweet Tweet
```
POST /2/users/{id}/retweets
Path Parameters:
  id - Your user ID

Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
  Content-Type: application/json

Body:
{
  "tweet_id": "tweet_id_to_retweet"
}

Response:
{
  "data": {
    "retweeted": true
  }
}

Rate Limit: 300 per 15 minutes
```

---

### Get Tweet
```
GET /2/tweets/{id}
Path Parameters:
  id - Tweet ID

Query Parameters:
  tweet.fields - public_metrics,created_at,author_id,conversation_id
  expansions - author_id,geo.place_id
  user.fields - name,username,verified,followers_count

Example Response:
{
  "data": {
    "id": "1234567890",
    "text": "Tweet content",
    "public_metrics": {
      "retweet_count": 10,
      "reply_count": 5,
      "like_count": 100,
      "quote_count": 2
    },
    "created_at": "2023-01-01T12:00:00Z",
    "author_id": "98765432"
  }
}
```

---

## Users Operations

### Follow User
```
POST /2/users/{id}/following
Path Parameters:
  id - Your user ID

Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
  Content-Type: application/json

Body:
{
  "target_user_id": "user_id_to_follow"
}

Response:
{
  "data": {
    "following": true
  }
}

Rate Limit: 300 per 15 minutes
```

---

### Unfollow User
```
DELETE /2/users/{id}/following/{target_user_id}
Path Parameters:
  id - Your user ID
  target_user_id - User to unfollow

Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN

Response:
{
  "data": {
    "following": false
  }
}
```

---

### Get User by Username
```
GET /2/users/by/username/{username}
Path Parameters:
  username - Twitter username (without @)

Query Parameters:
  user.fields - name,username,verified,followers_count,created_at
  expansions - pinned_tweet_id

Example:
GET /2/users/by/username/elonmusk?user.fields=verified,followers_count

Response:
{
  "data": {
    "id": "44196397",
    "name": "Elon Musk",
    "username": "elonmusk",
    "verified": true,
    "followers_count": 150000000
  }
}
```

---

### Get User by ID
```
GET /2/users/{id}
Path Parameters:
  id - User ID

Query Parameters:
  user.fields - name,username,verified,followers_count
```

---

### Search Users
```
GET /2/users/search
Query Parameters:
  query (required) - search query
  max_results (optional) - 10-100
  user.fields (optional) - verified,followers_count,created_at

Example:
GET /2/users/search?query=python+developer&max_results=50&user.fields=verified,followers_count

Response:
{
  "data": [
    {
      "id": "123456",
      "name": "Python Developer",
      "username": "pydev",
      "verified": false,
      "followers_count": 5000
    },
    ...
  ]
}
```

---

### Get User Following List
```
GET /2/users/{id}/following
Path Parameters:
  id - User ID

Query Parameters:
  max_results - 10-100
  user.fields - name,username,verified,followers_count
  pagination_token (optional) - for pagination

Returns list of users this user is following
```

---

### Get User Followers List
```
GET /2/users/{id}/followers
Path Parameters:
  id - User ID

Query Parameters:
  max_results - 10-100
  user.fields - verified,followers_count
  pagination_token (optional)

Returns list of users following this user
```

---

## Trends Operations

### Get Trending Topics
```
GET /1.1/trends/place.json
(Note: Uses v1.1 API, requires Bearer Token)

Query Parameters:
  id (required) - WOEID (Where On Earth ID)

WOEID Reference:
  1 - Worldwide
  23424977 - United States
  23424819 - United Kingdom
  23424856 - Pakistan
  23424848 - India
  2357024 - New York City
  2358410 - Los Angeles
  2430863 - Chicago

Example:
GET /1.1/trends/place.json?id=1

Response:
{
  "trends": [
    {
      "name": "#Bitcoin",
      "url": "https://twitter.com/search?q=%23Bitcoin",
      "query": "%23Bitcoin",
      "tweet_volume": 250000
    },
    ...
  ],
  "as_of": "2023-01-01T12:00:00Z",
  "created_at": "2023-01-01T11:50:00Z"
}
```

---

## Direct Messages Operations

### Get DM Conversations
```
GET /2/dm_conversations
Query Parameters:
  dm_conversation.fields - participant_ids,conversation_type
  max_results - 1-100
  pagination_token (optional)

Response:
{
  "data": [
    {
      "id": "123456",
      "participant_ids": ["456789", "789012"],
      "conversation_type": "Group"
    },
    ...
  ]
}
```

---

### Get DM Messages
```
GET /2/dm_conversations/{id}/messages
Path Parameters:
  id - Conversation ID

Query Parameters:
  dm.fields - created_at,sender_id,text
  max_results - 1-100

Response:
{
  "data": [
    {
      "id": "msg123",
      "text": "Message content",
      "sender_id": "456789",
      "created_at": "2023-01-01T12:00:00Z"
    },
    ...
  ]
}
```

---

### Create DM
```
POST /2/dm_conversations/{id}/messages
Path Parameters:
  id - Conversation ID

Headers:
  Authorization: Bearer YOUR_ACCESS_TOKEN
  Content-Type: application/json

Body:
{
  "text": "Your message here (max 10000 chars)"
}

Response:
{
  "data": {
    "dm_message_id": "msg123"
  }
}

Rate Limit: 200 per 15 minutes
```

---

## Rate Limits Summary

```
Endpoint                          | Limit          | Window
----------------------------------|----------------|--------
GET /2/tweets/search/recent       | 300-450 req    | 15 min
GET /2/users/{id}/following       | 15 req/user    | 15 min
POST /2/users/{id}/following      | 300 req        | 15 min
DELETE /2/users/{id}/following    | 300 req        | 15 min
GET /2/users/search               | 300 req        | 15 min
GET /2/users/by/username          | 300 req        | 15 min
POST /2/tweets                    | 50 req         | 15 min
POST /2/users/{id}/likes          | 300 req        | 15 min
POST /2/users/{id}/retweets       | 300 req        | 15 min
GET /2/dm_conversations           | 300 req        | 15 min
POST /2/dm_conversations          | 200 req        | 15 min
GET /1.1/trends/place             | 75 req         | 15 min
```

---

## Error Handling

### HTTP Status Codes

```
200 OK
  Success - operation completed

429 Too Many Requests
  Rate limited - wait 15 minutes before retrying

400 Bad Request
  Invalid parameters - check request format

401 Unauthorized
  Invalid credentials - check token/authentication

403 Forbidden
  Don't have permission - check OAuth scopes

404 Not Found
  Tweet/user doesn't exist

500 Internal Server Error
  X API issue - retry after 1 minute
```

### Common Error Responses

```json
{
  "errors": [
    {
      "message": "Invalid request",
      "type": "https://api.x.com/2/problems/resource-not-found",
      "title": "Not Found",
      "resource_type": "tweet",
      "parameter": "id",
      "value": "invalid_id"
    }
  ]
}
```

---

## OAuth 2.0 Scopes

```
tweet.read
  - Read tweets and timelines
  - Required for: search, get tweets, get user tweets

tweet.write
  - Create and edit tweets
  - Required for: creating tweets

like.read
  - See which tweets user has liked
  - Required for: check if tweet liked

like.write
  - Like and unlike tweets
  - Required for: liking tweets

retweet.read
  - See retweets
  - Required for: check if retweet exists

retweet.write
  - Retweet and unretweeet
  - Required for: retweeting

follow.read
  - See who user follows
  - Required for: get following list

follow.write
  - Follow and unfollow users
  - Required for: following/unfollowing

users.read
  - See user profile info
  - Required for: get user data, following/followers counts

users.search.read
  - Search for users
  - Required for: user search

direct_messages.read
  - Read direct messages
  - Required for: reading DMs

direct_messages.write
  - Send direct messages
  - Required for: sending DMs

block.read / block.write
  - Manage blocks

mute.read / mute.write
  - Manage mutes
```

---

## Pagination

Many endpoints return large datasets with pagination:

```
Response with pagination:
{
  "data": [...],
  "meta": {
    "result_count": 100,
    "next_token": "b26v89c19zqg8o3fpza8qwjhz0....",
    "newest_id": "1234567890",
    "oldest_id": "1234567800"
  }
}

Next Request:
GET /2/tweets/search/recent?query=bitcoin&pagination_token=b26v89c19zqg8o3fpza8qwjhz0....
```

---

## Best Practices

### 1. Request Optimization
```
✓ Use fields parameter to get only needed data
✓ Use expansions for related data
✓ Batch requests when possible
✗ Don't request data you won't use
```

### 2. Error Handling
```javascript
try {
  const response = await api.post('/tweets', {text: tweet});
  return response.data;
} catch (error) {
  if (error.response?.status === 429) {
    // Rate limited - wait and retry
    await sleep(60000);
    return retry();
  } else if (error.response?.status === 401) {
    // Credentials invalid
    console.error('Invalid credentials');
    process.exit(1);
  } else if (error.response?.status === 400) {
    // Bad request
    console.error('Invalid parameters:', error.response.data);
  }
}
```

### 3. Rate Limit Management
```javascript
// Track rate limit usage
const checkRateLimits = () => {
  if (requestsInWindow > limit * 0.8) {
    console.warn('Approaching rate limit');
    // Pause operations
    shouldPause = true;
  }
};

// Add delays between operations
const delay = Math.random() * 30000 + 30000; // 30-60 seconds
await sleep(delay);
```

### 4. Human-like Behavior
```javascript
✓ Random delays between operations
✓ Mix different operation types
✓ Don't operate 24/7 (8-10 hours/day)
✓ Vary posting times
✓ Sometimes skip opportunities
✓ Gradual operation increase

✗ Burst operations (100 likes in 1 minute)
✗ Only one operation type
✗ Exact same time every day
✗ Run continuously (24/7)
```

---

## Implementation Examples

### Search & Like Example
```javascript
// 1. Search for tweets
const tweets = await api.get('/2/tweets/search/recent', {
  params: {
    query: '#bitcoin lang:en',
    max_results: 50,
    'tweet.fields': 'public_metrics,created_at'
  }
});

// 2. Score tweets by engagement
const scored = tweets.data.data.map(tweet => ({
  ...tweet,
  engagement: tweet.public_metrics.like_count + 
              (tweet.public_metrics.retweet_count * 2)
}));

// 3. Sort by engagement
scored.sort((a, b) => b.engagement - a.engagement);

// 4. Like top tweets
for (const tweet of scored.slice(0, 20)) {
  await api.post(`/users/${myUserId}/likes`, {
    tweet_id: tweet.id
  });
  
  // Human-like delay
  await sleep(Math.random() * 30000 + 30000);
}
```

### Follow Influential Users Example
```javascript
// 1. Search for users in niche
const users = await api.get('/2/users/search', {
  params: {
    query: 'python developer',
    max_results: 100,
    'user.fields': 'verified,followers_count,created_at'
  }
});

// 2. Filter quality users
const filtered = users.data.data.filter(user => 
  user.followers_count > 100 &&
  user.followers_count < 50000 &&
  user.verified === false // Less likely to be institutional
);

// 3. Follow filtered users
for (const user of filtered.slice(0, 30)) {
  await api.post(`/users/${myUserId}/following`, {
    target_user_id: user.id
  });
  
  // Random delay 2-5 minutes
  await sleep(Math.random() * 180000 + 120000);
}
```

### Generate & Post Content Example
```javascript
// 1. Get current trends
const trends = await api.get('/1.1/trends/place.json', {
  params: { id: 1 }
});

// 2. Pick top trend
const trendName = trends.data[0].trends[0].name;

// 3. Use AI to generate tweet
const tweet = await openai.createCompletion({
  prompt: `Write a tweet about ${trendName}`,
  max_tokens: 50
});

// 4. Post tweet
await api.post('/2/tweets', {
  text: tweet.choices[0].text
});
```

---

## Cost Tracking

```javascript
// Estimated costs per operation:
const COSTS = {
  search: 0.002,        // $0.002 per search
  get_user: 0.001,      // $0.001 per user lookup
  like: 0.002,          // $0.002 per like
  follow: 0.002,        // $0.002 per follow
  post: 0.010,          // $0.010 per post
  dm: 0.005             // $0.005 per DM
};

// Calculate daily cost
const dailyLikes = 100;
const dailyFollows = 50;
const dailyPosts = 3;

const dailyCost = 
  (dailyLikes * COSTS.like) +
  (dailyFollows * COSTS.follow) +
  (dailyPosts * COSTS.post);

console.log(`Estimated daily cost: $${dailyCost.toFixed(2)}`);
console.log(`Estimated monthly cost: $${(dailyCost * 30).toFixed(2)}`);
```

---

## Troubleshooting Common Issues

### "Tweet not found"
```
Cause: Tweet was deleted or made private
Solution: Skip tweet, try next one
Action: Log tweet ID, don't retry
```

### "User not found"
```
Cause: Account deleted or suspended
Solution: Skip user, try next one
Action: Mark user as inactive
```

### "Duplicate action"
```
Cause: Already liked/followed
Solution: Check database first
Action: Query if interaction exists before action
```

### "Rate limited"
```
Cause: Too many requests in 15 minutes
Solution: Wait 15 minutes, reduce request rate
Action: Pause all operations, implement backoff
```

---

## Security Checklist

- [ ] Never hardcode credentials
- [ ] Use environment variables for secrets
- [ ] Rotate credentials monthly
- [ ] Don't share API keys
- [ ] Use HTTPS only
- [ ] Validate all user inputs
- [ ] Log all operations for auditing
- [ ] Monitor for unusual activity
- [ ] Keep dependencies updated
- [ ] Test error handling thoroughly

---

## Additional Resources

- **Rate Limit Checker**: https://developer.x.com/rate-limits
- **API Status**: https://api.x.com/2/openapi.json
- **Postman Collection**: https://www.postman.com/xapidevelopers/
- **SDK Documentation**: https://docs.x.com/xdks/overview
- **Community Forum**: https://devcommunity.x.com/

