#!/usr/bin/env python3
"""Rebuild response_getrecords_dcat_*.xml from result_1_dcat.xml / result_2_dcat.xml.

Run from the ckanext-geocat repo root after editing the canonical DCAT fixtures.
"""

import os
import xml.etree.ElementTree as ET
from typing import List

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(
    REPO_ROOT, "ckanext", "geocat", "tests", "fixtures", "test_harvesters"
)


def _load_dataset(filename: str) -> ET.Element:
    path = os.path.join(FIXTURES, filename)
    with open(path, "rb") as f:
        root = ET.fromstring(f.read())
    for el in root.iter():
        if el.tag.endswith("Dataset") and "dcat" in el.tag:
            return el
    raise SystemExit(f"no dcat:Dataset in {path}")


def _write_batch(
    path: str, datasets: List[ET.Element], matched: int, returned: int
) -> None:
    get_records_response = ET.Element(
        "{http://www.opengis.net/cat/csw/2.0.2}GetRecordsResponse"
    )
    csw_search_results = ET.SubElement(
        get_records_response, "{http://www.opengis.net/cat/csw/2.0.2}SearchResults"
    )
    csw_search_results.set("numberOfRecordsMatched", str(matched))
    csw_search_results.set("numberOfRecordsReturned", str(returned))
    csw_search_results.set("nextRecord", "0")
    for dataset_el in datasets:
        get_records_response.append(dataset_el)
    out = ET.tostring(get_records_response, encoding="unicode")
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(out)


def main() -> None:
    dataset_record_1 = _load_dataset("result_1_dcat.xml")
    dataset_record_2 = _load_dataset("result_2_dcat.xml")
    _write_batch(
        os.path.join(FIXTURES, "response_getrecords_dcat_batch.xml"),
        [dataset_record_1, dataset_record_2],
        2,
        2,
    )
    _write_batch(
        os.path.join(FIXTURES, "response_getrecords_dcat_one.xml"),
        [dataset_record_1],
        1,
        1,
    )
    print(
        "Wrote response_getrecords_dcat_batch.xml and response_getrecords_dcat_one.xml"
    )


if __name__ == "__main__":
    main()
