import logging

def setup_logger(log_file='main.log', debug=False):
    # Configure basic logging settings

    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),  # Log to a file
            logging.StreamHandler()  # Also log to console
        ]
    )

    return