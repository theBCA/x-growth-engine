# X Growth Engine - Execution Plan

## Phase 1: Project Setup (Day 1-2)

### Step 1.1: Initialize Project Structure
```bash
cd /Users/berk.arslan/x-bot

# Create directories
mkdir -p src/{auth,api,db,scheduler,utils,services}
mkdir -p src/{config,types,hooks}
mkdir -p logs
mkdir -p data

# Create main files
touch src/index.ts
touch src/config/config.ts
touch src/types/index.ts
```

### Step 1.2: Setup package.json
```bash
npm init -y
```

Update package.json with:
```json
{
  "name": "x-growth-engine",
  "version": "1.0.0",
  "description": "Enterprise X growth automation tool with AI integration",
  "main": "dist/index.js",
  "scripts": {
    "dev": "ts-node src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "lint": "eslint src/**/*.ts"
  },
  "keywords": ["x", "twitter", "growth", "automation", "ai"],
  "author": "",
  "license": "MIT",
  "dependencies": {
    "axios": "^1.6.0",
    "dotenv": "^16.0.0",
    "node-cron": "^3.0.0",
    "sqlite3": "^5.1.0",
    "openai": "^4.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "ts-node": "^10.9.0",
    "@types/node-cron": "^3.0.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0"
  }
}
```

### Step 1.3: Setup TypeScript
```bash
npx tsc --init
```

Create tsconfig.json:
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
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

### Step 1.4: Install Dependencies
```bash
npm install
npm install --save-dev @types/node @types/node-cron typescript ts-node
```

---

## Phase 2: Core Implementation (Day 3-5)

### Step 2.1: Create Config Module
**File:** `src/config/config.ts`

```typescript
import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // X API
  bearerToken: process.env.bearerToken!,
  consumerKey: process.env.consumerKey!,
  consumerKeySecret: process.env.consumerKeySecret!,
  accessToken: process.env.accessToken!,
  accessTokenSecret: process.env.accessTokenSecret!,

  // Language
  language: (process.env.BOT_LANGUAGE || 'en') as 'en' | 'tr',

  // OpenAI (optional)
  openaiKey: process.env.OPENAI_API_KEY,

  // Bot Settings
  maxDailyActions: 100,
  maxLikesPerDay: 50,
  maxRetweetsPerDay: 20,
  maxFollowsPerDay: 30,
};

// Validate required credentials
if (!config.bearerToken || !config.consumerKey) {
  throw new Error('Missing required X API credentials in .env');
}
```

### Step 2.2: Create Types
**File:** `src/types/index.ts`

```typescript
export interface Tweet {
  id: string;
  author_id: string;
  author_username: string;
  text: string;
  engagement_score: number;
  liked: boolean;
  retweeted: boolean;
  created_at: string;
}

export interface User {
  id: string;
  username: string;
  followers_count: number;
  following_count: number;
}

export interface ActivityLog {
  id: string;
  action_type: 'like' | 'retweet' | 'follow' | 'post' | 'dm';
  target_id: string;
  status: 'success' | 'failed' | 'pending';
  timestamp: string;
}

export interface BotSettings {
  maxDailyActions: number;
  maxLikesPerDay: number;
  maxRetweetsPerDay: number;
  maxFollowsPerDay: number;
}
```

### Step 2.3: Create Database Module
**File:** `src/db/database.ts`

```typescript
import sqlite3 from 'sqlite3';
import path from 'path';

const dbPath = path.join(process.cwd(), 'data', 'bot.db');
const db = new sqlite3.Database(dbPath);

export function initializeDatabase() {
  return new Promise<void>((resolve, reject) => {
    db.serialize(() => {
      // Tweets table
      db.run(`
        CREATE TABLE IF NOT EXISTS tweets (
          id TEXT PRIMARY KEY,
          author_id TEXT,
          author_username TEXT,
          text TEXT,
          engagement_score REAL,
          liked BOOLEAN DEFAULT 0,
          retweeted BOOLEAN DEFAULT 0,
          created_at TEXT,
          interaction_timestamp TEXT
        )
      `);

      // Users table
      db.run(`
        CREATE TABLE IF NOT EXISTS users (
          id TEXT PRIMARY KEY,
          username TEXT UNIQUE,
          followers_count INTEGER,
          following_count INTEGER,
          followed BOOLEAN DEFAULT 0,
          follow_timestamp TEXT
        )
      `);

      // Trends table
      db.run(`
        CREATE TABLE IF NOT EXISTS trends (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          trend_name TEXT UNIQUE,
          volume INTEGER,
          engagement_score REAL,
          last_checked TEXT
        )
      `);

      // Activity Log
      db.run(`
        CREATE TABLE IF NOT EXISTS activity_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          action_type TEXT,
          target_id TEXT,
          status TEXT,
          timestamp TEXT,
          details TEXT
        )
      `);

      // DMs table
      db.run(`
        CREATE TABLE IF NOT EXISTS dms (
          id TEXT PRIMARY KEY,
          sender_id TEXT,
          sender_username TEXT,
          message_text TEXT,
          replied BOOLEAN DEFAULT 0,
          ai_response TEXT,
          created_at TEXT,
          reply_timestamp TEXT
        )
      `, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  });
}

export default db;
```

