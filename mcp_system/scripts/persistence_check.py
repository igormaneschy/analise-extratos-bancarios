# Persistence check script
# Moved from tests/unit to scripts for manual execution

import importlib.util
import sys
import sqlite3
from pathlib import Path
import os
import tempfile
import traceback


def _load_server_module(mcp_data_dir: str):
    repo_root = Path(__file__).resolve().parents[2]
    mcp_path = repo_root / "mcp_system" / "mcp_server_enhanced.py"
    spec = importlib.util.spec_from_file_location("_mcp_server_persist_script", str(mcp_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return spec.name, module


def run_persistence_check():
    tmp_dir = tempfile.mkdtemp(prefix="mcp_test_mem_")
    os.environ['MCP_DATA_DIR'] = tmp_dir
    print(f"[persistence-check] Using MCP_DATA_DIR={tmp_dir}")

    name = None
    server = None
    try:
        name, server = _load_server_module(tmp_dir)

        store = getattr(server, 'store', None)
        if store is None:
            store = server._get_memory()
        if store is None:
            raise RuntimeError("MemoryStore not available after bootstrap")

        db_path = getattr(store, 'db_path', None) or str(Path(tmp_dir) / 'session_store.sqlite3')
        if not Path(db_path).exists():
            raise RuntimeError(f"Expected DB to exist at {db_path}")

        fake_pack = {
            "total_tokens_sent": 77,
            "tokens_saved_total": 5,
            "cache_tokens_saved": 1,
            "compression_tokens_saved": 0,
            "budget_info": {"model": "persist-test-model"},
        }

        def fake_build_context_pack(indexer, query, budget_tokens, max_chunks, strategy):
            return dict(fake_pack)

        # monkeypatch-like replacement without pytest
        setattr(server, 'build_context_pack', fake_build_context_pack)

        res = server._handle_context_pack(query="persist-test", token_budget=10, max_chunks=1, strategy="mmr", model_name="persist-test-model", provider="pv")
        if res.get('status') != 'success':
            raise RuntimeError(f"Handler returned error: {res}")

        active_store = server._get_memory() or store
        active_db = getattr(active_store, 'db_path', db_path)

        # Prefer API-based check
        if hasattr(active_store, 'get_llm_usage_agg'):
            agg = active_store.get_llm_usage_agg()
            total_tokens = sum(float(v.get('tokens', 0.0)) for v in agg.values())
            if total_tokens < 77.0:
                raise RuntimeError(f"Aggregated tokens {total_tokens} < expected 77.0; agg={agg}")
        else:
            # Fallback to SQL sum check
            conn = sqlite3.connect(active_db)
            try:
                cur = conn.cursor()
                cur.execute("SELECT SUM(tokens) FROM llm_usage")
                row = cur.fetchone()
                total = float(row[0] or 0.0)
                if total < 77.0:
                    raise RuntimeError(f"DB tokens sum {total} < expected 77.0 (db={active_db})")
            finally:
                conn.close()

        print("[persistence-check] OK: tokens persisted to MemoryStore DB")

    except Exception as exc:
        print("[persistence-check] FAILED:")
        traceback.print_exc()
        return 1
    finally:
        if name and name in sys.modules:
            try:
                del sys.modules[name]
            except Exception:
                pass

    return 0


if __name__ == '__main__':
    rc = run_persistence_check()
    sys.exit(rc)
