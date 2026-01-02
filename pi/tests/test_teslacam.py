from core.teslacam import TeslaCamMonitor
from core.config import settings


def test_teslacam_monitor_init():
    monitor = TeslaCamMonitor(settings)
    assert monitor.config == settings
