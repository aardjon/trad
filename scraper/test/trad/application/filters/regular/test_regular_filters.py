"""
Unit tests for all features that must work exactly the same for all trad.application.filters.regular
filters.
"""

import pytest

from trad.application.filters.regular.merge import MergeFilter
from trad.application.filters.regular.validation import DataValidationFilter
from trad.application.pipes import CollectedData
from trad.kernel.boundaries.filters import Filter
from trad.kernel.entities import ExternalSource


@pytest.mark.parametrize("filter_class", [MergeFilter, DataValidationFilter])
@pytest.mark.parametrize(
    "source_labels",
    [
        [],
        ["My private summit book"],
        ["SourceA", "SourceB", "SourceC"],
    ],
)
def test_transfer_sources(filter_class: type[Filter], source_labels: list[str]) -> None:
    """
    Ensures that the intermediate filters transfer all external sources from the input pipe as they
    are.

    :param filter_class: Filter class to test
    :param source_labels: Labels of all sources in the input pipe.
    """
    input_sources = [
        ExternalSource(label, f"http://{label}", f"{label} authors", f"{label} licence")
        for label in source_labels
    ]

    input_pipe = CollectedData()
    output_pipe = CollectedData()

    for source in input_sources:
        input_pipe.add_source(source)

    # The actual test case: Create and run the filter
    merge_filter = filter_class()
    merge_filter.execute_filter(input_pipe, output_pipe)

    # The output pipe must now contain exactly the same source data as the input pipe
    output_sources = output_pipe.get_sources()

    for input_source, output_source in zip(
        sorted(input_sources, key=lambda s: s.label),
        sorted(output_sources, key=lambda s: s.label),
        strict=True,
    ):
        assert input_source.label == output_source.label
        assert input_source.url == output_source.url
        assert input_source.attribution == output_source.attribution
        assert input_source.license_name == output_source.license_name
