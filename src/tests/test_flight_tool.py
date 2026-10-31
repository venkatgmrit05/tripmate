import pytest
import requests

from src.tools import flight_tool


class TestFlightToolHappyPaths:
    def test_clean_text_normalizes_and_removes_travel_words(self):
        assert flight_tool.clean_text("  Plan a 7-day Japan trip! ") == "a 7 japan"
        # assert flight_tool.clean_text("  Plan a 7-day Japan trip! ") == "a 8 japan"
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("USA", "US"),
            ("United Kingdom", "GB"),
            ("Plan a trip to Bangladesh", "BD"),
        ],
    )
    def test_country_name_to_code_resolves_aliases_and_names(self, text, expected):
        assert flight_tool.country_name_to_code(text) == expected

    def test_airport_country_matches_code_and_country_name(self):
        assert flight_tool.airport_country_matches({"country": "CA"}, "CA")
        assert flight_tool.airport_country_matches({"country": "Canada"}, "CA")

    def test_get_best_airport_uses_configured_preference(self, monkeypatch):
        monkeypatch.setattr(flight_tool, "COUNTRY_MAIN_AIRPORT", {"CA": "YYZ"})
        monkeypatch.setattr(flight_tool, "AIRPORTS", {"YYZ": {}})

        assert flight_tool.get_best_airport_for_country("CA") == "YYZ"

    def test_get_best_airport_scores_candidates_when_no_preference(self, monkeypatch):
        monkeypatch.setattr(flight_tool, "COUNTRY_MAIN_AIRPORT", {})
        monkeypatch.setattr(
            flight_tool,
            "AIRPORTS",
            {
                "AAA": {
                    "country": "ZZ",
                    "name": "Example International Airport",
                    "city": "Example City",
                },
                "BBB": {"country": "ZZ", "name": "Local Airport", "city": "Town"},
            },
        )

        assert flight_tool.get_best_airport_for_country("ZZ") == "AAA"

    def test_resolve_location_to_iata_handles_code_city_and_country(self):
        assert flight_tool.resolve_location_to_iata("YYZ") == "YYZ"
        assert flight_tool.resolve_location_to_iata("Toronto") == "YYZ"
        assert flight_tool.resolve_location_to_iata("Canada") == "YYZ"

    def test_parse_route_handles_explicit_route_and_global_query(self):
        assert flight_tool.parse_route("Flights from Toronto to London") == (
            "YYZ",
            "LHR",
        )
        assert flight_tool.parse_route("show all global flights") == (None, None)

    def test_format_flight_includes_flight_and_route_details(self):
        result = flight_tool.format_flight(
            {
                "airline": {"name": "Example Air"},
                "flight": {"iata": "EA123"},
                "flight_status": "active",
                "departure": {
                    "airport": "Toronto Pearson",
                    "iata": "YYZ",
                    "terminal": "1",
                    "gate": "A2",
                    "scheduled": "2026-10-30T10:00:00+00:00",
                    "delay": 12,
                },
                "arrival": {
                    "airport": "London Heathrow",
                    "iata": "LHR",
                    "terminal": "5",
                    "gate": "B3",
                    "scheduled": "2026-10-30T20:00:00+00:00",
                    "delay": None,
                },
            }
        )

        assert "Airline: Example Air" in result
        assert "Flight: EA123" in result
        assert "IATA: YYZ" in result
        assert "Delay: 12 minutes" in result
        assert "Airport: London Heathrow" in result
        assert "Delay: N/A" in result

    def test_search_flights_formats_mocked_api_response(self, monkeypatch):
        flight = {
            "airline": {"name": "Example Air"},
            "flight": {"iata": "EA123"},
            "departure": {"airport": "Toronto Pearson", "iata": "YYZ"},
            "arrival": {"airport": "London Heathrow", "iata": "LHR"},
        }
        response = type("Response", (), {"json": lambda self: {"data": [flight]}})()
        monkeypatch.setattr(flight_tool, "API_KEY", "test-key")
        calls = []

        def fake_get(url, *, params, timeout):
            calls.append((url, params, timeout))
            return response

        monkeypatch.setattr(flight_tool.requests, "get", fake_get)

        result = flight_tool.search_flights("Flights from Toronto to London")

        assert "Live flights from YYZ to LHR" in result
        assert "Flight: EA123" in result
        assert calls == [
            (
                flight_tool.BASE_URL,
                {
                    "access_key": "test-key",
                    "limit": 10,
                    "dep_iata": "YYZ",
                    "arr_iata": "LHR",
                },
                30,
            )
        ]


