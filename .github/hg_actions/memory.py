import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from clusterfk_llm.memory.manager import MemoryManager  # type: ignore
    from clusterfk_llm.memory.models import BaseMemory, MemoryTier, MemoryType  # type: ignore

    _HAS_CLUSTERFK_LLM = True
except ModuleNotFoundError:
    MemoryManager = None  # type: ignore
    BaseMemory = None  # type: ignore
    MemoryTier = None  # type: ignore
    MemoryType = None  # type: ignore
    _HAS_CLUSTERFK_LLM = False

class HGAMemory:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.manager = MemoryManager(data_dir=data_dir) if _HAS_CLUSTERFK_LLM else None
        self._work_log_path = os.path.join(data_dir, "work_log.jsonl")
        self.initialized = False

    async def initialize(self):
        if not self.initialized:
            os.makedirs(self.data_dir, exist_ok=True)
            self.initialized = True

    async def store_work_log(self, content: str, metadata: dict = None):
        """Stores a technical memento of work done."""
        await self.initialize()

        metadata_obj: Dict[str, Any] = dict(metadata or {})
        metadata_obj.setdefault("source", "hgactions")
        metadata_obj.setdefault("type", "work_log")

        if self.manager is not None:
            memory = BaseMemory(
                content=content,
                memory_type=MemoryType.TECHNICAL_MEMENTO,
                tier=MemoryTier.FAST,
                metadata=metadata_obj,
            )
            await self.manager.store_memory(memory)
            return

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "content": content,
            "metadata": metadata_obj,
        }
        with open(self._work_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")

    async def get_context(self, query_text: str, max_results: int = 5) -> str:
        """Retrieves relevant context for planning."""
        await self.initialize()

        if self.manager is not None:
            return await self.manager.get_memory_context_for_prompt(query_text)

        if not os.path.exists(self._work_log_path):
            return ""

        try:
            with open(self._work_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return ""

        # Simple strategy: return the most recent entries, best-effort.
        selected = []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                selected.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(selected) >= max_results:
                break

        selected.reverse()
        chunks = []
        for item in selected:
            ts = item.get("ts", "")
            content = item.get("content", "")
            chunks.append(f"[{ts}] {content}".strip())
        return "\n".join(chunks)
