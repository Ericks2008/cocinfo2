# logger_config.py
import logging
import os
import json
from google.cloud import logging as cloud_logging
from google.cloud.logging.handlers import CloudLoggingHandler

def setup_logging():
    """
    Configures the Python logging module to send logs to Google Cloud Logging.
    It automatically detects the environment (local vs. Google Cloud)
    and adjusts logging accordingly.
    """
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Default level for all handlers

    # Prevent duplicate loggers if setup_logging is called multiple times
    if not logger.handlers:
        # Check if running in a Google Cloud environment (App Engine, Cloud Run, Cloud Functions)
        # In these environments, stdout/stderr are typically captured by Google Cloud Logging
        # and automatically structured. Using CloudLoggingHandler directly might cause duplicates
        # or less optimal structuring than the native agents.
        if os.environ.get('GAE_ENV') or os.environ.get('K_SERVICE') or os.environ.get('FUNCTION_NAME'):
            # Running on Google Cloud:
            # We rely on the built-in logging agent to capture stdout/stderr.
            # Configure a StreamHandler to output JSON to stdout.
            # Google Cloud Logging will automatically parse JSON logs into structured fields.
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(JsonFormatter())
            logger.addHandler(stream_handler)
            logger.info("Configured logging for Google Cloud environment (JSON to stdout)")
        else:
            # Running locally or in a non-Google Cloud environment:
            # Use the CloudLoggingHandler to send logs directly to Cloud Logging.
            # This also provides good local debugging by printing to console.
            client = cloud_logging.Client()
            handler = CloudLoggingHandler(client)
            logger.addHandler(handler)
            logger.info("Configured logging for local environment (CloudLoggingHandler)")

            # Optional: Add a StreamHandler for local console output if CloudLoggingHandler
            # doesn't automatically print to console in your specific setup
            # (CloudLoggingHandler typically sends to network, not necessarily console).
            # If you want local console output AND Cloud Logging, add this:
            # local_console_handler = logging.StreamHandler()
            # local_console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            # logger.addHandler(local_console_handler)

    return logger

class JsonFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as JSON, suitable for
    Google Cloud Logging's structured logging.
    """
    def format(self, record):
        # Base fields from the LogRecord
        log_entry = {
            "message": record.getMessage(),
            "severity": record.levelname,
            "timestamp": {
                "seconds": int(record.created),
                "nanos": int(record.msecs * 1_000_000),
            },
            "python_logger": record.name,
            "line_number": record.lineno,
            "filename": record.filename,
            "function_name": record.funcName,
        }

        # Add custom fields passed via `extra` argument in logging calls
        if hasattr(record, 'json_fields'):
            log_entry.update(record.json_fields)
        if hasattr(record, 'labels'):
            log_entry['labels'] = record.labels
        if hasattr(record, 'http_request'):
            log_entry['httpRequest'] = record.http_request
        if hasattr(record, 'trace'):
            log_entry['logging.googleapis.com/trace'] = record.trace
        if hasattr(record, 'span_id'):
            log_entry['logging.googleapis.com/span_id'] = record.span_id
        if hasattr(record, 'resource'):
            # For specific GCP resource types (e.g., specific GCE instance, Cloud Function)
            # This is often auto-detected by Cloud Logging agents, but can be overridden.
            log_entry['resource'] = record.resource

        return json.dumps(log_entry)

# Example usage (for local testing or as a main entry point)
#if __name__ == "__main__":
#    my_logger = setup_logging()
#
#    # Test logs
#    my_logger.debug("This is a debug message. It might not show if level is INFO.")
#    my_logger.info("Application started successfully.")
#    my_logger.warning("Configuration file not found, using defaults.")
#    my_logger.error("Failed to connect to the database!", exc_info=True) # exc_info=True adds stack trace
#
#    # Structured logging with extra fields
#    user_id = "user_123"
#    transaction_id = "txn_abc"
#    my_logger.info(
#        "User logged in.",
#        extra={
#            "json_fields": {
#                "user_id": user_id,
#                "event_type": "user_login",
#                "ip_address": "192.0.2.1",
#            },
#            "labels": {
#                "environment": "development",
#                "source": "webapp",
#            },
#            # Example of adding an HTTP request context (for HttpRequest payload in Cloud Logging)
#            "http_request": {
#                "requestMethod": "GET",
#                "requestUrl": "/api/v1/login",
#                "status": 200,
#                "userAgent": "Mozilla/5.0",
#                "remoteIp": "192.0.2.1",
#            },
#            # Example of adding a trace ID (if integrated with OpenTelemetry/Cloud Trace)
#            "trace": "projects/your-gcp-project-id/traces/a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
#        }
#    )
#
#    try:
#        1 / 0
#    except ZeroDivisionError:
#        my_logger.exception("An unhandled exception occurred during division.")
