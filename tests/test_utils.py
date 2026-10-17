import pytest

from conftest import PAGE_TEXTS

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def utils():
    import utils

    return utils


def test_get_page_count(utils, sample_pdf):
    assert utils.get_page_count(str(sample_pdf)) == len(PAGE_TEXTS)


def test_get_page_count_missing_file(utils, tmp_path):
    assert utils.get_page_count(str(tmp_path / "missing.pdf")) == 0


def test_ocr_to_text_all_pages(utils, sample_pdf):
    pages = sorted(utils.ocr_to_text(str(sample_pdf), grayscale=True), key=lambda p: p[1])
    assert [number for _, number in pages] == [1, 2]
    for (text, _), expected in zip(pages, PAGE_TEXTS):
        assert text.strip() == expected


def test_ocr_to_text_page_range(utils, sample_pdf):
    pages = list(utils.ocr_to_text(str(sample_pdf), first_page=2, last_page=2))
    assert len(pages) == 1
    assert pages[0][0].strip() == PAGE_TEXTS[1]


def test_ocr_to_text_negative_last_page(utils, sample_pdf):
    pages = list(utils.ocr_to_text(str(sample_pdf), last_page=-1))
    assert len(pages) == 1
    assert pages[0][0].strip() == PAGE_TEXTS[0]


def test_pdf_to_text_writes_file(utils, sample_pdf, tmp_path):
    assert utils.pdf_to_text(str(sample_pdf), str(tmp_path)) == ""
    assert (tmp_path / "sample.txt").exists()


def test_pdf_to_text_missing_file_returns_error(utils, tmp_path):
    error = utils.pdf_to_text(str(tmp_path / "missing.pdf"), str(tmp_path))
    assert error
