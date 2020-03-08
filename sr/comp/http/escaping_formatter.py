
import logging


class EscapingFormatter(logging.Formatter):
    """A class that formats log output nicely."""

    def format(self, record):  # noqa:A003 # name `format` is defined by parent class
        msg = super().format(record)
        # Newlines are the only thing known to have caused issues thus far
        escaped = msg.replace('\n', '\\n')
        return escaped
