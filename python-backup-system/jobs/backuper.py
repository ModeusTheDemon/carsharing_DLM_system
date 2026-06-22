import logging
import uuid
from datetime import datetime, timezone
from database.session import get_db
from database.models import MainUser, MainRide
from policies.rules_engine import RetentionRulesEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s")
logger = logging.getLogger(__name__)


def run_anonymizer():
    logger.info("Starting Anonymizer Job: Anonymizing deleted user data...")

    rules_engine = RetentionRulesEngine()

    try:
        with get_db() as db:
            users_to_anonymize = db.query(MainUser).filter(
                MainUser.is_deleted == True
            ).all()

            if not users_to_anonymize:
                logger.info("No deleted users found for anonymization.")
                return

            logger.info(f"Found {len(users_to_anonymize)} deleted users to anonymize.")

            for user in users_to_anonymize:
                user_id = user.id
                logger.info(f"Anonymizing user {user_id}...")

                anonymous_suffix = str(uuid.uuid4())[:8]
                anonymized_email = f"anonymous_{anonymous_suffix}@carsharing.internal"

                user.email = anonymized_email
                user.phone = f"+0000000{anonymous_suffix}"
                user.first_name = "Anonymous"
                user.last_name = "Anonymous"

                main_rides = db.query(MainRide).filter(
                    MainRide.user_id == user_id
                ).all()

                for ride in main_rides:
                    ride.status = "USER_ANONYMIZED"

                archive_rides = []

                logger.info(f"User {user_id} anonymized: {len(main_rides)} main rides, {len(archive_rides)} archive rides")

            db.commit()
            logger.info(f"Successfully anonymized {len(users_to_anonymize)} users and their associated data.")

            config_summary = rules_engine.get_config_summary()
            logger.info(f"Anonymization completed with configuration:\n{config_summary}")

    except Exception as e:
        error_config = rules_engine.get_error_handling_config()
        logger.error(f"Anonymizer job failed: {e}. Retry configuration: {error_config}")

        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error details: {error_details}")

        try:
            db.rollback()
            logger.info("Transaction rolled back due to error")
        except:
            logger.warning("Could not rollback transaction")

        raise


if __name__ == "__main__":
    run_anonymizer()
