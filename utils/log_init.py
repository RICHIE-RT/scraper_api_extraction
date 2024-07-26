from dotenv import load_dotenv
import logging
import os

load_dotenv()
SCRAPER_LOGDIR = os.getenv("SCRAPER_LOGDIR")
if not os.path.exists(SCRAPER_LOGDIR):
    os.mkdir(SCRAPER_LOGDIR)


def setup_logger(name, log_file, level):
    formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(message)s',  datefmt='%m-%d-%Y %I:%M')
    
    """To setup as many loggers as you want"""
    file_handler = logging.FileHandler(log_file)        
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger

info_logger = setup_logger('logger', f'{SCRAPER_LOGDIR}/success_log.log', logging.INFO)
error_logger = setup_logger('error_logger', f'{SCRAPER_LOGDIR}/error_log.log', logging.ERROR)