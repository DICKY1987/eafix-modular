"""Code evidence patches must reject stale bytes and incorrect line locators."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'governance/module_consolidation'))
from apply_reviewed_candidates import verify_reviewed_source
from authority_core import file_sha


def source_change(tmp_path):
    p=tmp_path/'source.py';p.write_text('header\nvalue = 3\ntail\n')
    return p,{'source_path':'source.py','source_sha256':file_sha(p),'source_line_start':2,'source_line_end':2,'reviewed_source_text':'value = 3\n'}


def test_exact_code_locator_passes(tmp_path):
    _,change=source_change(tmp_path)
    verify_reviewed_source(change,tmp_path)


def test_code_edit_is_stale(tmp_path):
    p,change=source_change(tmp_path);p.write_text('header\nvalue = 4\ntail\n')
    with pytest.raises(ValueError,match='Stale'):verify_reviewed_source(change,tmp_path)


@pytest.mark.parametrize('start,end',[(0,2),(3,2),(1,9)])
def test_invalid_locator_rejected(tmp_path,start,end):
    _,change=source_change(tmp_path);change.update(source_line_start=start,source_line_end=end)
    with pytest.raises(ValueError,match='Invalid'):verify_reviewed_source(change,tmp_path)


def test_wrong_reviewed_text_rejected(tmp_path):
    _,change=source_change(tmp_path);change['reviewed_source_text']='value = 4\n'
    with pytest.raises(ValueError,match='locator/text'):verify_reviewed_source(change,tmp_path)
