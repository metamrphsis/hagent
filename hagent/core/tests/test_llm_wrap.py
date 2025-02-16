#!/usr/bin/env python3
# See LICENSE for details

import os
import tempfile
import pytest
from unittest.mock import patch

from hagent.core.llm_wrap import LLM_wrap


def test_llm_wrap_caching():
    # Use existing configuration file for caching test.
    conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_wrap_conf1.yaml')

    lw = LLM_wrap()
    res = lw.from_file(name='test_caching', log_file='test_llm_wrap_caching.log', conf_file=conf_file)
    assert res

    jokes1 = lw.inference({}, 'use_prompt1', n=1)
    jokes2 = lw.inference({}, 'use_prompt1', n=1)

    # Since caching is enabled, both responses should match.
    assert len(jokes1) == 1
    assert len(jokes2) == 1
    assert jokes1[0].endswith(jokes2[0]), f'{jokes1} vs {jokes2}'


def test_llm_wrap_n_diff():
    conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_wrap_conf1.yaml')

    lw = LLM_wrap()
    ok = lw.from_file(name='test_caching', log_file='test_llm_wrap_caching.log', conf_file=conf_file)
    assert ok

    res = lw.inference({}, 'use_prompt_random', n=3)
    assert len(res) == 3
    assert res[0] != res[1]
    assert res[0] != res[2]


def test_bad_config_file_nonexistent():
    # Test with a non-existent configuration file.
    lw = LLM_wrap()
    non_existent_file = '/non/existent/conf.yaml'
    ok = lw.from_file('test_bad_config', non_existent_file, 'test_bad_config.log')
    assert not ok
    assert 'unable to read' in lw.last_error

    result = lw.inference({}, 'some_prompt', n=1)
    # Expect empty result and an error about missing llm "model".
    assert 'unable to read' in lw.last_error
    assert result == []

def test_bad_prompt():
    # Test with a non-existent configuration file.
    conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_wrap_conf1.yaml')

    lw = LLM_wrap()
    res = lw.from_file(name='test_caching', log_file='test_llm_wrap_caching.log', conf_file=conf_file)
    assert res

    result = lw.inference({}, 'some_bad_prompt', n=1)

    assert 'unable to find' in lw.last_error
    assert result == []

def test_bad_config_file_bad_yaml():
    # Create a temporary file with invalid YAML content.
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write('invalid: [yaml, : :')
        tmp_path = tmp.name
    try:
        lw = LLM_wrap()
        ok = lw.from_file('test_bad_yaml', tmp_path, 'test_bad_yaml.log')
        assert not ok
        assert 'reading conf_file' in lw.last_error

        result = lw.inference({}, 'some_prompt', n=1)
        assert result == []
        assert 'reading conf_file' in lw.last_error
    finally:
        os.unlink(tmp_path)


def test_missing_env_var():
    original_value = os.environ.get("FIREWORKS_AI_API_KEY")

    # Remove the environment variable
    if "FIREWORKS_AI_API_KEY" in os.environ:
        del os.environ["FIREWORKS_AI_API_KEY"]

        # Use existing configuration file for caching test.
        conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_wrap_conf1.yaml')

        lw = LLM_wrap()
        lw.from_file(name='test_caching', log_file='test_llm_wrap_caching.log', conf_file=conf_file)

        with pytest.raises(ValueError):
            jokes = lw.inference({}, 'use_prompt1', n=1)

        print(f"XX{lw.last_error}")
        assert "Environment" in lw.last_error
    else:
        assert False, "Must set FIREWORKS_AI_API_KEY for unit test"



if __name__ == '__main__':  # pragma: no cover
    test_llm_wrap_caching()
    test_llm_wrap_n_diff()
    test_bad_config_file_nonexistent()
    test_bad_config_file_bad_yaml()
    test_missing_env_var()
    test_bad_prompt()

