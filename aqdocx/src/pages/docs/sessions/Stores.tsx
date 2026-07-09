import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Database } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsStores() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionHeaderClass = `text-2xl font-mono font-bold tracking-tight mb-6 flex items-center gap-3 ${
    isDark ? 'text-white' : 'text-gray-900'
  }`
  const textClass = `text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-aquilia-500 mb-4">
          <Database className="w-4 h-4" />
          Sessions / Stores
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Stores
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Session stores manage persistence and loading of active sessions. Aquilia exposes a typed <DocTerm id="sessions.store">SessionStore</DocTerm> protocol, implemented out-of-the-box by MemoryStore and FileStore.
        </p>
      </div>

      {/* SessionStore Protocol */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionStore Protocol</h2>
        <p className={textClass}>
          All storage backends must implement the <code className="text-aquilia-500">SessionStore</code> protocol.
          Stores are purely responsible for persistence — they do not enforce expiration policies or idle timeouts.
        </p>
        <CodeBlock language="python" filename="protocol.py" highlightLines={[9, 13, 17, 21, 25, 29]}>{`from typing import Protocol
from aquilia.sessions import Session, SessionID


class SessionStore(Protocol):
    """Protocol for session storage backends."""

    async def load(self, session_id: SessionID) -> Session | None:
        """Load session by ID. Returns None if not found or corrupted."""
        ...

    async def save(self, session: Session) -> None:
        """Persist session. Sets session version and resets dirty state."""
        ...

    async def delete(self, session_id: SessionID) -> None:
        """Delete session by ID."""
        ...

    async def exists(self, session_id: SessionID) -> bool:
        """Check if session exists in store."""
        ...

    async def list_by_principal(self, principal_id: str) -> list[Session]:
        """Find active sessions belonging to user principal."""
        ...

    async def count_by_principal(self, principal_id: str) -> int:
        """Count active sessions belonging to user principal."""
        ...

    async def cleanup_expired(self) -> int:
        """Remove expired sessions from storage. Returns removed count."""
        ...

    async def shutdown(self) -> None:
        """Gracefully release storage client resources."""
        ...`}</CodeBlock>
      </section>

      {/* MemoryStore */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>MemoryStore (In-Memory LRU)</h2>
        <p className={textClass}>
          An in-memory store utilizing an <code className="text-aquilia-500">OrderedDict</code> to achieve O(1) LRU eviction.
          Features locking for asynchronous consistency and secondary index tables for principal queries.
          MemoryStore is not persistent across server reboots.
        </p>
        <CodeBlock language="python" filename="memory_store.py" highlightLines={[4, 10, 13, 16]}>{`from aquilia.sessions import MemoryStore

# Manual construction (requires max_sessions limit)
store = MemoryStore(max_sessions=10000)

# Factory presets optimized for specific payloads:

# Web: High capacity (25k max sessions)
store = MemoryStore.web_optimized()

# API: Medium capacity (15k max sessions)
store = MemoryStore.api_optimized()

# Mobile: Medium capacity (15k max sessions)
store = MemoryStore.development_focused()  # 1k capacity

# High-throughput: Max capacity (50k max sessions)
store = MemoryStore.high_throughput()`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>LRU Eviction Mechanism</h3>
        <p className={textClass}>
          When capacity is reached, new saves trigger LRU eviction, popping the oldest accessed session from the store:
        </p>
        <CodeBlock language="python" filename="lru.py" highlightLines={[6, 9, 12]}>{`store = MemoryStore(max_sessions=3)

# 1. Fill the store
await store.save(session_a) # OrderedDict: [A]
await store.save(session_b) # OrderedDict: [A, B]
await store.save(session_c) # OrderedDict: [A, B, C]

# 2. Access A to make it recently-used
await store.load(session_a.id) # OrderedDict moves A to end: [B, C, A]

