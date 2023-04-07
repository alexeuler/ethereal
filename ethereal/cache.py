from typing import Dict, Any, List, TypedDict
import json
from functools import cached_property, cache
import os
from datetime import datetime
from .base import Base


class CacheException(Exception):
    pass


class CacheConfig(TypedDict):
    root: str


class Cache(Base):
    _config: CacheConfig

    def __init__(self, config: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = config

    def load_json(self, key: str) -> Dict[str, Any]:
        with open(self._path(key), "r") as f:
            return json.load(f)

    @cache
    def load(self, key: str) -> str:
        with open(self._path(key), "r") as f:
            return f.read()

    def save(self, key: str, data: str):
        del self.load[key]
        path = self._path(key)
        os.makedirs(path, exist_ok=True)
        with open(path, "w") as f:
            f.write(data)
            f.flush()

    def _path(self, key: str) -> str:
        return f"{self._config.root}/{key}".replace("//", "/")


class JsonDataCache(Base):
    _cache_folder: str

    def __init__(self, cache_folder: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_folder = cache_folder

    @cached_property
    def data(self) -> Dict[str, Any] | List[Any]:
        try:
            with open(self._path(), "r") as f:
                return json.load(f)
        except Exception as e:
            pass
        res = self.save()
        if res is None:
            raise CacheException(f"Cannot open {self._filename()}")
        return res

    @property
    def cache_date(self) -> datetime:
        try:
            ts = os.path.getmtime(self._path())

        except Exception as e:
            ts = 0

        return datetime.utcfromtimestamp(ts)

    def save(self):
        self.logger.info(f"Fetching data...")
        if not hasattr(self, "_fetch"):
            self.logger.error(f"No _fetch method found")
            return None
        res = self._fetch()
        self.logger.info(f"Done, saving data")
        with open(self._path(), "w") as f:
            json.dump(res, f, indent=2)
        self.logger.info(f"Done")
        return res

    def cache_clear(self):
        if "data" in self.__dict__:
            del self.__dict__["data"]

    def _path(self) -> str:
        return f"{self._cache_folder}/json_cache/{self._filename()}.json"

    def _filename(self):
        return self.__class__.__name__
