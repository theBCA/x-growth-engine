# X Bot - Technical Implementation Guide

## Quick Start (Step-by-Step)

### Part 1: Project Setup (30 minutes)

#### 1.1 Initialize Node.js Project
```bash
mkdir x-bot && cd x-bot
npm init -y
npm install --save dotenv axios tweepy sqlite3 node-cron
npm install --save-dev typescript @types/node ts-node
```

#### 1.2 TypeScript Configuration
Create `tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

#### 1.3 Environment Setup
Create `.env` file:
```env
# X API Credentials (OAuth 2.0)
X_CLIENT_ID=your_client_id
X_CLIENT_SECRET=your_client_secret
X_REDIRECT_URI=http://127.0.0.1:3000/callback

# Or use OAuth 1.0a
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# AI API
OPENAI_API_KEY=your_openai_key
# OR
XAI_API_KEY=your_xai_key

# Bot Settings
BOT_ACCOUNT_ID=your_twitter_user_id
BOT_NICHE=technology
BOT_TARGET_AUDIENCE=developers
LOG_LEVEL=debug

# Database
DB_PATH=./data/bot.db

# Safety Limits
MAX_LIKES_PER_DAY=150
MAX_FOLLOWS_PER_DAY=100
MAX_RETWEETS_PER_DAY=30
MAX_POSTS_PER_DAY=5
```

#### 1.4 Create Project Structure
```bash
mkdir -p src/{auth,api,db,ai,scheduler,utils}
mkdir -p data logs
touch src/index.ts
```

---

### Part 2: Core Authentication Module (1 hour)

Create `src/auth/oauth.ts`:
```typescript
import axios, { AxiosInstance } from 'axios';
import dotenv from 'dotenv';

dotenv.config();

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

class XAuthenticator {
  private clientId: string;
  private clientSecret: string;
  private redirectUri: string;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor() {
    this.clientId = process.env.X_CLIENT_ID || '';
    this.clientSecret = process.env.X_CLIENT_SECRET || '';
    this.redirectUri = process.env.X_REDIRECT_URI || 'http://127.0.0.1:3000/callback';
  }

  /**
   * Get authorization URL for user to login
   */
  getAuthorizationUrl(): string {
    const scope = [
      'tweet.read',
      'tweet.write',
      'like.write',
      'retweet.write',
      'follow.write',
      'users.read',
      'users.search.read',
      'direct_messages.read',
      'direct_messages.write'
    ];

    const params = new URLSearchParams({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      response_type: 'code',
      scope: scope.join(' '),
      state: Math.random().toString(36).substring(7)
    });

    return `https://twitter.com/i/oauth2/authorize?${params.toString()}`;
  }

  /**
   * Exchange authorization code for access token
   */
  async getAccessToken(code: string): Promise<string> {
    try {
      const response = await axios.post<TokenResponse>(
        'https://api.x.com/2/oauth2/token',
        {
          client_id: this.clientId,
          client_secret: this.clientSecret,
          redirect_uri: this.redirectUri,
          grant_type: 'authorization_code',
          code: code
        }
      );

      this.accessToken = response.data.access_token;
      this.tokenExpiry = Date.now() + response.data.expires_in * 1000;

      console.log('✓ Access token obtained successfully');
      return this.accessToken;
    } catch (error) {
      console.error('✗ Failed to get access token:', error);
      throw error;
    }
  }

  /**
   * Check if token is expired
   */
  isTokenExpired(): boolean {
    return Date.now() > this.tokenExpiry;
  }

  /**
   * Get current access token
   */
  getToken(): string {
    if (!this.accessToken) {
      throw new Error('No access token available. User must authenticate first.');
    }
    if (this.isTokenExpired()) {
      throw new Error('Access token has expired. Need to re-authenticate.');
    }
    return this.accessToken;
  }