# 3. Save D triggers LRU eviction of B
await store.save(session_d) # OrderedDict evicts B: [C, A, D]
print(await store.exists(session_b.id)) # False (evicted!)`}</CodeBlock>
      </section>

      {/* FileStore */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>FileStore (JSON File-based)</h2>
        <p className={textClass}>
          Saves each session as an individual JSON file. Incorporates atomic write protocols (temp file creation + atomic rename)
          to ensure file corruption does not occur during system failures. FileStore is suitable for low-traffic development.
        </p>
        <CodeBlock language="python" filename="file_store.py" highlightLines={[4]}>{`from aquilia.sessions import FileStore

# Constructor takes directory folder path
store = FileStore(directory="/var/lib/aquilia/sessions")

# Session IDs are strictly validated to prevent path-traversal attacks.
# Data is formatted inside sess_*.json files.`}</CodeBlock>
      </section>

      {/* Custom Store */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>Building a Custom Store (Redis Example)</h2>
        <p className={textClass}>
          Implement the <code className="text-aquilia-500">SessionStore</code> protocol to define your custom storage (such as Redis, DynamoDB, or PostgreSQL):
        </p>
        <CodeBlock language="python" filename="redis_store.py" highlightLines={[6, 17, 21, 28, 41]}>{`import json
from datetime import datetime, timezone
from aquilia.sessions import Session, SessionID


class RedisSessionStore:
    """Pluggable Redis backend implementing SessionStore protocol."""

    def __init__(self, client, prefix: str = "aquilia:sess:"):
        self.client = client
        self.prefix = prefix

    def _key(self, sid: SessionID) -> str:
        return f"{self.prefix}{str(sid)}"

    async def load(self, session_id: SessionID) -> Session | None:
        raw = await self.client.get(self._key(session_id))
        if not raw:
            return None
        return Session.from_dict(json.loads(raw))

    async def save(self, session: Session) -> None:
        key = self._key(session.id)
        payload = json.dumps(session.to_dict())
        
        # Calculate remaining TTL seconds dynamically
        ttl = 3600
        if session.expires_at:
            now = datetime.now(timezone.utc)
            ttl = max(int((session.expires_at - now).total_seconds()), 1)
            
        await self.client.setex(key, ttl, payload)
        
        # Keep track of principal query indices
        if session.principal:
            p_key = f"{self.prefix}principal:{session.principal.id}"
            await self.client.sadd(p_key, str(session.id))
            
        session.mark_clean()

    async def delete(self, session_id: SessionID) -> None:
        session = await self.load(session_id)
        key = self._key(session_id)
        await self.client.delete(key)
        
        if session and session.principal:
            p_key = f"{self.prefix}principal:{session.principal.id}"
            await self.client.srem(p_key, str(session_id))

    async def exists(self, session_id: SessionID) -> bool:
        return bool(await self.client.exists(self._key(session_id)))

    async def list_by_principal(self, principal_id: str) -> list[Session]:
        p_key = f"{self.prefix}principal:{principal_id}"
        sids = await self.client.smembers(p_key)
        sessions = []
        for sid_str in sids:
            try:
                sid = SessionID.from_string(sid_str)
                sess = await self.load(sid)
                if sess:
                    sessions.append(sess)
            except Exception:
                continue
        return sessions

    async def count_by_principal(self, principal_id: str) -> int:
        p_key = f"{self.prefix}principal:{principal_id}"
        return await self.client.scard(p_key)

    async def cleanup_expired(self) -> int:
        # No-op: Redis automatically evicts keys using setex TTLs
        return 0

    async def shutdown(self) -> None:
        await self.client.close()

# Register the store in the SessionEngine (engine receives a single store instance)
from aquilia.sessions import SessionEngine
engine = SessionEngine(
    policy=policy,
    store=RedisSessionStore(redis_client),
    transport=transport
)`}</CodeBlock>
      </section>

      {/* Store Comparison - Clean minimalist table */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Store Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className={`border-b-2 ${isDark ? 'border-zinc-800 text-zinc-400' : 'border-zinc-200 text-zinc-500'} font-mono text-xs font-semibold`}>
                <th className="text-left py-3 pr-4">Feature</th>
                <th className="text-left py-3 pr-4">MemoryStore</th>
                <th className="text-left py-3 pr-4">FileStore</th>
                <th className="text-left py-3">Custom (Redis)</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-zinc-300' : 'text-zinc-700'}>
              {[
                ['Persistence', '❌ Lost on restart', '✅ Disk-persisted', '✅ Network-persisted'],
                ['Performance', '⚡ Fastest', '🐢 Disk I/O bound', '⚡ Fast (network)'],
                ['Multi-process', '❌ Single process only', '✅ Shared filesystem', '✅ Shared network'],
                ['LRU Eviction', '✅ Built-in (max_sessions)', '❌ Requires manual sweep', '✅ Handled by Redis TTL'],
                ['Principal Index', '✅ Built-in secondary table', '🐢 Requires full directory scan', '✅ Managed via Redis Sets'],
                ['Atomic Writes', 'N/A', '✅ tempfile + rename replacement', '✅ Redis atomic setex'],
                ['Recommended for', 'Local development & unit tests', 'Low-traffic standalone apps', 'Production clusters'],
              ].map(([feature, memory, file, custom], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-zinc-900/50 hover:bg-white/[0.01]' : 'border-zinc-100 hover:bg-black/[0.01]'} transition-colors`}>
                  <td className="py-3 pr-4 font-semibold text-xs">{feature}</td>
                  <td className="py-3 pr-4 text-xs">{memory}</td>
                  <td className="py-3 pr-4 text-xs">{file}</td>
                  <td className="py-3 text-xs">{custom}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
