# Este teste carrega o módulo mcp_server_enhanced diretamente por caminho
# (import por arquivo) para garantir execução isolada dentro da pasta mcp_system.
# Motivo: a suíte principal ignora o pacote mcp_system para cobertura; ao manter o
# teste aqui dentro garantimos que ele seja executado no contexto deste sub-pacote
# e evitamos problemas de import devido à configuração do .coveragerc.

import importlib.util
import sys
from pathlib import Path
import pytest


def _load_server_module():
    # Resolve path to mcp_system/mcp_server_enhanced.py relative to this file
    # parents[3] resolves to repo root when this file is under mcp_system/tests/unit
    repo_root = Path(__file__).resolve().parents[3]
    mcp_path = repo_root / "mcp_system" / "mcp_server_enhanced.py"
    if not mcp_path.exists():
        pytest.skip("mcp_system module not present in workspace")

    spec = importlib.util.spec_from_file_location("_mcp_server_testmod", str(mcp_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return spec.name, module


def test_context_pack_updates_metrics_isolated(monkeypatch, tmp_path):
    """Load the server module from file (isolated) and assert metrics update.

    This avoids importing the mcp_system package via normal package import
    (the test runner may ignore that package). We load the file as a module by
    path so the test runs in isolation and is discoverable when running tests
    under the mcp_system subtree.
    """
    name, server = _load_server_module()

    try:
        # Reset counters to a known state
        for attr in (
            "_tokens_sent_total",
            "_tokens_saved_total",
            "_cache_tokens_saved_total",
            "_compression_tokens_saved_total",
            "_last_query_tokens_sent",
            "_last_query_tokens_saved",
        ):
            if hasattr(server, attr):
                setattr(server, attr, 0)

        fake_pack = {
            "total_tokens_sent": 42,
            "tokens_saved_total": 10,
            "cache_tokens_saved": 3,
            "compression_tokens_saved": 2,
            "budget_info": {"model": "test-model"},
        }

        def fake_build_context_pack(indexer, query, budget_tokens, max_chunks, strategy):
            return dict(fake_pack)

        # Patch the build_context_pack used by the server handler
        monkeypatch.setattr(server, "build_context_pack", fake_build_context_pack, raising=False)

        # Call the handler
        res = server._handle_context_pack(query="q", token_budget=16, max_chunks=1, strategy="mmr", model_name="test-model", provider="test-prov")
        assert isinstance(res, dict) and res.get("status") == "success"
        data = res.get("data")
        assert data is not None

        # Metrics should have been updated from the fake pack
        assert getattr(server, "_last_query_tokens_sent", 0) == 42
        assert getattr(server, "_last_query_tokens_saved", 0) == 10
        assert int(getattr(server, "_tokens_sent_total", 0)) >= 42
        assert int(getattr(server, "_tokens_saved_total", 0)) >= 10
        assert int(getattr(server, "_cache_tokens_saved_total", 0)) >= 3
        assert int(getattr(server, "_compression_tokens_saved_total", 0)) >= 2

        # get_stats should reflect the last query and totals
        stats = server._handle_get_stats()
        assert stats.get("status") == "success"
        stats_data = stats.get("data", {})
        assert stats_data.get("last_query_total_tokens") == 42
        assert int(stats_data.get("tokens_sent_total", 0)) >= 42

    finally:
        # Cleanup module from sys.modules to avoid side effects
        try:
            del sys.modules[name]
        except Exception:
            pass