  /**
   * Create authenticated API client
   */
  createApiClient(): AxiosInstance {
    return axios.create({
      baseURL: 'https://api.x.com/2',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
  }
}

export default new XAuthenticator();
```

Create `src/auth/credentials.ts`:
```typescript
import fs from 'fs';
import path from 'path';

interface StoredCredentials {
  accessToken: string;
  tokenExpiry: number;
  refreshToken?: string;
}

class CredentialManager {
  private credPath: string;

  constructor() {
    this.credPath = path.join(process.cwd(), 'data', 'credentials.json');
  }

  /**
   * Save credentials to file (encrypted in production)
   */
  saveCredentials(credentials: StoredCredentials): void {
    try {
      fs.mkdirSync(path.dirname(this.credPath), { recursive: true });
      // TODO: Encrypt this in production!
      fs.writeFileSync(this.credPath, JSON.stringify(credentials, null, 2));
      console.log('✓ Credentials saved');
    } catch (error) {
      console.error('✗ Failed to save credentials:', error);
      throw error;
    }
  }

  /**
   * Load credentials from file
   */
  loadCredentials(): StoredCredentials | null {
    try {
      if (!fs.existsSync(this.credPath)) {
        return null;
      }
      const data = fs.readFileSync(this.credPath, 'utf-8');
      // TODO: Decrypt in production!
      return JSON.parse(data);
    } catch (error) {
      console.error('✗ Failed to load credentials:', error);
      return null;
    }
  }

  /**
   * Check if credentials exist and are valid
   */
  hasValidCredentials(): boolean {
    const creds = this.loadCredentials();
    if (!creds) return false;
    return Date.now() < creds.tokenExpiry;
  }
}

export default new CredentialManager();
```

---

### Part 3: Database Setup (45 minutes)

Create `src/db/models.ts`:
```typescript
import sqlite3 from 'sqlite3';
import path from 'path';

const DB_PATH = process.env.DB_PATH || './data/bot.db';

class Database {
  private db: sqlite3.Database;

  constructor() {
    this.db = new sqlite3.Database(DB_PATH, (err) => {
      if (err) {
        console.error('Database connection error:', err);
      } else {
        console.log('✓ Connected to database');
      }
    });
  }

  /**
   * Initialize all tables
   */
  async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.serialize(() => {
        // Tweets table - track all interactions
        this.db.run(`
          CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY,
            author_id TEXT,
            author_username TEXT,
            text TEXT,
            engagement_score INTEGER,
            liked BOOLEAN DEFAULT 0,
            retweeted BOOLEAN DEFAULT 0,
            replied BOOLEAN DEFAULT 0,
            created_at TIMESTAMP,
            interaction_timestamp TIMESTAMP
          )
        `);

        // Users table - track follows
        this.db.run(`
          CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            followers_count INTEGER,
            following_count INTEGER,
            followed BOOLEAN DEFAULT 0,
            unfollowed BOOLEAN DEFAULT 0,
            follow_timestamp TIMESTAMP,
            unfollow_timestamp TIMESTAMP
          )
        `);

        // Trends table - track trending topics
        this.db.run(`
          CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_name TEXT,
            volume INTEGER,
            engagement_score INTEGER,
            last_checked TIMESTAMP
          )
        `);

        // Activity log - track all bot actions
        this.db.run(`
          CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            target_id TEXT,
            status TEXT,
            timestamp TIMESTAMP,
            details TEXT
          )
        `);

        // DMs table - track direct messages
        this.db.run(`
          CREATE TABLE IF NOT EXISTS dms (
            id TEXT PRIMARY KEY,
            sender_id TEXT,
            sender_username TEXT,
            message_text TEXT,
            replied BOOLEAN DEFAULT 0,
            ai_response TEXT,
            created_at TIMESTAMP,
            reply_timestamp TIMESTAMP
          )
        `, (err) => {
          if (err) reject(err);
          else resolve();
        });
      });
    });
  }

  /**
   * Generic run method for INSERT/UPDATE/DELETE
   */
  run(sql: string, params: any[] = []): Promise<void> {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Generic get method for single row
   */
  get(sql: string, params: any[] = []): Promise<any> {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  /**
   * Generic all method for multiple rows
   */
  all(sql: string, params: any[] = []): Promise<any[]> {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows || []);
      });
    });
  }

  close(): void {
    this.db.close();
  }
}

