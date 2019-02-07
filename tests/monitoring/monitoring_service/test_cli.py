import logging
from typing import List
from unittest.mock import DEFAULT, patch

from click.testing import CliRunner

from monitoring_service.cli import main

patch_args = dict(
    target='monitoring_service.cli',
    MonitoringService=DEFAULT,
    HTTPProvider=DEFAULT,
)
DEFAULT_ARGS: List[str] = [
    '--private-key', '0x' + '1' * 40,
    '--state-db', ':memory:',
]


def test_success():
    """ Calling the request_collector with default args should succeed after heavy mocking """
    runner = CliRunner()
    with patch.multiple(**patch_args):
        result = runner.invoke(main, DEFAULT_ARGS, catch_exceptions=False)
    assert result.exit_code == 0


def test_shutdown():
    """ Clean shutdown after KeyboardInterrupt """
    runner = CliRunner()
    with patch.multiple(**patch_args) as mocks:
        mocks['MonitoringService'].return_value.run.side_effect = KeyboardInterrupt
        result = runner.invoke(main, DEFAULT_ARGS, catch_exceptions=False)
        assert result.exit_code == 0


def test_log_level():
    """ Setting of log level via command line switch """
    runner = CliRunner()
    with patch('request_collector.cli.logging.basicConfig') as basicConfig:
        for log_level in ('CRITICAL', 'WARNING'):
            runner.invoke(main, DEFAULT_ARGS + ['--log-level', log_level])
            # pytest already initializes logging, so basicConfig does not have
            # an effect. Use mocking to check that it's called properly.
            assert logging.getLevelName(
                basicConfig.call_args[1]['level'] == log_level,
            )
