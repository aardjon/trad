"""
Unit tests for the trad.kernel.entities.names module.
"""

import pytest

from trad.kernel.entities.names import NormalizedName


class TestNormalizedName:
    """
    Unit tests for the NormalizedName class.
    """

    @pytest.mark.parametrize(
        ("object_name", "expected_normalization"),
        [
            ("AbCDe", "abcde"),  # Lower-case the name
            ("aäböcüdße", "abcde"),  # Remove german umlauts
            ("ab cd,ef-gh", "ab_cd_ef_gh"),  # Split at space and punctuation
            ("ef cd ab", "ab_cd_ef"),  # Order the segments correctly
            # Some real-world examples from Sächsische Schweiz, combining conversions
            ("Gamrigkegel", "gamrigkegel"),
            ("Müllerstein", "mllerstein"),
            ("Berggießhübler Turm, Westlicher", "berggiehbler_turm_westlicher"),
            ("Zerborstener Turm, Erster", "erster_turm_zerborstener"),
            ("Erster zerborstener Turm", "erster_turm_zerborstener"),
            ("Glück-Auf-Turm", "auf_glck_turm"),
            ("Glück Auf Turm", "auf_glck_turm"),
            ("Liebespaar, Südturm", "liebespaar_sdturm"),
            ("Liebespaar Südturm", "liebespaar_sdturm"),
            ("Lokomotive - Esse", "esse_lokomotive"),
            ("Lokomotive-Esse", "esse_lokomotive"),
        ],
    )
    def test_creation(self, object_name: str, expected_normalization: str) -> None:
        """
        Tests the correct normalization and the string representation of the input value.
        """
        norm_name = NormalizedName(object_name)
        assert str(norm_name) == expected_normalization

    @pytest.mark.parametrize(
        ("a", "b", "expect_equality"),
        [
            (NormalizedName("qwertz"), NormalizedName("qwertz"), True),
            (NormalizedName("qwertz"), NormalizedName("QwErTz"), True),
            (NormalizedName("qwertz"), NormalizedName("qwarks"), False),
        ],
    )
    def test_comparison(
        self, a: NormalizedName, b: NormalizedName, *, expect_equality: bool
    ) -> None:
        """
        Ensures that the equality comparison of NormalizedNames works as expected.
        """
        assert (a == b) is expect_equality
        assert (a != b) is not expect_equality

    def test_dict_support(self) -> None:
        """
        Ensures that NormalizedName objects can be used as dict keys.
        """
        ident1 = NormalizedName("test1")
        ident2 = NormalizedName("test2")

        id_dict = {ident1: "A", ident2: "B"}
        assert len(id_dict) == 2  # noqa: PLR2004
        assert ident1 in id_dict
        assert ident2 in id_dict
        assert id_dict[ident1] == "A"
        assert id_dict[ident2] == "B"
        assert id_dict[NormalizedName("TesT1")] == "A"
        assert id_dict[NormalizedName("TesT2")] == "B"