export default new Database();
```

Create `src/db/queries.ts`:
```typescript
import db from './models';

export const TweetQueries = {
  /**
   * Add or update tweet in database
   */
  async saveTweet(tweetData: any): Promise<void> {
    await db.run(
      `INSERT OR REPLACE INTO tweets (id, author_id, author_username, text, engagement_score, created_at)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [tweetData.id, tweetData.author_id, tweetData.author_username, tweetData.text, tweetData.engagement_score, new Date()]
    );
  },

  /**
   * Mark tweet as liked
   */
  async markLiked(tweetId: string): Promise<void> {
    await db.run(
      `UPDATE tweets SET liked = 1, interaction_timestamp = ? WHERE id = ?`,
      [new Date(), tweetId]
    );
  },

  /**
   * Get candidate tweets for liking
   */
  async getCandidateTweets(limit: number = 50): Promise<any[]> {
    return db.all(
      `SELECT * FROM tweets WHERE liked = 0 ORDER BY engagement_score DESC LIMIT ?`,
      [limit]
    );
  },

  /**
   * Get already liked tweets today
   */
  async getLikesToday(): Promise<number> {
    const result = await db.get(
      `SELECT COUNT(*) as count FROM tweets WHERE liked = 1 AND DATE(interaction_timestamp) = DATE('now')`
    );
    return result?.count || 0;
  }
};

export const UserQueries = {
  /**
   * Save or update user
   */
  async saveUser(userData: any): Promise<void> {
    await db.run(
      `INSERT OR REPLACE INTO users (id, username, followers_count, following_count)
       VALUES (?, ?, ?, ?)`,
      [userData.id, userData.username, userData.followers_count, userData.following_count]
    );
  },

  /**
   * Mark user as followed
   */
  async markFollowed(userId: string): Promise<void> {
    await db.run(
      `UPDATE users SET followed = 1, follow_timestamp = ? WHERE id = ?`,
      [new Date(), userId]
    );
  },

  /**
   * Get candidate users to follow
   */
  async getCandidateUsers(limit: number = 50): Promise<any[]> {
    return db.all(
      `SELECT * FROM users WHERE followed = 0 ORDER BY followers_count DESC LIMIT ?`,
      [limit]
    );
  },

  /**
   * Check if already following user
   */
  async isFollowed(userId: string): Promise<boolean> {
    const result = await db.get(
      `SELECT followed FROM users WHERE id = ?`,
      [userId]
    );
    return result?.followed === 1;
  }
};

export const ActivityQueries = {
  /**
   * Log bot activity
   */
  async log(actionType: string, targetId: string, status: string, details?: string): Promise<void> {
    await db.run(
      `INSERT INTO activity_log (action_type, target_id, status, timestamp, details)
       VALUES (?, ?, ?, ?, ?)`,
      [actionType, targetId, status, new Date(), details]
    );
  },

  /**
   * Get today's activity count
   */
  async getTodayActionCount(actionType: string): Promise<number> {
    const result = await db.get(
      `SELECT COUNT(*) as count FROM activity_log WHERE action_type = ? AND DATE(timestamp) = DATE('now')`,
      [actionType]
    );
    return result?.count || 0;
  },

  /**
   * Get activity history
   */
  async getHistory(limit: number = 100): Promise<any[]> {
    return db.all(
      `SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?`,
      [limit]
    );
  }
};
```

---

### Part 4: X API Wrapper (1.5 hours)

Create `src/api/posts.ts`:
```typescript
import axios from 'axios';
import auth from '../auth/oauth';
import { ActivityQueries } from '../db/queries';

const API_BASE = 'https://api.x.com/2';

export const PostsAPI = {
  /**
   * Search for tweets
   */
  async searchTweets(query: string, maxResults: number = 10): Promise<any[]> {
    try {
      const client = auth.createApiClient();
      const response = await client.get('/tweets/search/recent', {
        params: {
          query: query,
          max_results: Math.min(maxResults, 100),
          'tweet.fields': 'public_metrics,created_at,author_id',
          'expansions': 'author_id'
        }
      });

      await ActivityQueries.log('search_tweets', query, 'success', `Found ${response.data.data?.length || 0} tweets`);
      return response.data.data || [];
    } catch (error) {
      await ActivityQueries.log('search_tweets', query, 'failed', String(error));
      console.error('Search tweets error:', error);
      return [];
    }
  },

  /**
   * Like a tweet
   */
  async likeTweet(tweetId: string, userId: string): Promise<boolean> {
    try {
      const client = auth.createApiClient();
      await client.post(`/users/${userId}/likes`, {
        tweet_id: tweetId
      });

      await ActivityQueries.log('like_tweet', tweetId, 'success');
      return true;
    } catch (error: any) {
      if (error.response?.status === 429) {
        await ActivityQueries.log('like_tweet', tweetId, 'rate_limited');
      } else {
        await ActivityQueries.log('like_tweet', tweetId, 'failed', String(error));
      }
      return false;
    }
  },

  /**
   * Retweet a tweet
   */
  async retweetTweet(tweetId: string, userId: string): Promise<boolean> {
    try {
      const client = auth.createApiClient();
      await client.post(`/users/${userId}/retweets`, {
        tweet_id: tweetId
      });

      await ActivityQueries.log('retweet_tweet', tweetId, 'success');
      return true;
    } catch (error) {
      await ActivityQueries.log('retweet_tweet', tweetId, 'failed', String(error));
      return false;
    }
  },

  /**
   * Create a tweet
   */
  async createTweet(text: string): Promise<string | null> {
    try {
      const client = auth.createApiClient();
      const response = await client.post('/tweets', {
        text: text
      });

      const tweetId = response.data.data?.id;
      await ActivityQueries.log('create_tweet', tweetId || 'unknown', 'success');
      return tweetId || null;
    } catch (error) {
      await ActivityQueries.log('create_tweet', 'unknown', 'failed', String(error));
      return null;
    }
  }
};
```

Create `src/api/users.ts`:
```typescript
import auth from '../auth/oauth';
import { ActivityQueries } from '../db/queries';

export const UsersAPI = {
  /**
   * Follow a user
   */
  async followUser(userId: string, targetId: string): Promise<boolean> {
    try {
      const client = auth.createApiClient();
      await client.post(`/users/${userId}/following`, {
        target_user_id: targetId
      });

      await ActivityQueries.log('follow_user', targetId, 'success');
      return true;
    } catch (error: any) {
      if (error.response?.status === 429) {
        await ActivityQueries.log('follow_user', targetId, 'rate_limited');
      } else {
        await ActivityQueries.log('follow_user', targetId, 'failed', String(error));
      }
      return false;
    }
  },

  /**
   * Get user info
   */
  async getUser(username: string): Promise<any> {
    try {
      const client = auth.createApiClient();
      const response = await client.get(`/users/by/username/${username}`, {
        params: {
          'user.fields': 'public_metrics,verified'
        }
      });

      return response.data.data;
    } catch (error) {
      console.error('Get user error:', error);
      return null;
    }
  },

  /**
   * Search for users
   */
  async searchUsers(query: string, maxResults: number = 10): Promise<any[]> {
    try {
      const client = auth.createApiClient();
      const response = await client.get('/users/search', {
        params: {
          query: query,
          max_results: Math.min(maxResults, 100),
          'user.fields': 'public_metrics,verified'
        }
      });

      return response.data.data || [];
    } catch (error) {
      console.error('Search users error:', error);
      return [];
    }
  }
};
```

---

### Part 5: Trends & Search Module (1 hour)

Create `src/api/trends.ts`:
```typescript
import axios from 'axios';
import { ActivityQueries } from '../db/queries';

export const TrendsAPI = {
  /**
   * Get trending topics
   * Note: X API v1.1 endpoint, requires Bearer Token
   */
  async getTrendingTopics(woeid: number = 1): Promise<string[]> {
    try {
      const bearer = process.env.X_BEARER_TOKEN;
      if (!bearer) throw new Error('Bearer token not configured');

      const response = await axios.get(
        `https://api.x.com/1.1/trends/place.json?id=${woeid}`,
        {
          headers: {
            'Authorization': `Bearer ${bearer}`
          }
        }
      );

      const trends = response.data[0]?.trends || [];
      const trendNames = trends.map((t: any) => t.name).slice(0, 10);

      await ActivityQueries.log('fetch_trends', String(woeid), 'success', `Found ${trendNames.length} trends`);
      return trendNames;
    } catch (error) {
      await ActivityQueries.log('fetch_trends', String(woeid), 'failed', String(error));
      console.error('Get trends error:', error);
      return [];
    }
  }
};

