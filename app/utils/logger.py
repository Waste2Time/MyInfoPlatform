import logging
from logging.handlers import RotatingFileHandler
import os


class ProjectLogger:
    """简单的项目级日志包装器，封装了 Python logging 并提供与 logging.Logger 相同的方法。

    用法：
        from app.utils.logger import logger
        logger.info("message")
    """

    def __init__(self, name: str = "myinfoplatform", level: int = logging.INFO, log_file: str | None = None):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            self._logger.setLevel(level)
            fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            # 控制台处理器
            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            self._logger.addHandler(ch)
            # 可选的滚动文件处理器（若指定环境变量或 log_file）
            lf = log_file or os.getenv("MYINFO_LOG_FILE")
            if lf:
                fh = RotatingFileHandler(lf, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
                fh.setFormatter(fmt)
                self._logger.addHandler(fh)

    # 代理常用方法
    def debug(self, *args, **kwargs):
        return self._logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs):
        return self._logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        return self._logger.error(*args, **kwargs)

    def exception(self, *args, **kwargs):
        # exception() 自动记录堆栈信息，确保 level 为 ERROR
        return self._logger.exception(*args, **kwargs)


# module-level logger 实例，供项目直接导入使用
logger = ProjectLogger()._logger

