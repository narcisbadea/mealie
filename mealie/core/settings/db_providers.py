from abc import ABC, abstractmethod
from pathlib import Path
from urllib import parse as urlparse

from pydantic import BaseModel, PostgresDsn, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AbstractDBProvider(ABC):
    @property
    @abstractmethod
    def db_url(self) -> str: ...

    @property
    @abstractmethod
    def db_url_public(self) -> str: ...

    @property
    @abstractmethod
    def data_dir(self) -> Path: ...


class SQLiteProvider(AbstractDBProvider, BaseModel):
    prefix: str = ""

    _data_dir: Path = PrivateAttr(default_factory=lambda: Path("/app/data"))

    model_config = SettingsConfigDict(arbitrary_types_allowed=True)

    def __init__(self, data_dir: Path = Path("/app/data"), **data):
        super().__init__(**data)
        self._data_dir = data_dir

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def db_path(self):
        return self.data_dir / f"{self.prefix}mealie.db"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path.absolute()!s}"

    @property
    def db_url_public(self) -> str:
        return self.db_url


class PostgresProvider(AbstractDBProvider, BaseSettings):
    POSTGRES_USER: str = "mealie"
    POSTGRES_PASSWORD: str = "mealie"
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "mealie"
    POSTGRES_URL_OVERRIDE: str | None = None

    _data_dir: Path | None = None

    model_config = SettingsConfigDict(arbitrary_types_allowed=True, extra="allow")

    def set_data_dir(self, data_dir: Path) -> None:
        """Set the data directory for file storage."""
        self._data_dir = data_dir

    @property
    def data_dir(self) -> Path:
        """Return the data directory for file storage."""
        if self._data_dir is None:
            return Path("/app/data")
        return self._data_dir

    def _parse_override_url(self, url: str) -> str:
        if not url.startswith("postgresql://"):
            raise ValueError("POSTGRES_URL_OVERRIDE scheme must be postgresql")

        scheme, remainder = url.split("://", 1)
        if "@" in remainder and ":" in remainder.split("@")[0]:
            credentials, host_part = remainder.rsplit("@", 1)
            user, password = credentials.split(":", 1)
            return f"{scheme}://{user}:{urlparse.quote(password, safe='')}@{host_part}"

        return url

    @property
    def db_url(self) -> str:
        if self.POSTGRES_URL_OVERRIDE:
            return self._parse_override_url(self.POSTGRES_URL_OVERRIDE)

        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.POSTGRES_USER,
                password=urlparse.quote(self.POSTGRES_PASSWORD),
                host=f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}",
                path=f"{self.POSTGRES_DB or ''}",
            )
        )

    @property
    def db_url_public(self) -> str:
        if self.POSTGRES_URL_OVERRIDE:
            return "Postgres Url Overridden"

        return f"postgresql://******:******@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB or ''}"


def db_provider_factory(provider_name: str, data_dir: Path, env_file: Path, env_encoding="utf-8") -> AbstractDBProvider:
    if provider_name == "postgres":
        provider = PostgresProvider(_env_file=env_file, _env_file_encoding=env_encoding)
        provider.set_data_dir(data_dir)
        return provider
    else:
        return SQLiteProvider(data_dir=data_dir)
