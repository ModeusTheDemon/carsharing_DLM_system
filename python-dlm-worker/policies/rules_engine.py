import json
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
    
    def get_telemetry_cleanup_threshold(self) -> datetime:
        """Get threshold date for telemetry data cleanup (15 days)"""
        days = self.config["telemetry_policy"]["cleanup_after_days"]
        return datetime.now(timezone.utc) - timedelta(days=days)
    
    def get_ride_archive_threshold(self) -> datetime:
        """Get threshold date for ride archiving (3 months = 90 days)"""
        days = self.config["rides_policy"]["archive_after_days"]
        return datetime.now(timezone.utc) - timedelta(days=days)
    
    def get_payment_preservation_threshold(self) -> datetime:
        """Get threshold date for payment preservation (5 years)"""
        years = self.config["payments_policy"]["preserve_for_years"]
        return datetime.now(timezone.utc) - timedelta(days=years * 365)
    
    def should_anonymize_immediately(self) -> bool:
        """Check if user data should be anonymized immediately upon deletion"""
        return self.config["users_policy"]["anonymize_immediately"]
    
    def get_schedule_config(self) -> Dict[str, str]:
        """Get scheduling configuration"""
        return {
            "archiver": self.config["scheduling"]["archiver_cron"],
            "anonymizer": self.config["scheduling"]["anonymizer_cron"],
            "cleaner": self.config["scheduling"]["cleaner_cron"]
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
        Data Lifecycle Management Configuration:
        - Telemetry cleanup: {self.config['telemetry_policy']['cleanup_after_days']} days
        - Ride archiving: {self.config['rides_policy']['archive_after_days']} days
        - User anonymization: {'Immediate' if self.should_anonymize_immediately() else 'Delayed'}
        - Payment preservation: {self.config['payments_policy']['preserve_for_years']} years
        - Scheduling: 
          * Archiver: {self.config['scheduling']['archiver_cron']}
          * Anonymizer: {self.config['scheduling']['anonymizer_cron']}
          * Cleaner: {self.config['scheduling']['cleaner_cron']}
        - Error handling: {self.config['error_handling']['max_retries']} retries with {self.config['error_handling']['retry_delay_seconds']}s delay
        """