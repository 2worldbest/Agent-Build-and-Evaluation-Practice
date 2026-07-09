import types

import gateway


def test_start_in_background_starts_telegram_only_once(monkeypatch):
    gateway._RUNNING_CHANNELS.clear()

    calls = []

    class DummyAdapter:
        def __init__(self, name):
            self.name = name

        def check(self):
            if self.name == "telegram":
                return ("ok", "ok")
            return ("unset", "")

        def run(self):
            calls.append(self.name)

    class FakeThread:
        def __init__(self, target, name=None, daemon=None):
            self.target = target
            self.name = name

        def start(self):
            self.target()

    monkeypatch.setattr(gateway, "TelegramAdapter", lambda: DummyAdapter("telegram"))
    monkeypatch.setattr(gateway, "SlackAdapter", lambda: DummyAdapter("slack"))
    monkeypatch.setattr(gateway, "EmailTriggerAdapter", lambda: DummyAdapter("email"))
    monkeypatch.setattr(gateway.threading, "Thread", FakeThread)
    monkeypatch.setattr(gateway, "set_agent", lambda agent: None)

    gateway.start_in_background(agent_factory=lambda: object())
    gateway.start_in_background(agent_factory=lambda: object())

    assert calls == ["telegram"]