class TestFlightToolRainyDays:
    def test_country_name_to_code_returns_none_for_unknown_country(self):
        assert flight_tool.country_name_to_code("Atlantis") is None

    def test_get_best_airport_returns_none_when_no_candidates(self, monkeypatch):
        monkeypatch.setattr(flight_tool, "COUNTRY_MAIN_AIRPORT", {})
        monkeypatch.setattr(flight_tool, "AIRPORTS", {})

        assert flight_tool.get_best_airport_for_country("ZZ") is None

    def test_resolve_location_returns_none_for_blank_or_unknown_location(
        self, monkeypatch
    ):
        monkeypatch.setattr(flight_tool, "AIRPORTS", {})
        assert flight_tool.resolve_location_to_iata("") is None
        assert flight_tool.resolve_location_to_iata("Nowhereville") is None

    def test_parse_route_returns_no_codes_when_query_has_no_location(self):
        assert flight_tool.parse_route("find something interesting") == (None, None)

    def test_format_flight_uses_fallbacks_for_missing_fields(self):
        result = flight_tool.format_flight({})

        assert "Airline: Unknown airline" in result
        assert "Flight: Unknown flight number" in result
        assert "Airport: Unknown departure airport" in result
        assert "IATA: Unknown" in result
        assert "Delay: N/A" in result

    def test_search_flights_reports_missing_api_key(self, monkeypatch):
        monkeypatch.setattr(flight_tool, "API_KEY", None)

        result = flight_tool.search_flights("Flights from Toronto to London")

        assert "AVIATIONSTACK_API_KEY is missing" in result

    def test_search_flights_reports_request_failure(self, monkeypatch):
        monkeypatch.setattr(flight_tool, "API_KEY", "test-key")

        def raise_request_error(*args, **kwargs):
            raise requests.exceptions.Timeout("request timed out")

        monkeypatch.setattr(flight_tool.requests, "get", raise_request_error)

        result = flight_tool.search_flights("all flights")

        assert "Flight API request failed: request timed out" in result

    def test_search_flights_reports_invalid_json(self, monkeypatch):
        class InvalidJsonResponse:
            def json(self):
                raise ValueError("invalid JSON")

        monkeypatch.setattr(flight_tool, "API_KEY", "test-key")
        monkeypatch.setattr(
            flight_tool.requests,
            "get",
            lambda *args, **kwargs: InvalidJsonResponse(),
        )

        assert flight_tool.search_flights("all flights") == (
            "Flight API returned invalid JSON."
        )

    def test_search_flights_reports_api_error(self, monkeypatch):
        class ErrorResponse:
            def json(self):
                return {"error": {"code": "invalid_access_key", "message": "Bad key"}}

        monkeypatch.setattr(flight_tool, "API_KEY", "test-key")
        monkeypatch.setattr(
            flight_tool.requests,
            "get",
            lambda *args, **kwargs: ErrorResponse(),
        )

        result = flight_tool.search_flights("all flights")

        assert "Code: invalid_access_key" in result
        assert "Message: Bad key" in result

    def test_search_flights_reports_empty_results_for_route(self, monkeypatch):
        class EmptyResponse:
            def json(self):
                return {"data": []}

        monkeypatch.setattr(flight_tool, "API_KEY", "test-key")
        monkeypatch.setattr(
            flight_tool.requests,
            "get",
            lambda *args, **kwargs: EmptyResponse(),
        )

        result = flight_tool.search_flights("Flights from Toronto to London")

        assert "No live flight data found for route YYZ to LHR." in result
        assert "not ticket prices" in result
