"""Main entry point for X growth automation."""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import run_growth_strategy
from utils.logger import logger
from database import db
from config import Config


def main():
    """Main application entry point."""
    try:
        logger.info("=" * 60)
        logger.info("🚀 X Growth Engine Starting...")
        logger.info("=" * 60)
        
        # Validate configuration first
        logger.info("Validating configuration...")
        Config.validate()
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        db.connect()
        
        # Run optimized growth strategy
        logger.info("Starting optimized growth strategy...")
        run_growth_strategy()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Growth Engine Completed Successfully")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if db.client:
            db.disconnect()


if __name__ == "__main__":
    main()
