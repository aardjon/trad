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
from trad.kernel.entities.geotypes import GeoPosition
from trad.kernel.entities.ranked import RankedValue
from trad.kernel.entities.routedata import Summit
from trad.kernel.errors import MergeConflictError


def _create_position(lat: int, lon: int, rank: int) -> RankedValue[GeoPosition]:
    return RankedValue.create_valid(GeoPosition(lat, lon), rank)


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
            [Summit("Mons Permuta", position=_create_position(504620000, 147390000, 1))],
            Summit("Permuta, Mons", position=_create_position(504620000, 147390000, 11)),
            [
                Summit(
                    "Mons Permuta",
                    position=_create_position(504620000, 147390000, 1),
                )
            ],
        ),
        # Merge multiple Summits into one if new information reveals that this is necessary
        pytest.param(
            [Summit(unspecified_names=["Name1"]), Summit(unspecified_names=["Name2"])],
            Summit(official_name="Name1", alternate_names=["Name2"]),
            [
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    unspecified_names=["Name1", "Name2"],
                )
            ],
            id="Merge existing Summits: New name information",
        ),
        # ... at least it their positions are close together
        pytest.param(
            [
                Summit(
                    unspecified_names=["Name1"],
                    position=_create_position(404620000, 247390000, 12),
                ),
                Summit(
                    unspecified_names=["Name2"],
                    position=_create_position(404621000, 247389000, 13),
                ),
            ],
            Summit(
                official_name="Name1",
                alternate_names=["Name2"],
                position=_create_position(404620000, 247390000, 2),
            ),
            [
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    unspecified_names=["Name1", "Name2"],
                    position=_create_position(404620000, 247390000, 2),
                )
            ],
            id="Merge existing Summits: New name information and close positions",
        ),
        # Two summits with the same name that are too far away from each other must not be
        # merged
        (
            [Summit(official_name="Name1", position=_create_position(304620000, 547390000, 1))],
            Summit(official_name="Name1", position=_create_position(547390000, 304620000, 1)),
            [
                Summit(official_name="Name1", position=_create_position(304620000, 547390000, 1)),
                Summit(official_name="Name1", position=_create_position(547390000, 304620000, 1)),
            ],
        ),
        (
            [
                Summit(
                    unspecified_names=["Name2"],
                    position=_create_position(404630000, 247380000, 11),
                ),
            ],
            Summit(
                official_name="Name1",
                alternate_names=["Name2"],
                position=_create_position(247390000, 404620000, 2),
            ),
            [
                Summit(
                    unspecified_names=["Name2"],
                    position=_create_position(404630000, 247380000, 11),
                ),
                Summit(
                    official_name="Name1",
                    alternate_names=["Name2"],
                    position=_create_position(247390000, 404620000, 2),
                ),
            ],
        ),
        # Don't change other existing summits
        (
            [Summit("S1"), Summit("S2", position=_create_position(404620000, 247390000, 1))],
            Summit("S3", position=_create_position(504620000, 147390000, 1)),
            [
                Summit("S1"),
                Summit("S2", position=_create_position(404620000, 247390000, 1)),
                Summit("S3", position=_create_position(504620000, 147390000, 1)),
            ],
        ),
        (
            [
                Summit("S1", position=_create_position(304620000, 347390000, 12)),
                Summit("S2", position=_create_position(504620000, 147391000, 12)),
                Summit("S3", position=_create_position(404620000, 247390000, 2)),
            ],
            Summit("S2", position=_create_position(504620000, 147390000, 2)),
            [
                Summit("S1", position=_create_position(304620000, 347390000, 12)),
                Summit(
                    "S2",
                    position=_create_position(504620000, 147390000, 2),
                ),
                Summit("S3", position=_create_position(404620000, 247390000, 2)),
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
        sorted((s for i, s in output_pipe.iter_summits()), key=lambda s: s.official_name or ""),
        sorted(expected_summit_list, key=lambda s: s.official_name or ""),
        strict=True,
    ):
        assert real.official_name == expected.official_name
        assert sorted(real.alternate_names) == sorted(expected.alternate_names)
        assert sorted(real.unspecified_names) == sorted(expected.unspecified_names)
        assert real.position.rank == expected.position.rank
        assert real.position.is_null() == expected.position.is_null()
        assert real.position.rank == expected.position.rank
        if not expected.position.is_null():
            assert real.position.value.is_equal_to(expected.position.value)


@pytest.mark.parametrize(
    ("input_summits", "expected_error"),
    [
        # Error case: Conflicting position data (same name but positions are close together),
        # existing data must not be changed!
        (
            [
                Summit("S1"),
                Summit("S2", position=_create_position(304620000, 547390000, 1)),
                Summit("S3", position=_create_position(404620000, 247390000, 1)),
                Summit("S2", position=_create_position(304621000, 547389000, 1)),
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
        # Merge sector name into an existing summit
        (
            Summit("Summit", sector=RankedValue.create_null()),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 2)),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 2)),
            nullcontext(),
        ),
        (
            Summit("Summit", sector=RankedValue.create_valid("Sector", 7)),
            Summit("Summit", sector=RankedValue.create_null()),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 7)),
            nullcontext(),
        ),
        # Merge sector names of different ranks
        (
            Summit("Summit", sector=RankedValue.create_valid("Sector 1", 2)),
            Summit("Summit", sector=RankedValue.create_valid("Sector 2", 1)),
            Summit("Summit", sector=RankedValue.create_valid("Sector 2", 1)),
            nullcontext(),
        ),
        (
            Summit("Summit", sector=RankedValue.create_valid("Sector", 7)),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 5)),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 5)),
            nullcontext(),
        ),
        # Merging equal sector names must not raise an error
        (
            Summit("Summit", sector=RankedValue.create_valid("Sector", 3)),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 3)),
            Summit("Summit", sector=RankedValue.create_valid("Sector", 3)),
            nullcontext(),
        ),
        (
            Summit("Summit", sector=RankedValue.create_null()),
            Summit("Summit", sector=RankedValue.create_null()),
            Summit("Summit", sector=RankedValue.create_null()),
            nullcontext(),
        ),
        # Merge position data into an existing summit
        (
            Summit("Summit 1"),
            Summit("Summit 1", position=_create_position(504620000, 147390000, 1)),
            Summit("Summit 1", position=_create_position(504620000, 147390000, 1)),
            nullcontext(),
        ),
        (
            Summit("Summit 1"),
            Summit("Summit 1", position=_create_position(504620000, 147390000, 12)),
            Summit("Summit 1", position=_create_position(504620000, 147390000, 12)),
            nullcontext(),
        ),
        (
            Summit("Summit 1", position=_create_position(504567000, 147650000, 2)),
            Summit("Summit 1", position=_create_position(504620000, 147390000, 13)),
            Summit("Summit 1", position=_create_position(504567000, 147650000, 2)),
            nullcontext(),
        ),
        pytest.param(
            Summit("Summit", position=_create_position(504620000, 147390000, 2)),
            Summit("Summit", position=_create_position(504620000, 147390000, 5)),
            Summit("Summit", position=_create_position(504620000, 147390000, 2)),
            nullcontext(),
            id="Position: Same value, different rank",
        ),
        # Merging equal position datá must not raise an error
        (
            Summit("Summit 1", position=_create_position(504620000, 147390000, 2)),
            Summit(
                "Summit 1",
                alternate_names=["Summit 2"],
                position=_create_position(504620000, 147390000, 2),
            ),
            Summit(
                "Summit 1",
                alternate_names=["Summit 2"],
                position=_create_position(504620000, 147390000, 2),
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
            Summit("Summit", position=_create_position(504620000, 147390000, 1)),
            Summit("Summit", position=_create_position(404620000, 247390000, 1)),
            Summit("Summit", position=_create_position(504620000, 147390000, 1)),
            pytest.raises(MergeConflictError),
        ),
        (
            Summit("Summit", sector=RankedValue.create_valid("Sector 1", 2)),
            Summit("Summit", sector=RankedValue.create_valid("Sector 2", 2)),
            Summit("Summit", sector=RankedValue.create_valid("Sector 1", 2)),
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
    - Sector name is added if there is none already
    - Unresolvable merge conflicts raise a MergeConflictError (preserving existing data)
    """
    with failure_context:
        _SummitMerger.enrich_summit(target=existing_summit, source=summit_to_merge)

        assert existing_summit.official_name == expected_summit.official_name
        assert sorted(existing_summit.alternate_names) == sorted(expected_summit.alternate_names)
        assert sorted(existing_summit.unspecified_names) == sorted(
            expected_summit.unspecified_names
        )
        assert existing_summit.position.is_null() == expected_summit.position.is_null()
        assert existing_summit.position.rank == expected_summit.position.rank
        if not existing_summit.position.is_null():
            assert existing_summit.position.value.is_equal_to(expected_summit.position.value)
        assert existing_summit.sector == expected_summit.sector
