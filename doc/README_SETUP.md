# X Growth Tool - Python Setup

## Quick Start

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Edit `.env` file and add:
- Your X API credentials (already configured)
- MongoDB URI (local or Atlas)
- OpenAI API key

### 4. Setup MongoDB
**Option A: Local MongoDB**
```bash
brew install mongodb-community
brew services start mongodb-community
```

**Option B: MongoDB Atlas (Cloud)**
- Sign up at mongodb.com/cloud/atlas
- Create free cluster
- Get connection string
- Update MONGODB_URI in .env

### 5. Run the Application
```bash
python src/main.py
```

## Project Structure
```
src/
├── config/          # Configuration management
├── database/        # MongoDB connection and models
├── auth/            # X API authentication
├── api/             # X API wrapper
├── ai/              # OpenAI integration
├── operations/      # Core engagement operations
├── utils/           # Utilities (logger, delays)
└── main.py          # Entry point
```
