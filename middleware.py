from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)

class ConnectionErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except ConnectionAbortedError as e:
            logger.error(f"Connection aborted error: {e}")
            return redirect('connection_error')
        except ConnectionRefusedError as e:
            logger.error(f"Connection refused error: {e}")
            return redirect('connection_error')
        except ConnectionResetError as e:
            logger.error(f"Connection reset error: {e}")
            return redirect('connection_error')
        except Exception as e:
            # Let Django's default exception handling take over for other exceptions
            raise