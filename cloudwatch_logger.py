import os
import boto3
import logging
import time
import json
import psutil
import inspect
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CloudWatchJsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'level': record.levelname,
            'location': record.location,
            'message': record.getMessage(),
            'memory_usage': f"{psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)} MB",
            'cpu_usage': f"{psutil.cpu_percent(interval=None)} %",
        }
        return json.dumps(log_record, indent=4)

class CloudWatchLogger:
    client = boto3.client('logs', 
                          region_name=os.getenv('AWS_REGION'), 
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), 
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    log_group = os.getenv('LOG_GROUP')
    sequence_token = None
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: [%(filename)s:%(lineno)d] %(message)s'))
    logger.addHandler(console_handler)

    @staticmethod
    def log(message, level=logging.INFO):
        # Generate log stream name based on the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        log_stream = f"{current_date}"

        # Check if the log stream exists, if not, create it
        CloudWatchLogger.ensure_log_stream_exists(log_stream)

        frame, filename, lineno, _, _, _ = inspect.stack()[1]
        location = f"{os.path.basename(filename)}:{lineno}"

        CloudWatchLogger.logger.log(level, message, extra={'location': location})

        cw_formatter = CloudWatchJsonFormatter()
        record = CloudWatchLogger.logger.makeRecord(
            name=CloudWatchLogger.logger.name,
            level=level,
            fn=filename,
            lno=lineno,
            msg=message,
            args=None,
            exc_info=None,
            extra={'location': location}
        )
        json_log_message = cw_formatter.format(record)

        current_timestamp = int(time.time() * 1000) - (2 * 3600)
        log_event = {
            'timestamp': current_timestamp,
            'message': json_log_message
        }

        try:
            if CloudWatchLogger.sequence_token:
                response = CloudWatchLogger.client.put_log_events(
                    logGroupName=CloudWatchLogger.log_group,
                    logStreamName=log_stream,
                    logEvents=[log_event],
                    sequenceToken=CloudWatchLogger.sequence_token
                )
            else:
                response = CloudWatchLogger.client.put_log_events(
                    logGroupName=CloudWatchLogger.log_group,
                    logStreamName=log_stream,
                    logEvents=[log_event]
                )
            
            CloudWatchLogger.sequence_token = response.get('nextSequenceToken')
        except boto3.client('logs').exceptions.InvalidSequenceTokenException as e:
            CloudWatchLogger.sequence_token = e.response['Error']['Message'].split()[-1]
            response = CloudWatchLogger.client.put_log_events(
                logGroupName=CloudWatchLogger.log_group,
                logStreamName=log_stream,
                logEvents=[log_event],
                sequenceToken=CloudWatchLogger.sequence_token
            )
            CloudWatchLogger.sequence_token = response['nextSequenceToken']
        except Exception as e:
            # Handle any other exceptions
            CloudWatchLogger.logger.error(f"An error occurred: {e}")

    @staticmethod
    def ensure_log_stream_exists(log_stream):
        try:
            CloudWatchLogger.client.create_log_stream(
                logGroupName=CloudWatchLogger.log_group,
                logStreamName=log_stream
            )
        except boto3.client('logs').exceptions.ResourceAlreadyExistsException:
            # Log stream already exists, no action needed
            pass

# Example usage
if __name__ == "__main__":
    CloudWatchLogger.log("Test message to log and send to CloudWatch")
