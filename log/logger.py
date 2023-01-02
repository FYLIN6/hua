import logging.handlers
import sys
import os
import datetime
import logging
from config_pack.file_config import FileConfig
sys.path.append('../../')


class Logger(object):
    level_switch = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    logger = logging.getLogger("logger")
    stream_handler = None
    file_handler = None

    debug_sign = True
    info_sign = True
    warning_sign = True
    error_sign = True
    critical_sign = True

    def __init__(self,
                 file_path=FileConfig.log_file_path,
                 stream_level='debug',
                 file_level='debug',
                 output_mode=None,
                 fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        if output_mode is None:
            output_mode = ['stream', 'file']
        self.update_config(file_path=file_path, stream_level=stream_level, file_level=file_level,
                           output_mode=output_mode, fmt=fmt)

    @classmethod
    def debug(self, *args, **kwargs):
        if self.debug_sign == True:
            self.logger.debug(*args, **kwargs)

    @classmethod
    def info(self, *args, **kwargs):
        if self.info_sign == True:
            self.logger.info(*args, **kwargs)

    @classmethod
    def warning(self, *args, **kwargs):
        if self.warning_sign == True:
            self.logger.warning(*args, **kwargs)

    @classmethod
    def error(self, *args, **kwargs):
        if self.error_sign == True:
            self.logger.error(*args, **kwargs)

    @classmethod
    def critical(self,  *args, **kwargs):
        if self.critical_sign == True:
           self.logger.critical(*args, **kwargs)

    @classmethod
    def update_config(self,
                      file_path=FileConfig.log_file_path,
                      include_log=None,
                      stream_level='debug',
                      file_level='debug',
                      name='',
                      dynamic=False,
                      output_mode=None,
                      fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):

        if output_mode is None:
            output_mode = ['stream', 'file']
        if include_log is None:
            include_log = ['debug', 'info', 'warning', 'error', 'critical']
        self.debug_sign = True if 'debug' in include_log else False
        self.info_sign = True if 'info' in include_log else False
        self.warning_sign = True if 'warning' in include_log else False
        self.error_sign = True if 'error' in include_log else False
        self.critical_sign = True if 'critical' in include_log else False

        self.logger.setLevel(logging.DEBUG)
        file_path = file_path
        if dynamic == True:
            file_path = os.path.join(FileConfig.log_folder,
                                     '{}_{}.log'.format(name, datetime.datetime.now().strftime('%Y%m%d%H%M%S')))

        if 'stream' in output_mode:

            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(self.level_switch[stream_level])
            self.stream_handler.setFormatter(logging.Formatter(fmt))
            self.logger.addHandler(self.stream_handler)
        else:
            if self.stream_handler:
                logging.getLogger("logger").removeHandler(self.stream_handler)
                self.stream_handler = None

        if 'file' in output_mode:
            self.file_handler = logging.FileHandler(filename=file_path, mode='w', encoding="UTF-8")
            self.file_handler.setLevel(self.level_switch[file_level])
            self.file_handler.setFormatter(logging.Formatter(fmt))
            self.logger.addHandler(self.file_handler)
        else:
            if self.file_handler:
                logging.getLogger("logger").removeHandler(self.file_handler)
                self.file_handler = None

