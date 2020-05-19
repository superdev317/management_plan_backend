from django.conf import settings

from rocketchat_API.rocketchat import RocketChat as BaseRocketChat


class RocketChat(BaseRocketChat):
    """
    By default RocketChat try login via API every time when we call him.
    But we want continue current user session
    """
    def __init__(
            self,
            user=None,
            password=None,
            server_url=settings.ROCKETCHAT_URL,
            ssl_verify=True,
            proxies=None,
            timeout=30,
            headers=None
    ):
        self.headers = headers or {}
        self.server_url = server_url
        self.proxies = proxies
        self.ssl_verify = ssl_verify
        self.timeout = timeout

        if not self.headers:
            super().__init__(
                user, password, server_url, ssl_verify, proxies, timeout
            )
