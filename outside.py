from cloudwatch_logger import CloudWatchLogger as logger

def function_that_raises_exception():
    """
    A sample function that intentionally raises an exception.
    """
    x=8/0

if __name__ == "__main__":
    try:
        # Call the function that will raise an exception
        function_that_raises_exception()
    except Exception as e:
        # Log the exception using CloudWatchLogger
        logger.log(e, '12345')