// WOEID (Where On Earth ID) reference:
// 1 - Worldwide
// 23424977 - United States
// 23424819 - United Kingdom
// 23424856 - Pakistan
// 2357024 - New York
// etc.
```

Create `src/api/search.ts`:
```typescript
import { PostsAPI } from './posts';
import db from '../db/models';
import { TweetQueries } from '../db/queries';

export const SearchModule = {
  /**
   * Search and score tweets
   */
  async searchAndScore(query: string, limit: number = 50): Promise<any[]> {
    try {
      console.log(`🔍 Searching for: "${query}"`);

      // Search tweets
      const tweets = await PostsAPI.searchTweets(query, limit);

      // Score tweets
      const scored = tweets.map(tweet => {
        const metrics = tweet.public_metrics;
        const engagement_score = (metrics.like_count * 1) + 
                                (metrics.retweet_count * 2) + 
                                (metrics.reply_count * 3);

        return {
          ...tweet,
          engagement_score: engagement_score,
          score_breakdown: {
            likes: metrics.like_count,
            retweets: metrics.retweet_count,
            replies: metrics.reply_count
          }
        };
      });

      // Sort by engagement
      scored.sort((a, b) => b.engagement_score - a.engagement_score);

      // Save to database
      for (const tweet of scored) {
        await TweetQueries.saveTweet({
          id: tweet.id,
          author_id: tweet.author_id,
          text: tweet.text,
          engagement_score: tweet.engagement_score
        });
      }

      console.log(`✓ Found and scored ${scored.length} tweets`);
      return scored;
    } catch (error) {
      console.error('Search and score error:', error);
      return [];
    }
  }
};
```

---

### Part 6: Scheduler & Main Bot (1 hour)

Create `src/scheduler/jobs.ts`:
```typescript
import cron from 'node-cron';
import { PostsAPI } from '../api/posts';
import { UsersAPI } from '../api/users';
import { TrendsAPI } from '../api/trends';
import { SearchModule } from '../api/search';
import { TweetQueries, UserQueries, ActivityQueries } from '../db/queries';

