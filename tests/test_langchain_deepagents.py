import importlib.util
import sys
import types
from pathlib import Path


def _load_module(monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    deepagents = types.ModuleType("deepagents")
    deepagents.HarnessProfile = type("HarnessProfile", (), {})
    deepagents.create_deep_agent = lambda *args, **kwargs: object()
    deepagents.register_harness_profile = lambda *args, **kwargs: None

    deepagents_backends = types.ModuleType("deepagents.backends")
    deepagents_backends.LocalShellBackend = object

    deepagents_models = types.ModuleType("deepagents._models")
    deepagents_models.get_model_identifier = lambda model: "id"
    deepagents_models.get_model_provider = lambda model: "provider"

    langchain_chat_models = types.ModuleType("langchain.chat_models")
    langchain_chat_models.init_chat_model = lambda **kwargs: object()

    connectors = types.ModuleType("connectors")
    connectors.build_messaging_tools = lambda: []

    monkeypatch.setitem(sys.modules, "deepagents", deepagents)
    monkeypatch.setitem(sys.modules, "deepagents.backends", deepagents_backends)
    monkeypatch.setitem(sys.modules, "deepagents._models", deepagents_models)
    monkeypatch.setitem(sys.modules, "langchain.chat_models", langchain_chat_models)
    monkeypatch.setitem(sys.modules, "connectors", connectors)

    spec = importlib.util.spec_from_file_location(
        "langchain_deepagents_under_test", repo_root / "langchain-deepagents.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_dev_command_uses_public_host_for_codespaces_port_forwarding(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setenv("CODESPACES", "true")
    monkeypatch.setenv("CODESPACE_NAME", "demo-space")
    monkeypatch.setenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    monkeypatch.setenv("LANGGRAPH_TUNNEL", "0")

    cmd, use_tunnel = module._build_dev_command([])

    assert use_tunnel is False
    assert "--host" in cmd
    assert cmd[cmd.index("--host") + 1] == "0.0.0.0"
