"""
cl-imports auto-resolution — walk a Common Logic module's import closure and
assemble it into one self-contained CLIF source.

A COLORE / Common-Logic module declares its dependencies with ``(cl-imports
<iri>)`` directives.  The protected CLIF parser *skips* them (``_parse_cl_imports``
returns a no-op), so a module whose imports are absent parses as a silently
*incomplete* theory — the betweenness ontology only became usable once its chain
``betweenness → weak_between → bet`` was resolved **by hand** into one file.  This
module resolves that chain automatically: it fetches/locates the transitive
closure, dedupes by IRI, and conjuncts every module's verbatim content on one
sheet.  The combined text feeds the existing ``from_clif_text`` pipeline
(block-comment strip → function relationalization → variable disambiguation →
parse); the now-satisfied ``cl-imports`` directives stay in place as harmless
no-ops.

Resolution is pluggable (``ImportResolver.resolve(iri) -> Optional[str]``):

  * :class:`MappingResolver`   — an in-memory ``{iri: text}`` dict (pure, offline;
    the test backend).
  * :class:`DirectoryResolver` — a local directory mirroring the IRI path under a
    prefix (offline, reproducible; the corpus-build default once a closure is
    vendored).
  * :class:`ColoreWebResolver` — fetch from the COLORE repository over the network
    (raw GitHub); opt-in, used to *populate* a local cache.
  * :class:`CachingResolver`   — wrap a remote resolver, persisting every fetched
    module to a local directory so a one-time online run yields an offline,
    reproducible, cited cache (the ``colore_between.clif`` vendoring, automated).
  * :class:`ChainResolver`     — try several resolvers in order (first hit wins).

Unresolved IRIs are *reported* on the closure, never silently dropped (the
manifest floor: ``docs/MANIFEST_AND_MEANING.md``).
"""

from __future__ import annotations

import re
import ssl
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Union, runtime_checkable

# The COLORE namespace prefix and the raw-GitHub layout its IRIs mirror.  An IRI
# ``http://colore.oor.net/<path>`` is the file ``ontologies/<path>`` in the repo.
COLORE_PREFIX = "http://colore.oor.net/"
COLORE_RAW_BASE = (
    "https://raw.githubusercontent.com/gruninger/colore/master/ontologies/"
)

_CL_IMPORTS_RE = re.compile(r"\(cl-imports\s+([^\s)]+)\s*\)")