interface BotConfig {
  userId: string;
  maxLikesPerDay: number;
  maxFollowsPerDay: number;
  maxRetweetsPerDay: number;
  maxPostsPerDay: number;
}

export class BotScheduler {
  private config: BotConfig;
  private isRunning: boolean = false;

  constructor(config: BotConfig) {
    this.config = config;
  }

  /**
   * Start the bot scheduler
   */
  start(): void {
    if (this.isRunning) {
      console.log('⚠️  Bot is already running');
      return;
    }

    this.isRunning = true;
    console.log('🤖 Starting X Bot Scheduler...');

    // Morning routine - 6 AM
    cron.schedule('0 6 * * *', () => this.morningRoutine());

    // Mid-day routine - 12 PM
    cron.schedule('0 12 * * *', () => this.midDayRoutine());

    // Evening routine - 6 PM
    cron.schedule('0 18 * * *', () => this.eveningRoutine());

    // Night routine - 10 PM
    cron.schedule('0 22 * * *', () => this.nightRoutine());

    console.log('✓ Scheduler started with 4 daily routines');
  }

  /**
   * Morning routine - fetch trends and search
   */
  private async morningRoutine(): Promise<void> {
    console.log('\n📅 Starting Morning Routine (6 AM)...');
    try {
      // Get worldwide trends
      const trends = await TrendsAPI.getTrendingTopics(1);
      console.log(`✓ Found ${trends.length} trends:`, trends.slice(0, 5));

      // Search for tweets on each trend (top 3)
      for (const trend of trends.slice(0, 3)) {
        await SearchModule.searchAndScore(trend, 30);
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
      }

      console.log('✓ Morning routine complete');
    } catch (error) {
      console.error('Morning routine error:', error);
    }
  }

