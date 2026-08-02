import pandas as pd
import pytest
from unittest import mock

import src.config as config
from src.wid_client import WidClient


def _fake_response(payload, status=200):
    resp = mock.Mock()
    resp.status_code = status
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    resp.text = "Forbidden"
    return resp


class TestWidClient:
    def test_url_built_from_config(self):
        client = WidClient()
        assert client.api_url == config.API_URL
        assert client.year_from == config.YEAR_FROM
        assert client.year_to == config.YEAR_TO

    def test_parse_response_returns_dataframe(self):
        payload = {
            "sptinc_p99p100_992_j": [
                {
                    "FR": {
                        "values": [
                            {"y": 1990, "v": 0.11, "dq": 4.0},
                            {"y": 2000, "v": 0.13, "dq": 4.0},
                        ]
                    }
                }
            ]
        }
        client = WidClient()
        df = client._parse_response("FR", "sptinc_p99p100_992_j", payload)
        assert isinstance(df, pd.DataFrame)
        assert "country" in df.columns
        assert "variable" in df.columns
        assert "year" in df.columns
        assert "value" in df.columns
        assert list(df["year"]) == [1990, 2000]
        assert list(df["value"]) == [0.11, 0.13]

    def test_parse_filters_outside_period(self):
        payload = {
            "sptinc_p99p100_992_j": [
                {
                    "FR": {
                        "values": [
                            {"y": 1980, "v": 0.10, "dq": 4.0},
                            {"y": 1995, "v": 0.12, "dq": 4.0},
                            {"y": 2030, "v": 0.20, "dq": 4.0},
                        ]
                    }
                }
            ]
        }
        client = WidClient()
        df = client._parse_response("FR", "sptinc_p99p100_992_j", payload)
        assert list(df["year"]) == [1995]

    def test_parse_skips_missing_values(self):
        payload = {
            "gptinc_p0p100_992_j": [
                {
                    "FR": {
                        "values": [
                            {"y": 1990, "v": 0.35, "dq": 4.0},
                            {"y": 1991, "v": None, "dq": 4.0},
                            {"y": 1992, "v": 0.36, "dq": 4.0},
                        ]
                    }
                }
            ]
        }
        client = WidClient()
        df = client._parse_response("FR", "gptinc_p0p100_992_j", payload)
        assert list(df["year"]) == [1990, 1992]

    def test_fetch_uses_cache_then_api(self, tmp_path, monkeypatch):
        payload = {
            "sptinc_p99p100_992_j": [
                {"FR": {"values": [{"y": 2000, "v": 0.12, "dq": 4.0}]}}
            ]
        }

        calls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            calls.append((url, params))
            return _fake_response(payload)

        client = WidClient(cache_dir=str(tmp_path))
        monkeypatch.setattr(client._session, "get", fake_get)

        df1 = client.fetch("FR", "sptinc_p99p100_992_j")
        df2 = client.fetch("FR", "sptinc_p99p100_992_j")

        assert len(df1) == 1
        assert len(df2) == 1
        assert len(calls) == 1, "второй запрос должен быть взят из кэша"

    def test_fetch_missing_key_raises(self, tmp_path, monkeypatch):
        client = WidClient(cache_dir=str(tmp_path))

        def fake_get(url, params=None, headers=None, timeout=None):
            return _fake_response({"message": "Forbidden"}, status=403)

        monkeypatch.setattr(client._session, "get", fake_get)
        with pytest.raises(RuntimeError, match="API"):
            client.fetch("FR", "sptinc_p99p100_992_j")

    def test_fetch_all_countries_and_variables(self, tmp_path, monkeypatch):
        def make_payload(variable):
            return {
                variable: [
                    {"US": {"values": [{"y": 2000, "v": 0.20, "dq": 4.0}]}}
                ]
            }

        calls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            calls.append((url, params["variables"]))
            return _fake_response(make_payload(params["variables"]))

        client = WidClient(cache_dir=str(tmp_path))
        monkeypatch.setattr(client._session, "get", fake_get)
        df = client.fetch_all()

        assert not df.empty
        assert len(calls) > 0
        assert {"country", "variable", "year", "value"} <= set(df.columns)
        # каждый вызов API кэшируется: повторный fetch_all не должен ходить в сеть
        n_calls = len(calls)
        df2 = client.fetch_all()
        assert len(calls) == n_calls, "повторный fetch_all должен использовать кэш"
        assert len(df2) >= len(df)
