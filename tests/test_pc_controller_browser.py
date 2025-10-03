import os
import sys
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Ai App'))
from pc_controller import PCController


def test_open_url_prefers_mac_apps(monkeypatch, tmp_path):
    ctrl = PCController()
    # Simulate macOS
    monkeypatch.setattr(ctrl, 'system', 'darwin')

    called = {}

    def fake_exists(path):
        # pretend Chrome is installed
        if 'Google Chrome.app' in path:
            return True
        return False

    def fake_popen(args, **kwargs):
        called['args'] = args
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr('subprocess.Popen', fake_popen)

    res = ctrl.open_url('https://example.com')
    assert res['success'] is True
    assert 'Google Chrome' in res['message'] or 'Opened' in res['message']