  /**
   * Mid-day routine - like and retweet
   */
  private async midDayRoutine(): Promise<void> {
    console.log('\n📅 Starting Mid-Day Routine (12 PM)...');
    try {
      const likesToday = await ActivityQueries.getTodayActionCount('like_tweet');
      const retweetsToday = await ActivityQueries.getTodayActionCount('retweet_tweet');

      // Like phase
      if (likesToday < this.config.maxLikesPerDay) {
        console.log(`📌 Like Phase (${likesToday}/${this.config.maxLikesPerDay})...`);
        const candidates = await TweetQueries.getCandidateTweets(20);

        for (const tweet of candidates) {
          if (likesToday >= this.config.maxLikesPerDay) break;

          const success = await PostsAPI.likeTweet(tweet.id, this.config.userId);
          if (success) {
            await TweetQueries.markLiked(tweet.id);
            likesToday++;
            console.log(`  ♥️  Liked tweet from @${tweet.author_username}`);
          }

          // Random delay 30-60 seconds
          await new Promise(resolve => 
            setTimeout(resolve, Math.random() * 30000 + 30000)
          );
        }
      }

      // Retweet phase
      if (retweetsToday < this.config.maxRetweetsPerDay) {
        console.log(`🔄 Retweet Phase (${retweetsToday}/${this.config.maxRetweetsPerDay})...`);
        const candidates = await TweetQueries.getCandidateTweets(10);

        for (const tweet of candidates) {
          if (retweetsToday >= this.config.maxRetweetsPerDay) break;

          const success = await PostsAPI.retweetTweet(tweet.id, this.config.userId);
          if (success) {
            retweetsToday++;
            console.log(`  🔄 Retweeted from @${tweet.author_username}`);
          }

          // Random delay 5-10 minutes
          await new Promise(resolve => 
            setTimeout(resolve, Math.random() * 300000 + 300000)
          );
        }
      }

      console.log('✓ Mid-day routine complete');
    } catch (error) {
      console.error('Mid-day routine error:', error);
    }
  }

  /**
   * Evening routine - follow and check DMs
   */
  private async eveningRoutine(): Promise<void> {
    console.log('\n📅 Starting Evening Routine (6 PM)...');
    try {
      const followsToday = await ActivityQueries.getTodayActionCount('follow_user');

      if (followsToday < this.config.maxFollowsPerDay) {
        console.log(`👥 Follow Phase (${followsToday}/${this.config.maxFollowsPerDay})...`);
        // TODO: Implement follow logic
        // Get users from likers or similar accounts
      }

      console.log('✓ Evening routine complete');
    } catch (error) {
      console.error('Evening routine error:', error);
    }
  }

  /**
   * Night routine - post content
   */
  private async nightRoutine(): Promise<void> {
    console.log('\n📅 Starting Night Routine (10 PM)...');
    try {
      const postsToday = await ActivityQueries.getTodayActionCount('create_tweet');

      if (postsToday < this.config.maxPostsPerDay) {
        console.log(`✍️  Posting content...`);
        // TODO: Implement AI content generation
        const tweetText = 'Your AI-generated tweet would go here! #XBot';
        await PostsAPI.createTweet(tweetText);
      }

      console.log('✓ Night routine complete');
    } catch (error) {
      console.error('Night routine error:', error);
    }
  }

  /**
   * Stop the scheduler
   */
  stop(): void {
    this.isRunning = false;
    console.log('🛑 Bot scheduler stopped');
  }
}
```

Create `src/index.ts`:
```typescript
import dotenv from 'dotenv';
import db from './db/models';
import auth from './auth/oauth';
import { BotScheduler } from './scheduler/jobs';

dotenv.config();

