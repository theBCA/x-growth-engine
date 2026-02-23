"""Database backup and restore utilities."""
import subprocess
from datetime import datetime
from pathlib import Path
import os
import tarfile
import shutil
from utils.logger import logger
from config import Config


class BackupManager:
    """Handles MongoDB backups and restoration."""
    
    BACKUP_DIR = Path("./backups")
    MAX_BACKUPS = 30  # Keep 30 days of backups
    
    @staticmethod
    def ensure_backup_dir():
        """Ensure backup directory exists."""
        BackupManager.BACKUP_DIR.mkdir(exist_ok=True)
        logger.debug(f"Backup directory: {BackupManager.BACKUP_DIR.absolute()}")
    
    @staticmethod
    def backup_database() -> str:
        """
        Create a backup of the MongoDB database.
        
        Returns:
            Path to backup file, or None if failed
        """
        BackupManager.ensure_backup_dir()
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dump_dir = f"/tmp/dump_{timestamp}"
        backup_file = BackupManager.BACKUP_DIR / f"x-growth_{timestamp}.tar.gz"
        
        try:
            logger.info("Starting database backup...")
            
            # Run mongodump
            result = subprocess.run([
                "mongodump",
                f"--uri={Config.MONGODB_URI}",
                f"--out={dump_dir}"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"mongodump failed: {result.stderr}")
                return None
            
            # Compress dump
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(dump_dir, arcname=os.path.basename(dump_dir))
            
            # Clean up temp dump
            shutil.rmtree(dump_dir, ignore_errors=True)
            
            # Get backup size
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            
            logger.info(f"✓ Database backup created: {backup_file.name} ({size_mb:.2f} MB)")
            
            # Cleanup old backups
            BackupManager.cleanup_old_backups()
            
            return str(backup_file)
            
        except subprocess.TimeoutExpired:
            logger.error("Backup timeout after 5 minutes")
            return None
        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            return None
    
    @staticmethod
    def restore_database(backup_file: str) -> bool:
        """
        Restore MongoDB from a backup file.
        
        Args:
            backup_file: Path to backup .tar.gz file
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extract_dir = f"/tmp/restore_{timestamp}"
        
        try:
            logger.info(f"Starting database restore from {backup_path.name}...")
            
            # Extract backup
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # Find dump directory
            dump_dirs = list(Path(extract_dir).glob("dump_*"))
            if not dump_dirs:
                logger.error("No dump directory found in backup")
                return False
            
            dump_dir = dump_dirs[0]
            
            # Run mongorestore
            result = subprocess.run([
                "mongorestore",
                f"--uri={Config.MONGODB_URI}",
                "--drop",  # Drop existing collections
                str(dump_dir)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"mongorestore failed: {result.stderr}")
                return False
            
            # Clean up temp files
            shutil.rmtree(extract_dir, ignore_errors=True)
            
            logger.info(f"✓ Database restored from {backup_path.name}")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Restore timeout after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False
    
    @staticmethod
    def cleanup_old_backups() -> None:
        """Remove backups older than MAX_BACKUPS days."""
        try:
            backups = sorted(BackupManager.BACKUP_DIR.glob("x-growth_*.tar.gz"))
            
            if len(backups) > BackupManager.MAX_BACKUPS:
                to_delete = backups[:-BackupManager.MAX_BACKUPS]
                for backup in to_delete:
                    backup.unlink()
                    logger.info(f"Deleted old backup: {backup.name}")
                
                logger.info(f"✓ Cleaned up {len(to_delete)} old backups")
                
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    @staticmethod
    def list_backups() -> list:
        """
        List all available backups.
        
        Returns:
            List of backup file paths sorted by date (newest first)
        """
        BackupManager.ensure_backup_dir()
        backups = sorted(
            BackupManager.BACKUP_DIR.glob("x-growth_*.tar.gz"),
            reverse=True
        )
        
        result = []
        for backup in backups:
            size_mb = backup.stat().st_size / (1024 * 1024)
            timestamp = backup.stem.replace("x-growth_", "")
            result.append({
                "path": str(backup),
                "name": backup.name,
                "size_mb": round(size_mb, 2),
                "timestamp": timestamp,
                "created": datetime.fromtimestamp(backup.stat().st_mtime)
            })
        
        return result
    
    @staticmethod
    def get_latest_backup() -> str:
        """
        Get path to most recent backup.
        
        Returns:
            Path to latest backup, or None if no backups exist
        """
        backups = BackupManager.list_backups()
        return backups[0]["path"] if backups else None
