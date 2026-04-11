"""
Unit tests for the trad.application.filters.source.sandsteinklettern filter implementation testing
the processing of summits.

TODO: Test Cases:
 - Error cases (exception)
"""

from typing import Final

import pytest

from trad.application.filters.source.sandsteinklettern.api import JsonGipfelStatus, JsonGipfelTyp
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Summit

from .conftest import JsonTestData, PreparedFilterRunner

_allowed_summit_types: Final = (JsonGipfelTyp.REGULAR, JsonGipfelTyp.CRAG)
_allowed_summit_status: Final = (
    JsonGipfelStatus.OPEN,
    JsonGipfelStatus.PARTIALLY_CLOSED,
    JsonGipfelStatus.OCCASIONALLY_CLOSED,
)


def _create_position(lat: float, lon: float) -> RankedValue[GeoPosition]:
    return RankedValue.create_valid(GeoPosition.from_decimal_degree(lat, lon), 11)


@pytest.mark.parametrize(
    ("summit_json_data", "expected_summit"),
    [  # All summit names must be respected
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                position=_create_position(50.89023, 14.04374),
            ),
            id="single name (german)",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "",
                "gipfelname_cz": "Mons Exempli",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                position=_create_position(50.89023, 14.04374),
            ),
            id="single name (czech)",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Einserturm (Zweierturm)",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Einserturm", "Zweierturm"],
                position=_create_position(50.89023, 14.04374),
            ),
            id="multiple names",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe",
                "gipfelname_cz": "Sněžka",
                "status": "",
                "typ": "G",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Sněžka"],
                position=_create_position(50.735989, 15.73965),
            ),
            id="different languages",
        ),
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe (Riesenkoppe)",
                "gipfelname_cz": "Sněžka (Śnieżka)",
                "status": "",
                "typ": "G",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Riesenkoppe", "Sněžka", "Śnieżka"],
                position=_create_position(50.735989, 15.73965),
            ),
            id="multiple languages and names",
        ),
    ]
    + [  # All allowed summit types
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": typ.value,
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                position=_create_position(50.89023, 14.04374),
            ),
            id=f"typ={typ.value}",
        )
        for typ in _allowed_summit_types
    ]
    + [  # All allowed summit status
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": status.value,
                "typ": "G",
                "vgrd": "14.04374",
                "ngrd": "50.89023",
            },
            Summit(
                unspecified_names=["Mons Exempli"],
                position=_create_position(50.89023, 14.04374),
            ),
            id=f"status={status.value}",
        )
        for status in _allowed_summit_status
    ]
    + [  # Fix wrong summit names (only a single example)
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Zwergfels",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.1106220",
                "ngrd": "50.9013408",
            },
            Summit(
                unspecified_names=["Zwerg"],
                position=_create_position(50.9013408, 14.1106220),
            ),
            id="fix wrong name",
        )
    ]
    + [  # Ignore future API extensions
        pytest.param(
            {
                "gipfel_ID": "1",
                "gipfelname_d": "Schneekoppe",
                "gipfelname_cz": "Sněžka",
                "status": "",
                "typ": "G",
                "new_attribute": "test",
                "vgrd": "15.73965",
                "ngrd": "50.735989",
            },
            Summit(
                unspecified_names=["Schneekoppe", "Sněžka"],
                position=_create_position(50.735989, 15.73965),
            ),
            id="additional JSON field",
        ),
    ],
)
def test_import_summit(
    summit_json_data: dict[str, str],
    expected_summit: Summit,
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that all aspects of (valid) summit data can be imported correctly:
     - Summit names in different variants and combinations
     - All status value for at least sometimes accessible
     - "regular" and "crag" summit types
     - Summit position (tested implicitly with other test cases, because coordinates are mandatory)
     - Certain summit names are known to be wrong in the external source, and thus must be fixed

    The 'summit_json_data' input parameter is the (external) JSON representaion of the summit being
    imported (the 'sektorid' attribute is added automatically), the 'expected_summit'
    parameter is the expected Summit object.
    """
    summit_json_data.update({"sektorid": "2"})
    minimal_data_sample["summits"] = [summit_json_data]
    minimal_data_sample["routes"] = []
    minimal_data_sample["posts"] = []

    output_pipe = run_prepared_filter(minimal_data_sample)

    # The resulting list must contain exactly one (the expected) Summit
    actual_summit_list = [summit for _id, summit in output_pipe.iter_summits()]
    assert len(actual_summit_list) == 1
    actual_summit = actual_summit_list[0]
    assert actual_summit.official_name == expected_summit.official_name
    assert sorted(actual_summit.alternate_names) == sorted(expected_summit.alternate_names)
    assert sorted(actual_summit.unspecified_names) == sorted(expected_summit.unspecified_names)
    assert actual_summit.position.value.is_equal_to(expected_summit.position.value)


@pytest.mark.parametrize(
    "summit_json_data",
    [  # Ignore all summit types except "regular" and "crag"
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": typ.value,
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"typ='{typ.value}'",
        )
        for typ in JsonGipfelTyp
        if typ not in _allowed_summit_types
    ]
    + [  # Ignore externally new (=unknown) summit types
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "",
                "typ": "NEW_AND_UNKNOWN",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="externally new 'typ'",
        )
    ]
    + [  # Ignore all summits that are not at least partially opened ("status")
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": status.value,
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"status='{status.value}'",
        )
        for status in JsonGipfelStatus
        if status not in _allowed_summit_status
    ]
    + [  # Ignore externally new (=unknown) summit status
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "Mons Exempli",
                "gipfelname_cz": "",
                "status": "NEW_AND_UNKNOWN",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="externally new 'status'",
        )
    ]
    + [  # Ignore summits without any name
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": "",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id="no name",
        )
    ]
    + [  # Ignore summits with certain names
        pytest.param(
            {
                "gipfel_ID": "4711",
                "gipfelname_d": f"Übungsstelle {nr}",
                "gipfelname_cz": "",
                "status": "",
                "typ": "G",
                "vgrd": "14.04544",
                "ngrd": "50.84041",
            },
            id=f"name=Übungsstelle {nr}",
        )
        for nr in ("A", "B", "C")
    ],
)
def test_ignore_summit(
    summit_json_data: dict[str, str],
    minimal_data_sample: JsonTestData,
    run_prepared_filter: PreparedFilterRunner,
) -> None:
    """
    Ensure that items with certain attributes must be ignored from the retrived summits list:
     - Most known summit types
     - Summits with a status that is not explicitly allowed
     - Summits that are never accessible
     - Summits whose name start with certain strings (no real summits that are not tagged separately
       in the external source)
     - Summits without a name
     - New summit types and status we don't know about (in case the external API is extended)

    Input parameter is the (external) JSON representation of s single summit that must be ignored.
    The 'sektorid' attribute is added automatically by the test.
    """
    summit_json_data.update({"sektorid": "2"})
    minimal_data_sample["summits"] = [summit_json_data]
    minimal_data_sample["routes"] = []
    minimal_data_sample["posts"] = []

    output_pipe = run_prepared_filter(minimal_data_sample)

    # The resulting list of Summits must be empty
    assert not list(output_pipe.iter_summits())
