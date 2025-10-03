import os
import sys
import shutil
import tempfile
from unittest import mock

# Ensure we can import Ai App modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Ai App'))

from pc_controller import PCController


def test_scaffold_static_project_tmpdir(tmp_path, monkeypatch):
    # Create controller
    ctrl = PCController()

    # Force no Ollama client available by patching import
    monkeypatch.setattr('pc_controller.OllamaClient', None, raising=False)

    # Run create command in a temp working dir
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    res = ctrl.handle_create_web_project('create web mysite')

    assert res['success'] is True
    assert 'mysite' in res['path'] or 'web_project_' in res['path']

    # Check files created
    assert os.path.isdir(res['path'])
    assert os.path.exists(os.path.join(res['path'], 'index.html'))
    assert os.path.exists(os.path.join(res['path'], 'styles.css'))
    assert os.path.exists(os.path.join(res['path'], 'app.js'))
    assert os.path.exists(os.path.join(res['path'], 'package.json'))

    # cleanup
    shutil.rmtree(res['path'])


def test_scaffold_vite_react(monkeypatch, tmp_path):
    ctrl = PCController()
    monkeypatch.chdir(tmp_path)

    # Mock OllamaClient to return deterministic values
    class MockOC:
        def get_response(self, prompt, lang='en'):
            if 'package.json' in prompt:
                return '{"name":"mock","version":"0.0.1"}'
            return '// mock file content'

    monkeypatch.setattr('pc_controller.OllamaClient', MockOC, raising=False)

    res = ctrl.handle_create_web_project('create web myapp react')
    assert res['success'] is True
    path = res['path']
    assert os.path.exists(os.path.join(path, 'package.json'))
    assert os.path.exists(os.path.join(path, 'index.html'))
    assert os.path.exists(os.path.join(path, 'src', 'main.jsx'))
    # cleanup
    shutil.rmtree(path)
