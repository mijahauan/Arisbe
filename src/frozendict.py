# Minimal local shim for `frozendict` package if not installed.
# Provides an immutable mapping suitable for our usage in EGI core.
from collections.abc import Mapping

class frozendict(Mapping):
    __slots__ = ("_data", "_hash")

    def __init__(self, *args, **kwargs):
        d = dict(*args, **kwargs)
        self._data = d
        self._hash = None

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"frozendict({self._data!r})"

    def copy(self, **add_or_override):
        if not add_or_override:
            return frozendict(self._data)
        nd = dict(self._data)
        nd.update(add_or_override)
        return frozendict(nd)

    def to_dict(self):
        return dict(self._data)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(self._data.items()))
        return self._hash

    # Block mutation-like methods
    def __setitem__(self, key, value):
        raise TypeError("frozendict is immutable")

    def __delitem__(self, key):
        raise TypeError("frozendict is immutable")
