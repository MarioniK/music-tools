import logging

from app import pipeline_logging


def test_pipeline_logging_configures_httpx_and_httpcore_to_warning_or_higher():
    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING
    assert pipeline_logging.logger.name == "tidal_parser"
