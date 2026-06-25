import logging
import uuid
from database.models import MainRide, ArchiveRide, MainPayment, ArchivePayment
from database.session import get_db
from policies.rules_engine import RetentionRulesEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s")
logger = logging.getLogger(__name__)


def uuid_to_bigint(uuid_val):
    if isinstance(uuid_val, str):
        uuid_val = uuid.UUID(uuid_val)
    return uuid_val.int % (2**63 - 1)


def run_archiver():
    logger.info("Starting Archiver Job: Moving old data to archive schema...")

    rules_engine = RetentionRulesEngine()
    ride_threshold = rules_engine.get_ride_archive_threshold()
    payment_threshold = rules_engine.get_payment_preservation_threshold()

    logger.info(f"Ride archiving threshold: {ride_threshold.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"Payment preservation check threshold: {payment_threshold.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        with get_db() as db:
            # Step 1: Find rides to archive (rides that have ended before threshold)
            rides_to_archive = db.query(MainRide).filter(
                MainRide.end_time <= ride_threshold
            ).all()

            if not rides_to_archive:
                logger.info("No old rides found for archiving. Main schema is clean.")
            else:
                logger.info(f"Found {len(rides_to_archive)} rides to archive.")

                archive_ride_records = []
                ride_ids_to_delete = []

                for ride in rides_to_archive:
                    archive_ride = ArchiveRide(
                        id=uuid_to_bigint(ride.id),
                        user_id=uuid_to_bigint(ride.user_id),
                        car_id=uuid_to_bigint(ride.vehicle_id),
                        status=ride.status,
                        end_reason=None,
                        started_at=ride.start_time,
                        finished_at=ride.end_time,
                        total_cost=ride.total_cost,
                        archived_at=ride.end_time or ride.created_at
                    )
                    archive_ride_records.append(archive_ride)
                    ride_ids_to_delete.append(ride.id)

                db.add_all(archive_ride_records)
                db.flush()
                logger.info(f"Successfully archived {len(archive_ride_records)} ride records.")

                db.query(MainTelemetry).filter(MainTelemetry.ride_id.in_(ride_ids_to_delete)).delete(synchronize_session=False)
                logger.info(f"Removed telemetry records for {len(ride_ids_to_delete)} archived rides.")

                db.query(MainPayment).filter(MainPayment.ride_id.in_(ride_ids_to_delete)).delete(synchronize_session=False)
                logger.info(f"Removed payment records for {len(ride_ids_to_delete)} archived rides.")

                db.query(MainRide).filter(MainRide.id.in_(ride_ids_to_delete)).delete(synchronize_session=False)
                logger.info(f"Removed {len(ride_ids_to_delete)} archived rides from main schema.")

            # Step 2: Find and archive payments that are old enough
            payments_to_archive = db.query(MainPayment).filter(
                MainPayment.created_at <= payment_threshold
            ).all()

            if payments_to_archive:
                logger.info(f"Found {len(payments_to_archive)} payments to archive.")

                archive_payment_records = []
                payment_ids_to_delete = []

                for payment in payments_to_archive:
                    archive_payment = ArchivePayment(
                        id=payment.id,
                        ride_id=payment.ride_id,
                        user_id=payment.user_id,
                        amount=payment.amount,
                        currency=payment.currency,
                        status=payment.status,
                        payment_method=payment.payment_method,
                        created_at=payment.created_at,
                        archived_at=payment.created_at
                    )
                    archive_payment_records.append(archive_payment)
                    payment_ids_to_delete.append(payment.id)

                db.add_all(archive_payment_records)
                db.flush()
                logger.info(f"Successfully archived {len(archive_payment_records)} payment records.")

                db.query(MainPayment).filter(MainPayment.id.in_(payment_ids_to_delete)).delete(synchronize_session=False)
                logger.info(f"Removed {len(payment_ids_to_delete)} archived payments from main schema.")
            else:
                logger.info("No payments found for archiving.")

            logger.info("Archiver job completed successfully.")

    except Exception as e:
        error_config = rules_engine.get_error_handling_config()
        logger.error(f"Archiver job failed: {e}. Retry configuration: {error_config}")

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
    run_archiver()
