from core.config import settings
from core.teslacam import TeslaCamMonitor


def test_teslacam_monitor_init():
    monitor = TeslaCamMonitor(settings)
    assert monitor.config == settings
