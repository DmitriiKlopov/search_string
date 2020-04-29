import logging


class AppNameFilter(logging.Filter):
    def __init__(self, name: str = "", app_name: str = "") -> None:
        super().__init__(name)
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name
        return True
