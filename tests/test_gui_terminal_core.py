import sys
from pathlib import Path


def _add_gui_path():
    root = Path(__file__).resolve().parents[1]
    gui_src = root / "gui_terminal" / "src"
    if str(gui_src) not in sys.path:
        sys.path.insert(0, str(gui_src))


def test_policy_manager_allows_echo():
    _add_gui_path()
    from gui_terminal.security.policy_manager import PolicyManager

    pm = PolicyManager()
    ok, reason = pm.command_allowed("echo hello")
    assert ok and "allowed" in reason


def test_event_bus_basic_pubsub():
    _add_gui_path()
    from gui_terminal.core.event_system import EventBus

    bus = EventBus()
    received = []

    def handler(payload):
        received.append(payload)

    bus.subscribe("topic", handler)
    bus.publish("topic", {"x": 1})
    assert received and received[0]["x"] == 1


def test_plugin_manager_discovers_and_loads(tmp_path):
    _add_gui_path()
    from gui_terminal.plugins.manager import PluginManager

    # Create a sample plugin file
    plugin_file = tmp_path / "sample_plugin.py"
    plugin_file.write_text(
        """
name = 'sample_plugin'

class _Plugin:
    def __init__(self):
        self.active = False
    def activate(self, context):
        self.active = True
    def deactivate(self):
        self.active = False

plugin = _Plugin()
        """
    )

    pm = PluginManager([str(tmp_path)])
    recs = pm.discover()
    assert any(r.name == "sample_plugin" for r in recs)

    loaded = False
    for rec in recs:
        lr = pm.load(rec)
        if lr and lr.name == "sample_plugin":
            loaded = True
    assert loaded

