"""
Unit tests for the trad.application.filters.regular.merge module merging Summits.
"""

from contextlib import AbstractContextManager, nullcontext

import pytest

from trad.application.filters.regular.merge import (
    MergeFilter,
    _SummitMerger,
)
from trad.application.pipes import CollectedData
from trad.kernel.entities import GeoPosition, Summit
from trad.kernel.errors import MergeConflictError


@pytest.mark.parametrize(
    ("existing_summits", "add_summit", "expected_summit_list"),
    [
        # Simple adding of a new summit
        ([], Summit("Summit"), [Summit("Summit")]),
        # Don't create double entries within a list
        (
            [Summit(alternate_names=["Alt1", "Alt2"], unspecified_names=["Unspec1", "Unspec2"])],
            Summit(alternate_names=["Alt2", "Alt3"], unspecified_names=["Unspec2", "Unspec3"]),
            [
                Summit(
                    alternate_names=["Alt1", "Alt2", "Alt3"],
                    unspecified_names=["Unspec1", "Unspec2", "Unspec3"],
                )
            ],
        ),
        # Merge different name variants
        (
            [Summit("Mons Permuta", low_grade_position=GeoPosition(504620000, 147390000))],
            Summit("Permuta, Mons", high_grade_position=GeoPosition(504620000, 147390000)),
            [
                Summit(
                    "Mons Permuta",
                    high_grade_position=GeoPosition(504620000, 147390000),
                    low_grade_position=GeoPosition(504620000, 147390000),
                )
            ],
        ),
        # Merge multiple Summits into one if new information reveals that this is necessary
        (
            [Summit(unspecified_names=["Name1"]), Summit(unspecified_names=["Name2"])],
            Summit(official_name="Name1", alternate_names=["Name2"]),
            [
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    unspecified_names=["Name1", "Name2"],
                )
            ],
        ),
        # ... at least it their positions are close together
        (
            [
                Summit(
                    unspecified_names=["Name1"],
                    low_grade_position=GeoPosition(404620000, 247390000),
                ),
                Summit(
                    unspecified_names=["Name2"],
                    low_grade_position=GeoPosition(404621000, 247389000),
                ),
            ],
            Summit(
                official_name="Name1",
                alternate_names=["Name2"],
                high_grade_position=GeoPosition(404620000, 247390000),
            ),
            [
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    unspecified_names=["Name1", "Name2"],
                    high_grade_position=GeoPosition(404620000, 247390000),
                    low_grade_position=GeoPosition(404620000, 247390000),
                )
            ],
        ),
        # Two summits with the same name that are too far away from each other must not be
        # merged
        (
            [Summit(official_name="Name1", high_grade_position=GeoPosition(304620000, 547390000))],
            Summit(official_name="Name1", high_grade_position=GeoPosition(547390000, 304620000)),
            [
                Summit(
                    official_name="Name1", high_grade_position=GeoPosition(304620000, 547390000)
                ),
                Summit(
                    official_name="Name1", high_grade_position=GeoPosition(547390000, 304620000)
                ),
            ],
        ),
        (
            [
                Summit(
                    unspecified_names=["Name2"],
                    low_grade_position=GeoPosition(404630000, 247380000),
                ),
            ],
            Summit(
                official_name="Name1",
                alternate_names=["Name2"],
                high_grade_position=GeoPosition(247390000, 404620000),
            ),
            [
                Summit(
                    unspecified_names=["Name2"],
                    low_grade_position=GeoPosition(404630000, 247380000),
                ),
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    high_grade_position=GeoPosition(247390000, 404620000),
                ),
            ],
        ),
        # Don't change other existing summits
        (
            [Summit("S1"), Summit("S2", high_grade_position=GeoPosition(404620000, 247390000))],
            Summit("S3", high_grade_position=GeoPosition(504620000, 147390000)),
            [
                Summit("S1"),
                Summit("S2", high_grade_position=GeoPosition(404620000, 247390000)),
                Summit("S3", high_grade_position=GeoPosition(504620000, 147390000)),
            ],
        ),
        (
            [
                Summit("S1", low_grade_position=GeoPosition(304620000, 347390000)),
                Summit("S2", low_grade_position=GeoPosition(504620000, 147391000)),
                Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
            ],
            Summit("S2", high_grade_position=GeoPosition(504620000, 147390000)),
            [
                Summit("S1", low_grade_position=GeoPosition(304620000, 347390000)),
                Summit(
                    "S2",
                    high_grade_position=GeoPosition(504620000, 147390000),
                    low_grade_position=GeoPosition(504620000, 147391000),
                ),
                Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
            ],
        ),
    ],
)
def test_merge_summits(
    existing_summits: list[Summit],
    add_summit: Summit,
    expected_summit_list: list[Summit],
) -> None:
    """
    Ensures that add_summit() collects and merges Summit data properly:
     - A Summit not already available is simply added
     - An existing Summit's data is enriched
     - Unrelated existing Summits must not be changed
     - When adding additional names, several existing Summits may have to be merged into one

    :param existing_summits: List of Summits that are already stored in the input pipe.
    :param add_summit: The Summit object to add to the Pipe.
    :param expected_summit_list: List of Summits expected to be stored in the output pipe after
        the filter run.
    """
    input_pipe = CollectedData()
    output_pipe = CollectedData()

    for summit in existing_summits:
        input_pipe.add_summit(summit)
    input_pipe.add_summit(add_summit)

    # The actual test case: Run the filter
    merge_filter = MergeFilter()
    merge_filter.execute_filter(input_pipe, output_pipe)

    # Check the resulting summit list and data
    for real, expected in zip(
        (s for i, s in output_pipe.iter_summits()),
        expected_summit_list,
        strict=True,
    ):
        assert real.official_name == expected.official_name
        assert sorted(real.alternate_names) == sorted(expected.alternate_names)
        assert sorted(real.unspecified_names) == sorted(expected.unspecified_names)
        assert real.high_grade_position.is_equal_to(expected.high_grade_position)
        assert real.low_grade_position.is_equal_to(expected.low_grade_position)


