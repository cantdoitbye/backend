import logging

# Set up Matrix logger
matrix_logger = logging.getLogger("matrix_logger")
if not matrix_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    matrix_logger.addHandler(handler)
    matrix_logger.setLevel(logging.INFO)
