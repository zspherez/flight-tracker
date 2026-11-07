"""Regression coverage for flight search and metropolitan airport groups."""

import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fli.models import Airline, Airport, FlightLeg, FlightResult
from fli.search.exceptions import SearchParseError

from app.models import SearchRequest
from app.rate_limit import limiter
from app.routers.search import router
from app.search import _run_search, _run_search_multi_airport


def flight(airline=Airline.UA):
    return FlightResult(
        legs=[
            FlightLeg(
                airline=airline,
                flight_number="123",
                departure_airport=Airport.EGE,
                arrival_airport=Airport.EWR,
                departure_datetime=datetime(2027, 2, 22, 9),
                arrival_datetime=datetime(2027, 2, 22, 15),
                duration=240,
            )
        ],
        price=355,
        currency="USD",
        duration=240,
        stops=0,
    )


class SearchTests(unittest.TestCase):
    @patch("app.search.SearchFlights")
    def test_city_search_expands_airports_and_preserves_results(self, search):
        search.return_value.search.return_value = [flight(), flight(Airline.NK)]
        results = _run_search(
            SearchRequest(origin=" ege ", destination="nyc", travel_date="2027-02-22")
        )
        filters = search.return_value.search.call_args.args[0]
        segment = filters.flight_segments[0]
        self.assertEqual(segment.departure_airport, [[Airport.EGE, 0]])
        self.assertEqual(
            segment.arrival_airport, [[Airport.JFK, 0], [Airport.LGA, 0], [Airport.EWR, 0]]
        )
        self.assertFalse(filters.exclude_basic_economy)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].destination, "EWR")
        self.assertEqual(results[0].price, 355)
        self.assertEqual(results[0].flight_codes, "UA123")

    @patch("app.search.SearchFlights")
    def test_no_results_returns_empty_list_for_both_search_paths(self, search):
        search.return_value.search.return_value = None
        self.assertEqual(
            _run_search(SearchRequest(origin="EGE", destination="JFK", travel_date="2027-02-22")),
            [],
        )
        self.assertEqual(
            _run_search_multi_airport(
                ["NYC"], ["EGE"], "2027-02-22", "ANY", "ECONOMY", None, None, False
            ),
            [],
        )
        segment = search.return_value.search.call_args.args[0].flight_segments[0]
        self.assertEqual(
            segment.departure_airport, [[Airport.JFK, 0], [Airport.LGA, 0], [Airport.EWR, 0]]
        )

    def test_upstream_error_remains_an_error(self):
        with patch("app.search.SearchFlights") as search:
            search.return_value.search.side_effect = SearchParseError("blocked page")
            with self.assertRaises(SearchParseError):
                _run_search(
                    SearchRequest(origin="EGE", destination="NYC", travel_date="2027-02-22")
                )


class SearchApiTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.state.limiter = limiter
        app.include_router(router)
        self.client = TestClient(app)
        self.params = {"origin": "EGE", "destination": "NYC", "travel_date": "2027-02-22"}

    def test_unknown_airport_is_validation_error_not_server_error(self):
        response = self.client.post("/api/search", json={**self.params, "destination": "ZZZ"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("Unknown airport or city code", response.text)

    def test_unsupported_basic_economy_filter_is_rejected(self):
        response = self.client.post(
            "/api/search", json={**self.params, "exclude_basic_economy": True}
        )
        self.assertEqual(response.status_code, 422)

    def test_upstream_failure_returns_useful_gateway_error(self):
        with patch(
            "app.routers.search.search_flights",
            new=AsyncMock(side_effect=SearchParseError("blocked page")),
        ):
            response = self.client.post("/api/search", json=self.params)
        self.assertEqual(response.status_code, 502)
        self.assertIn("Google Flights could not return results", response.json()["detail"])

    def test_empty_search_is_successful(self):
        with patch("app.routers.search.search_flights", new=AsyncMock(return_value=[])):
            response = self.client.post("/api/search", json=self.params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


if __name__ == "__main__":
    unittest.main()
