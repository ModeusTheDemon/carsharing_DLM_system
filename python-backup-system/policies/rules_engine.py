# import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from .config_validator import ConfigValidator


class RetentionRulesEngine:
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "retention.json")
        
        # Load and validate configuration
        self.config = ConfigValidator.validate_config_file(config_path)
    
    def get_healthcheck_threshold(self) -> datetime:
        """Get threshold date for healthcheck (5 minutes)"""
        minutes = self.config["healthcheck_policy"]["healthcheck_every_minutes"]
        return datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    def get_inc_save_threshold(self) -> datetime:
        """Get threshold date for increment save (1 week = 7 days)"""
        weeks = self.config["save_inc_policy"]["save_inc_every_weeks"]
        return datetime.now(timezone.utc) - timedelta(weeks=weeks)
    
    def get_full_save_threshold(self) -> datetime:
        """Get threshold date for full save (1 mounth = 30 days)"""
        mounths = self.config["save_full_policy"]["save_full_every_months"]
        return datetime.now(timezone.utc) - timedelta(days=mounths * 30)
    
    def get_schedule_config(self) -> Dict[str, str]:
        """Get scheduling configuration"""
        return {
            "healthcheck": self.config["scheduling"]["healthcheck_cron"],
            "inc_saver": self.config["scheduling"]["save_inc_cron"],
            "full_saver": self.config["scheduling"]["save_full_cron"]
        }
    
    def get_error_handling_config(self) -> Dict[str, Any]:
        """Get error handling configuration"""
        return {
            "max_retries": self.config["error_handling"]["max_retries"],
            "retry_delay_seconds": self.config["error_handling"]["retry_delay_seconds"],
            "exponential_backoff": self.config["error_handling"]["exponential_backoff"]
        }
    
    def get_config_summary(self) -> str:
        """Get human-readable configuration summary"""
        return f"""
        Backup System Configuration:
        - Healthcheck: {self.config['healthcheck_policy']['healthcheck_every_minutes']} minutes
        - Increment save: {self.config['save_inc_policy']['save_inc_every_weeks']} weeks
        - Full save: {self.config['save_full_policy']['save_full_every_months']} mounths
        - Scheduling: 
          * Checker: {self.config['scheduling']['healthcheck_cron']}
          * Saver_incremental: {self.config['scheduling']['save_inc_cron']}
          * Saver_full: {self.config['scheduling']['save_full_cron']}
        - Error handling: {self.config['error_handling']['max_retries']} retries with {self.config['error_handling']['retry_delay_seconds']}s delay
        """