import re
from datetime import datetime

from src.etl.normalize import EXPORT_TIMESTAMP_FMT, export_timestamp


def test_export_timestamp_format():
    stamp = export_timestamp()
    assert re.fullmatch(r"\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2}", stamp)
    parsed = datetime.strptime(stamp, EXPORT_TIMESTAMP_FMT)
    assert parsed.year >= 2020
