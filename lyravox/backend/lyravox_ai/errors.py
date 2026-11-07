class ApiError(Exception):
    """An error with an HTTP status and a machine-readable code, returned to clients as {"error": {"code", "message"}}."""
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message

    def body(self):
        return {'error': {'code': self.code, 'message': self.message}}


class Cancelled(Exception):
    """Raised inside the pipeline when the job was cancelled."""


class JobTimeout(Exception):
    """Raised inside the pipeline when the job ran past its deadline."""


class AudioError(Exception):
    """The audio could not be read / decoded."""
