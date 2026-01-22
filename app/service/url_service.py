from app.repository.short_url_repo import ShortURLRepository


class ShortURLService:
    def __init__(self, url_repo: ShortURLRepository):
        self.url_repo = url_repo

    def create_short_url(self, url: str) -> str:
       ...