# -*- coding: utf-8 -*-
# inspired by https://github.com/Frozenball/pytest-sugar
import datetime
import os
import re

from subunit import StreamResultToBytes

import py
import pytest
from _pytest.terminal import TerminalReporter


def pytest_collection_modifyitems(session, config, items):
    if config.option.subunit:
        terminal_reporter = config.pluginmanager.getplugin('terminalreporter')
        terminal_reporter.tests_count += len(items)
    if config.option.subunit_load_list:
        with open(config.option.subunit_load_list) as f:
            to_run = f.readlines()
        to_run = [line.strip() for line in to_run]
        filtered = [item for item in items if item.nodeid in to_run]
        items[:] = filtered


def pytest_deselected(items):
    """ Update tests_count to not include deselected tests """
    if len(items) > 0:
        pluginmanager = items[0].config.pluginmanager
        terminal_reporter = pluginmanager.getplugin('terminalreporter')
        if (hasattr(terminal_reporter, 'tests_count')
                and terminal_reporter.tests_count > 0):
            terminal_reporter.tests_count -= len(items)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        '--subunit', action="store_true", dest="subunit", default=False,
        help=(
            "enable pytest-subunit"
        )
    )
    group._addoption(
        '--subunit-load-list', dest="subunit_load_list", default=False,
        help=(
            "Path to file with list of tests to run"
        )
    )


@pytest.mark.tryfirst
def pytest_load_initial_conftests(early_config, parser, args):
    # XXX: very hacky. Adding support for python setup.py testr --coverage
    # see https://github.com/testing-cabal/testrepository/blob/master/testrepository/setuptools_command.py#L106
    # For now it cannot run in parallel mode, in tox.ini there should be added
    # --testr-args='--concurrency=1'
    parsed_args = parser.parse_known_args(args)
    if parsed_args.subunit:
        python_env = os.environ.get('PYTHON', None)
        if python_env and python_env.startswith('coverage'):
            cov_plugin = early_config.pluginmanager.get_plugin('pytest_cov')
            # XXX: coverage plugin not installed. Silently ignoring
            if not cov_plugin:
                return
            # matching: coverage run --source (package) --parallel-mode
            coverage_pat = re.compile('coverage run --source (\w+) --parallel-mode')
            match = coverage_pat.match(python_env)
            cov_args = args + ['--cov']
            if match:
                package = match.groups()[0]
                cov_args += [package]
            cov_plugin.pytest_load_initial_conftests(early_config,
                                                     parser, cov_args)


@pytest.mark.trylast
def pytest_configure(config):
    if config.option.subunit:
        # Get the standard terminal reporter plugin and replace it with our
        standard_reporter = config.pluginmanager.getplugin('terminalreporter')
        subunit_reporter = SubunitTerminalReporter(standard_reporter)
        config.pluginmanager.unregister(standard_reporter)
        config.pluginmanager.register(subunit_reporter, 'terminalreporter')


_ZERO = datetime.timedelta(0)

class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return _ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return _ZERO

utc = UTC()


class SubunitTerminalReporter(TerminalReporter):
    def __init__(self, reporter):
        TerminalReporter.__init__(self, reporter.config)
        self.writer = self._tw
        self.tests_count = 0
        self.reports = []
        self.skipped = []
        self.failed = []
        self.result = StreamResultToBytes(self.writer._file)

    def _status(self, report, status):
        # task id
        test_id = report.nodeid

        # get time
        now = datetime.datetime.now(utc)

        # capture output
        writer=py.io.TerminalWriter(stringio=True)
        try:
            report.toterminal(writer)
        except:
            pass
        writer.stringio.seek(0)
        out = writer.stringio.read()
        out = str(out)

        # send status
        self.result.status(test_id=test_id,
                           test_status=status,
                           timestamp=now,
                           file_name=report.fspath,
                           file_bytes=out,
                           mime_type="text/plain; charset=utf8")

    def pytest_collectreport(self, report):
        pass

    def pytest_collection_finish(self, session):
        if self.config.option.collectonly:
            self._printcollecteditems(session.items)

    def pytest_collection(self):
        # Prevent shoving `collecting` message
        pass

    def report_collect(self, final=False):
        # Prevent shoving `collecting` message
        pass

    def pytest_sessionstart(self, session):
        pass

    def pytest_runtest_logstart(self, nodeid, location):
        pass

    def pytest_sessionfinish(self, session, exitstatus):
        # always exit with exitcode 0
        session.exitstatus = 0

    def pytest_runtest_logreport(self, report):
        self.reports.append(report)
        test_id = report.nodeid
        if report.when in ['setup', 'session']:
            self._status(report, 'exists')
            if report.outcome == 'passed':
                self._status(report, 'inprogress')
            if report.outcome == 'failed':
                self._status(report, 'fail')
        elif report.when in ['call']:
            if hasattr(report, "wasxfail"):
                if report.skipped:
                    self._status(report, 'xfail')
                elif report.failed:
                    self._status(report, 'uxsuccess')
            elif report.outcome == 'failed':
                self._status(report, 'fail')
                self.failed.append(test_id)
            elif report.outcome == 'skipped':
                self._status(report, 'skip')
                self.skipped.append(test_id)
        elif report.when in ['teardown']:
            if test_id not in self.skipped and test_id not in self.failed:
                if report.outcome == 'passed':
                    self._status(report, 'success')
                elif report.outcome == 'failed':
                    self._status(report, 'fail')
        else:
            raise Exception(str(report))

    def _printcollecteditems(self, items):
        for item in items:
            test_id = item.nodeid
            self.result.status(test_id=test_id, test_status='exists')

    def summary_stats(self):
        pass

    def summary_failures(self):
        # Prevent failure summary from being shown since we already
        # show the failure instantly after failure has occured.
        pass

    def summary_errors(self):
        # Prevent error summary from being shown since we already
        # show the error instantly after error has occured.
        pass