@pytest.mark.parametrize(
    ("input_summits", "expected_error"),
    [
        # Error case: Conflicting position data (same name but positions are close together),
        # existing data must not be changed!
        (
            [
                Summit("S1"),
                Summit("S2", high_grade_position=GeoPosition(304620000, 547390000)),
                Summit("S3", high_grade_position=GeoPosition(404620000, 247390000)),
                Summit("S2", high_grade_position=GeoPosition(304621000, 547389000)),
            ],
            MergeConflictError,
        ),
    ],
)
def test_summit_merge_conflict(
    input_summits: list[Summit], expected_error: type[Exception]
) -> None:
    """
    Ensures that trying to merge summit data with unresolvable conflicts raises.

    :param input_summits: List of Summits that are stored in the input pipe.
    :param expected_error: The exception type that must be raised.
    """
    input_pipe = CollectedData()
    output_pipe = CollectedData()

    for summit in input_summits:
        input_pipe.add_summit(summit)

    merge_filter = MergeFilter()
    with pytest.raises(expected_error):
        merge_filter.execute_filter(input_pipe, output_pipe)


@pytest.mark.parametrize(
    ("existing_summit", "summit_to_merge", "expected_summit", "failure_context"),
    [
        # Merge position data into an existing summit
        (
            Summit("Summit 1"),
            Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
            Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
            nullcontext(),
        ),
        (
            Summit("Summit 1"),
            Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
            Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
            nullcontext(),
        ),
        (
            Summit("Summit 1", high_grade_position=GeoPosition(504567000, 147650000)),
            Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
            Summit(
                "Summit 1",
                high_grade_position=GeoPosition(504567000, 147650000),
                low_grade_position=GeoPosition(504620000, 147390000),
            ),
            nullcontext(),
        ),
        (
            Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
            Summit("Summit 1", low_grade_position=GeoPosition(504620000, 147390000)),
            Summit("Summit 1", low_grade_position=GeoPosition(504567000, 147650000)),
            nullcontext(),
        ),
        # Merging equal position datá must not raise an error
        (
            Summit("Summit 1", high_grade_position=GeoPosition(504620000, 147390000)),
            Summit(
                "Summit 1",
                alternate_names=["Summit 2"],
                high_grade_position=GeoPosition(504620000, 147390000),
            ),
            Summit(
                "Summit 1",
                alternate_names=["Summit 2"],
                high_grade_position=GeoPosition(504620000, 147390000),
            ),
            nullcontext(),
        ),
        # Merge multiple names in various variants
        (
            Summit(official_name="Official", alternate_names=["Alt1", "Alt2"]),
            Summit(official_name="Official", alternate_names=["Alt3"]),
            Summit(official_name="Official", alternate_names=["Alt1", "Alt2", "Alt3"]),
            nullcontext(),
        ),
        (
            Summit(official_name="Official", alternate_names=["Alt2"]),
            Summit(alternate_names=["Official", "Alt3"]),
            Summit(official_name="Official", alternate_names=["Alt2", "Alt3"]),
            nullcontext(),
        ),
        (
            Summit(unspecified_names=["Unspec"]),
            Summit(official_name="Name", alternate_names=["Alt1", "Alt2"]),
            Summit(
                official_name="Name",
                alternate_names=["Alt1", "Alt2"],
                unspecified_names=["Unspec"],
            ),
            nullcontext(),
        ),
        # Error Cases
        (
            Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
            Summit("Summit", high_grade_position=GeoPosition(404620000, 247390000)),
            Summit("Summit", high_grade_position=GeoPosition(504620000, 147390000)),
            pytest.raises(MergeConflictError),
        ),
    ],
)
def test_enrich_summit(
    existing_summit: Summit,
    summit_to_merge: Summit,
    expected_summit: Summit,
    failure_context: AbstractContextManager[None],
) -> None:
    """
    Tests the enrichment ("merge") of an existing Summit object with data from another one:

    - Position data is added if there is none already
    - The official name is set if it is not already
    - All alternate and unspecified names are added to the existing Summit
    - The official name must not be included in the alternate names list
    - Unresolvable merge conflicts raise a MergeConflictError (preserving existing data)
    """
    with failure_context:
        _SummitMerger.enrich_summit(target=existing_summit, source=summit_to_merge)

        assert existing_summit.official_name == expected_summit.official_name
        assert sorted(existing_summit.alternate_names) == sorted(expected_summit.alternate_names)
        assert sorted(existing_summit.unspecified_names) == sorted(
            expected_summit.unspecified_names
        )
        assert existing_summit.high_grade_position.is_equal_to(expected_summit.high_grade_position)

        assert existing_summit.low_grade_position.is_equal_to(expected_summit.low_grade_position)