async function main() {
  try {
    console.log('🚀 Initializing X Bot...\n');

    // Initialize database
    console.log('📊 Initializing database...');
    await db.initialize();

    // Check for credentials
    const botUserId = process.env.BOT_ACCOUNT_ID || 'your_user_id';

    if (botUserId === 'your_user_id') {
      console.log('\n⚠️  Please set BOT_ACCOUNT_ID in your .env file');
      console.log('To get your user ID:');
      console.log('1. Go to https://console.x.com/');
      console.log('2. Create an app and generate credentials');
      console.log('3. Make a request to /2/users/me to get your ID');
      return;
    }

    // Initialize scheduler
    const botConfig = {
      userId: botUserId,
      maxLikesPerDay: parseInt(process.env.MAX_LIKES_PER_DAY || '150'),
      maxFollowsPerDay: parseInt(process.env.MAX_FOLLOWS_PER_DAY || '100'),
      maxRetweetsPerDay: parseInt(process.env.MAX_RETWEETS_PER_DAY || '30'),
      maxPostsPerDay: parseInt(process.env.MAX_POSTS_PER_DAY || '5')
    };

    const scheduler = new BotScheduler(botConfig);
    scheduler.start();

    console.log('\n✓ X Bot is running!');
    console.log(`  - Max likes/day: ${botConfig.maxLikesPerDay}`);
    console.log(`  - Max follows/day: ${botConfig.maxFollowsPerDay}`);
    console.log(`  - Max retweets/day: ${botConfig.maxRetweetsPerDay}`);
    console.log(`  - Max posts/day: ${botConfig.maxPostsPerDay}`);

    // Keep process running
    process.on('SIGINT', () => {
      console.log('\n\n👋 Shutting down...');
      scheduler.stop();
      db.close();
      process.exit(0);
    });

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

main();
```

---

## Running the Bot

### 1. Build TypeScript
```bash
npx tsc
```

### 2. Run the bot
```bash
node dist/index.ts
```

### 3. First-time setup with authentication
```bash
node dist/index.ts auth
# Follow the URL to authenticate with X
# Copy the code and paste it back
```

---

## File Structure Summary
```
x-bot/
├── src/
│   ├── auth/
│   │   ├── oauth.ts (OAuth 2.0 authentication)
│   │   └── credentials.ts (Credential storage)
│   ├── api/
│   │   ├── posts.ts (Posts operations)
│   │   ├── users.ts (Users operations)
│   │   ├── trends.ts (Trends API)
│   │   └── search.ts (Search & score)
│   ├── db/
│   │   ├── models.ts (Database setup)
│   │   └── queries.ts (Database operations)
│   ├── scheduler/
│   │   └── jobs.ts (Cron jobs)
│   └── index.ts (Main entry point)
├── data/
│   ├── bot.db (SQLite database)
│   └── credentials.json (Stored tokens)
├── .env (Configuration)
├── package.json
├── tsconfig.json
└── README.md
```

---

## Next Steps

1. ✅ Set up project structure
2. ✅ Implement authentication
3. ✅ Set up database
4. ✅ Create API wrappers
5. ⏳ Add AI integration (OpenAI)
6. ⏳ Implement error handling & retries
7. ⏳ Add monitoring & logging
8. ⏳ Test thoroughly
9. ⏳ Deploy to server

---

## Common Issues & Fixes

### "Rate limited"
- Reduce MAX_LIKES_PER_DAY, MAX_FOLLOWS_PER_DAY
- Increase delays between operations

### "Invalid credentials"
- Check .env file is correctly formatted
- Regenerate tokens from console.x.com
- Ensure OAuth scopes are correct

### "Database locked"
- Restart bot
- Check for multiple instances running
- Verify database file isn't corrupted

### "Tweet not found"
- Tweet may have been deleted
- Check tweet ID is correct
- Verify tweet still exists

---

## Monitoring & Logs

Check activity logs:
```bash
sqlite3 data/bot.db "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 20;"
```

View API usage:
```bash
sqlite3 data/bot.db "SELECT action_type, COUNT(*) as count FROM activity_log WHERE DATE(timestamp) = DATE('now') GROUP BY action_type;"
```
