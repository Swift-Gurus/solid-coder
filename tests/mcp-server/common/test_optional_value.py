"""Tests functional transformations over nullable values."""

from common.optional_value import OptionalValue


class TestOptionalValue:
    def test_maps_present_value_and_returns_fallback(self) -> None:
        result = (
            OptionalValue.from_nullable("value")
            .map(str.upper)
            .value_or("missing")
        )

        assert result == "VALUE"

    def test_skips_transformations_for_missing_value(self) -> None:
        transformed = False

        def transform(value: str) -> str:
            nonlocal transformed
            transformed = True
            return value.upper()

        result = (
            OptionalValue.from_nullable(None)
            .map(transform)
            .value_or("missing")
        )

        assert result == "missing"
        assert transformed is False

    def test_flat_maps_present_value(self) -> None:
        result = (
            OptionalValue.from_nullable("42")
            .flat_map(
                lambda value: OptionalValue.from_nullable(int(value))
            )
            .value_or(0)
        )

        assert result == 42

    def test_runs_only_the_matching_side_effect(self) -> None:
        effects: list[str] = []

        present = (
            OptionalValue.from_nullable("value")
            .do(lambda value: effects.append(value))
            .on_none(lambda: effects.append("unexpected"))
        )
        missing = (
            OptionalValue.from_nullable(None)
            .do(lambda value: effects.append(str(value)))
            .on_none(lambda: effects.append("missing"))
        )

        assert present.value_or("fallback") == "value"
        assert missing.value_or("fallback") == "fallback"
        assert effects == ["value", "missing"]