### Step 2.4: Create X API Module
**File:** `src/api/xapi.ts`

```typescript
import axios from 'axios';
import { config } from '../config/config';

const API_BASE = 'https://api.twitter.com/2';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Authorization': `Bearer ${config.bearerToken}`,
    'User-Agent': 'X-Growth-Engine/1.0'
  }
});

export class XAPI {
  // Search tweets
  async searchTweets(query: string, maxResults: number = 10) {
    try {
      const response = await apiClient.get('/tweets/search/recent', {
        params: {
          query,
          'max_results': maxResults,
          'tweet.fields': 'public_metrics,author_id,created_at'
        }
      });
      return response.data.data || [];
    } catch (error) {
      console.error('Error searching tweets:', error);
      return [];
    }
  }

  // Get trending topics
  async getTrends(woeid: number = 1) {
    try {
      // Using v1.1 endpoint for trends
      const response = await axios.get(`https://api.twitter.com/1.1/trends/place.json`, {
        params: { id: woeid },
        headers: { 'Authorization': `Bearer ${config.bearerToken}` }
      });
      return response.data[0]?.trends || [];
    } catch (error) {
      console.error('Error getting trends:', error);
      return [];
    }
  }

  // Like tweet
  async likeTweet(tweetId: string) {
    try {
      await apiClient.post(`/users/:id/likes`, {
        tweet_id: tweetId
      });
      return { success: true };
    } catch (error) {
      console.error('Error liking tweet:', error);
      return { success: false, error };
    }
  }

  // Retweet
  async retweet(tweetId: string) {
    try {
      await apiClient.post(`/users/:id/retweets`, {
        tweet_id: tweetId
      });
      return { success: true };
    } catch (error) {
      console.error('Error retweeting:', error);
      return { success: false, error };
    }
  }

  // Follow user
  async followUser(userId: string) {
    try {
      await apiClient.post(`/users/:id/following`, {
        target_user_id: userId
      });
      return { success: true };
    } catch (error) {
      console.error('Error following user:', error);
      return { success: false, error };
    }
  }

  // Post tweet
  async postTweet(text: string) {
    try {
      const response = await apiClient.post('/tweets', {
        text
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error posting tweet:', error);
      return { success: false, error };
    }
  }
}

export default new XAPI();
```

### Step 2.5: Create Scheduler
**File:** `src/scheduler/scheduler.ts`

```typescript
import cron from 'node-cron';
import xapi from '../api/xapi';
import db from '../db/database';

export class BotScheduler {
  // Morning routine (9 AM)
  schedulesMorning() {
    cron.schedule('0 9 * * *', async () => {
      console.log('🌅 Starting morning routine...');
      
      // Search and engage with relevant tweets
      const tweets = await xapi.searchTweets('tech startup', 10);
      
      for (const tweet of tweets) {
        // Like high engagement tweets
        await xapi.likeTweet(tweet.id);
        
        // Log activity
        db.run(
          'INSERT INTO activity_log (action_type, target_id, status, timestamp) VALUES (?, ?, ?, ?)',
          ['like', tweet.id, 'success', new Date().toISOString()]
        );
      }
    });
  }

  // Mid-day routine (1 PM)
  schedulesMidday() {
    cron.schedule('0 13 * * *', async () => {
      console.log('☀️ Starting mid-day routine...');
      
      const tweets = await xapi.searchTweets('AI technology', 10);
      
      for (const tweet of tweets) {
        // Retweet relevant content
        await xapi.retweet(tweet.id);
        
        db.run(
          'INSERT INTO activity_log (action_type, target_id, status, timestamp) VALUES (?, ?, ?, ?)',
          ['retweet', tweet.id, 'success', new Date().toISOString()]
        );
      }
    });
  }

  // Evening routine (6 PM)
  schedulesEvening() {
    cron.schedule('0 18 * * *', async () => {
      console.log('🌆 Starting evening routine...');
      
      // Get trending topics
      const trends = await xapi.getTrends();
      
      // Follow relevant users
      const users = await xapi.searchTweets('#growth', 5);
      
      console.log(`Found ${trends.length} trends and ${users.length} users`);
    });
  }

  startAll() {
    console.log('🤖 Bot scheduler started');
    this.schedulesMorning();
    this.schedulesMidday();
    this.schedulesEvening();
  }
}

export default new BotScheduler();
```

### Step 2.6: Create Main Entry Point
**File:** `src/index.ts`

```typescript
import { config } from './config/config';
import { initializeDatabase } from './db/database';
import scheduler from './scheduler/scheduler';

async function main() {
  console.log('🚀 X Growth Engine Starting...');
  console.log(`📝 Language: ${config.language}`);
  
  try {
    // Initialize database
    console.log('📊 Initializing database...');
    await initializeDatabase();
    console.log('✅ Database ready');
    
    // Start scheduler
    console.log('⏰ Starting scheduler...');
    scheduler.startAll();
    console.log('✅ Scheduler running');
    
    console.log('🎯 Bot is now active and running');
    console.log('Press Ctrl+C to stop');
    
    // Keep process alive
    process.on('SIGINT', () => {
      console.log('\n👋 Shutting down...');
      process.exit(0);
    });
    
  } catch (error) {
    console.error('❌ Error starting bot:', error);
    process.exit(1);
  }
}

main();
```

---

## Phase 3: Testing & Validation (Day 6)

### Step 3.1: Test Database
```bash
npm run build
npm start
# Should see:
# 🚀 X Growth Engine Starting...
# 📊 Initializing database...
# ✅ Database ready
# ⏰ Starting scheduler...
# ✅ Scheduler running
```

### Step 3.2: Test API Connections
```bash
# Check X API connectivity
curl -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  "https://api.twitter.com/2/tweets/search/recent?query=test"
```

### Step 3.3: Monitor Logs
```bash
# Check database
sqlite3 data/bot.db "SELECT * FROM activity_log LIMIT 10;"

# Check logs
tail -f logs/bot.log
```

---

## Phase 4: Optimization (Day 7)

### Step 4.1: Add Rate Limiting
```typescript
// src/utils/rateLimit.ts
export class RateLimit {
  private limits: Map<string, { count: number; reset: number }> = new Map();
  
  check(key: string, limit: number, windowMs: number): boolean {
    const now = Date.now();
    const entry = this.limits.get(key);
    
    if (!entry || entry.reset < now) {
      this.limits.set(key, { count: 1, reset: now + windowMs });
      return true;
    }
    
    if (entry.count >= limit) {
      return false;
    }
    
    entry.count++;
    return true;
  }
}
```

### Step 4.2: Add Error Handling
```typescript
// Wrap API calls in try-catch
// Log errors to database
// Implement retry logic
```

### Step 4.3: Add Monitoring
```typescript
// src/utils/monitor.ts
export class Monitor {
  logActivity(action: string, success: boolean) {
    // Log to database
    // Alert if too many failures
  }
  
  getStats() {
    // Return daily/weekly stats
  }
}
```

---

## Phase 5: Deployment (Day 8)

### Step 5.1: Prepare for Production
```bash
# Build
npm run build

# Test build
npm start

# Should work without typescript
```

### Step 5.2: Setup Environment
```bash
# Production .env
BOT_LANGUAGE=en
# (Keep credentials secret in production)
```

### Step 5.3: Deploy Options
- **Option A:** Local server (always on)
- **Option B:** Cloud server (AWS, DigitalOcean, Heroku)
- **Option C:** Cron job on VPS
- **Option D:** Docker container

---

## Quick Command Reference

```bash
# Setup
npm install
npm run build

# Development
npm run dev

# Production
npm start

# Database queries
sqlite3 data/bot.db

# Logs
tail -f logs/bot.log

# Git push (when ready)
git add .
git commit -m "Implement core bot functionality"
git push origin main
```

---

## Timeline Summary

| Phase | Days | Task |
|-------|------|------|
| Setup | 1-2 | Project structure, dependencies |
| Implementation | 3-5 | Core modules, API, scheduler |
| Testing | 6 | Validation, monitoring |
| Optimization | 7 | Rate limiting, error handling |
| Deployment | 8 | Production setup, launch |

---

## Success Metrics

✅ Database initialized  
✅ API connections working  
✅ Scheduler running  
✅ Activities logged  
✅ No errors in logs  
✅ Bot running 24/7  

---

**Ready to start? Begin with Step 1.1!** 🚀
