import json
import os
from typing import Dict, Any
import jsonschema
from jsonschema import validate


class ConfigValidator:
    SCHEMA = {
        "type": "object",
        "properties": {
            "healthcheck_policy": {
                "type": "object",
                "properties": {
                    "healthcheck_every_minutes": {"type": "number", "minimum": 1, "maximum": 59},
                    "description": {"type": "string"}
                },
                "required": ["healthcheck_every_minutes"],
                "additionalProperties": False
            },
            
            "save_inc_policy": {
                "type": "object",
                "properties": {
                    "save_inc_every_weeks": {"type": "number", "minimum": 1, "maximum": 4},
                    "description": {"type": "string"}
                },
                "required": ["save_inc_every_weeks"],
                "additionalProperties": False
            },
            
            "save_full_policy": {
                "type": "object",
                "properties": {
                    "save_full_every_months": {"type": "number", "minimum": 1, "maximum": 12},
                    "description": {"type": "string"}
                },
                "required": ["save_full_every_months"],
                "additionalProperties": False
            },
            
            "scheduling": {
                "type": "object",
                "properties": {
                    "healthcheck_cron": {"type": "string", "pattern": "^[0-9*/, -]+$"},
                    "save_inc_cron":    {"type": "string", "pattern": "^[0-9*/, -]+$"},
                    "save_full_cron":   {"type": "string", "pattern": "^[0-9*/, -]+$"},
                    "description": {"type": "string"}
                },
                "required": ["healthcheck_cron", "save_inc_cron", "save_full_cron"],
                "additionalProperties": False
            },
            
            "error_handling": {
                "type": "object",
                "properties": {
                    "max_retries": {"type": "number", "minimum": 0, "maximum": 10},
                    "retry_delay_seconds": {"type": "number", "minimum": 1, "maximum": 3600},
                    "exponential_backoff": {"type": "boolean"},
                    "description": {"type": "string"}
                },
                "required": ["max_retries", "retry_delay_seconds", "exponential_backoff"],
                "additionalProperties": False
            }
        },
        "required": [
            "healthcheck_policy", 
            "save_inc_policy", 
            "save_full_policy", 
            "scheduling",
            "error_handling"
        ],
        "additionalProperties": False
    }
    
    @classmethod
    def validate_config_file(cls, config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return cls.validate_config(config)
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validate(instance=config, schema=cls.SCHEMA)
            
            cls._validate_business_rules(config)
            
            return config
            
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}") from e
    
    @classmethod
    def _validate_business_rules(cls, config: Dict[str, Any]) -> None:
        save_inc_weeks = config["save_inc_policy"]["save_inc_every_weeks"]
        save_inc_days = save_inc_weeks * 7
        save_full_months = config["save_full_policy"]["save_full_every_months"]
        save_full_days = save_full_months * 30 # assert that all mounths have only 30 days
        
        if save_inc_days >= save_full_days:
            raise ValueError(
                "Error! Incriment saving shold be more often than full save"
                f"inc save in days: {save_inc_days}, full save in days: {save_full_days}"
            )
        
        cron_fields = ["healthcheck_cron", "save_inc_cron", "save_full_cron"]
        for field in cron_fields:
            cron = config["scheduling"][field]
            parts = cron.split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression '{cron}' for {field}. Expected 5 parts.")
    
    @classmethod
    def generate_default_config(cls) -> Dict[str, Any]:
        return {
            "healthcheck_policy": {
                "healthcheck_every_minutes": 5
            },

            "save_inc_policy": {
                "save_inc_every_weeks": 1
            },

            "save_full_policy": {
                "save_full_every_months": 1
            },

            "scheduling": {
                "healthcheck_cron": "*/5 * * * *",
                "save_inc_cron": "0 1 * * 1",
                "save_full_cron": "0 0 1 * *"
            },

            "error_handling": {
                "max_retries": 3,
                "retry_delay_seconds": 60,
                "exponential_backoff": True
            }
        }
    
    @classmethod
    def create_default_config_file(cls, config_path: str) -> None:
        default_config = cls.generate_default_config()
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"Created default configuration file: {config_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = os.path.join(os.path.dirname(__file__), "retention.json")
    
    try:
        config = ConfigValidator.validate_config_file(config_file)
        print(f"Configuration is valid: {config_file}")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        sys.exit(1)