def _ssl_context() -> ssl.SSLContext:
    """A verifying SSL context using ``certifi``'s CA bundle when available — the
    venv Python often lacks a system trust store, so a bare ``urlopen`` fails cert
    verification on raw GitHub (``curl`` works only because it uses the OS bundle)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def extract_imports(clif_text: str) -> List[str]:
    """The ``cl-imports`` IRIs declared in ``clif_text`` (in source order),
    read without parsing.  Shared by the closure walk and the importer."""
    return _CL_IMPORTS_RE.findall(clif_text)


# --------------------------------------------------------------------------- #
# Resolvers                                                                    #
# --------------------------------------------------------------------------- #

@runtime_checkable
class ImportResolver(Protocol):
    """Maps a ``cl-imports`` IRI to its CLIF source text (or ``None`` if this
    resolver cannot locate it)."""

    def resolve(self, iri: str) -> Optional[str]:
        ...


class MappingResolver:
    """Resolve from an in-memory ``{iri: clif_text}`` dict — pure and offline,
    the deterministic test backend."""

    def __init__(self, mapping: Dict[str, str]):
        self._m = dict(mapping)

    def resolve(self, iri: str) -> Optional[str]:
        return self._m.get(iri)


class DirectoryResolver:
    """Resolve an IRI to a file under ``base_dir`` whose relative path is the IRI
    minus ``prefix``.  ``http://colore.oor.net/mass/amount.clif`` →
    ``base_dir/mass/amount.clif``.  Offline and reproducible."""

    def __init__(self, base_dir: Union[str, Path], prefix: str = COLORE_PREFIX):
        self.base = Path(base_dir)
        self.prefix = prefix

    def resolve(self, iri: str) -> Optional[str]:
        if not iri.startswith(self.prefix):
            return None
        path = self.base / iri[len(self.prefix):]
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
        return None


class ColoreWebResolver:
    """Fetch a COLORE IRI from raw GitHub.  Network, opt-in — typically wrapped in
    a :class:`CachingResolver` so a single online run vendors an offline cache."""

    def __init__(
        self,
        prefix: str = COLORE_PREFIX,
        base_url: str = COLORE_RAW_BASE,
        timeout: float = 30.0,
    ):
        self.prefix = prefix
        self.base_url = base_url
        self.timeout = timeout
        self._ctx = _ssl_context()

    def resolve(self, iri: str) -> Optional[str]:
        if not iri.startswith(self.prefix):
            return None
        url = self.base_url + iri[len(self.prefix):]
        try:
            with urllib.request.urlopen(
                    url, timeout=self.timeout, context=self._ctx) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None


class CachingResolver:
    """Try a local cache directory first; on a miss, delegate to ``remote`` and
    persist the result into the cache (mirroring the IRI path).  A one-time online
    run thus leaves a vendored, offline, reproducible, citable closure on disk."""

    def __init__(
        self,
        remote: ImportResolver,
        cache_dir: Union[str, Path],
        prefix: str = COLORE_PREFIX,
    ):
        self.remote = remote
        self.cache = Path(cache_dir)
        self.prefix = prefix
        self._local = DirectoryResolver(cache_dir, prefix)

    def resolve(self, iri: str) -> Optional[str]:
        local = self._local.resolve(iri)
        if local is not None:
            return local
        text = self.remote.resolve(iri)
        if text is not None and iri.startswith(self.prefix):
            dest = self.cache / iri[len(self.prefix):]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        return text


class ChainResolver:
    """Try each resolver in order; the first to return text wins."""

    def __init__(self, *resolvers: ImportResolver):
        self.resolvers = list(resolvers)

    def resolve(self, iri: str) -> Optional[str]:
        for r in self.resolvers:
            text = r.resolve(iri)
            if text is not None:
                return text
        return None


# --------------------------------------------------------------------------- #
# Closure walk                                                                 #
# --------------------------------------------------------------------------- #

@dataclass
class ModuleSource:
    """One resolved module in the closure: its IRI, verbatim CLIF text, and the
    ``cl-imports`` IRIs it declares."""

    iri: str
    text: str
    imports: List[str] = field(default_factory=list)


@dataclass
class ResolvedClosure:
    """The transitive ``cl-imports`` closure of a root module.

    ``combined_clif`` is every resolved module's verbatim text concatenated under
    provenance headers — feed it to ``from_clif_text``.  ``modules`` is the
    closure in resolution (breadth-first) order.  ``unresolved`` lists IRIs no
    resolver could locate (reported, never silently dropped)."""

    combined_clif: str
    modules: List[ModuleSource]
    unresolved: List[str] = field(default_factory=list)
    root: Optional[str] = None

    @property
    def resolved_iris(self) -> List[str]:
        return [m.iri for m in self.modules]

    @property
    def is_complete(self) -> bool:
        return not self.unresolved

    @property
    def summary(self) -> str:
        parts = [f"{len(self.modules)} module(s) resolved"]
        if self.unresolved:
            parts.append(f"{len(self.unresolved)} unresolved: "
                         + ", ".join(self.unresolved))
        return "; ".join(parts)


def _assemble(modules: List[ModuleSource], unresolved: List[str]) -> str:
    """Concatenate verbatim module texts under ``;; ===== <iri> =====`` headers,
    flagging any unresolved IRI as an honest comment (so the assembled source
    records exactly what the closure does — and does not — contain)."""
    parts: List[str] = []
    for m in modules:
        parts.append(f";; ===== {m.iri} =====\n{m.text}")
    for iri in unresolved:
        parts.append(f";; ===== UNRESOLVED: {iri} =====")
    return "\n\n".join(parts)


def _walk(
    root_iri: str,
    resolver: ImportResolver,
    root_text: Optional[str],
) -> ResolvedClosure:
    seen: set = set()
    modules: List[ModuleSource] = []
    unresolved: List[str] = []
    work: deque = deque([root_iri])
    first = True

    while work:
        iri = work.popleft()
        if iri in seen:
            continue
        seen.add(iri)

        if first and root_text is not None:
            text: Optional[str] = root_text
        else:
            text = resolver.resolve(iri)
        first = False

        if text is None:
            unresolved.append(iri)
            continue

        imports = extract_imports(text)
        modules.append(ModuleSource(iri=iri, text=text, imports=imports))
        for imp in imports:
            if imp not in seen:
                work.append(imp)

    return ResolvedClosure(
        combined_clif=_assemble(modules, unresolved),
        modules=modules,
        unresolved=unresolved,
        root=root_iri,
    )


def resolve_from_text(
    clif_text: str,
    resolver: ImportResolver,
    *,
    root_iri: str = "(root)",
) -> ResolvedClosure:
    """Resolve the ``cl-imports`` closure of a root module given **as text** (the
    common case: you have ``density.clif`` in hand and want its dependencies).
    The root's own text is taken from ``clif_text``; everything it transitively
    imports is fetched through ``resolver``."""
    return _walk(root_iri, resolver, root_text=clif_text)


def resolve_from_iri(
    root_iri: str,
    resolver: ImportResolver,
) -> ResolvedClosure:
    """Resolve the ``cl-imports`` closure of a root module named **by IRI** — the
    root itself is fetched through ``resolver`` like every dependency."""
    return _walk(root_iri, resolver, root_text=None)
