import logging


class EscapingFormatter(logging.Formatter):
    """A class that formats log output nicely."""

    def format(  # noqa:A003 # name `format` is defined by parent class
        self,
        record: logging.LogRecord,
    ) -> str:
        msg = super().format(record)
        # Newlines are the only thing known to have caused issues thus far
        escaped = msg.replace('\n', '\\n')
        return escaped
