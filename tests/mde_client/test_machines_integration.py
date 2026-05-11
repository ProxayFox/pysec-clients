"""Live integration tests for the MachinesEndpoint.

Compare client responses against direct API responses to verify
end-to-end correctness.  These tests require Azure credentials and a
real Defender for Endpoint environment; they are skipped automatically
when the required environment variables are absent.

Run with::

    pytest tests/mde_client/test_machines_integration.py -v

Required environment variables:

    AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET,
    MDE_MACHINE_ID, MDE_MACHINE_TAG
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from mde_client import MDEClient
from mde_client.endpoints.machines import MachinesQuery

# ------------------------------------------------------------------
# Module-level skip when credentials are missing
# ------------------------------------------------------------------

_REQUIRED_ENV = (
    "AZURE_TENANT_ID",
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET",
    "MDE_MACHINE_ID",
    "MDE_MACHINE_TAG",
)
_missing = [v for v in _REQUIRED_ENV if not os.environ.get(v)]

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        bool(_missing),
        reason=f"Missing env vars: {', '.join(_missing)}",
    ),
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _assert_response_matches(
    client_record: dict,
    direct_record: dict,
    context: str = "",
) -> None:
    """Assert that every key in the direct API response exists and matches
    in the client response.

    Mirrors the ``validate()`` function from ``build/test.py``.
    """
    direct_record.pop("@odata.context", None)

    for key, expected in direct_record.items():
        assert key in client_record, (
            f"{context}: key '{key}' from direct API missing in client response"
            f"\nDirect keys:  {json.dumps(sorted(direct_record.keys()), indent=2)}"
            f"\nClient keys:  {json.dumps(sorted(client_record.keys()), indent=2)}"
        )
        actual = client_record[key]

        # Timestamp coercion: client returns datetime, API returns ISO string
        if isinstance(actual, datetime) and isinstance(expected, str):
            expected_dt = datetime.fromisoformat(expected.replace("Z", "+00:00"))
            assert actual == expected_dt, (
                f"{context}: timestamp mismatch for '{key}': {actual!r} vs {expected!r}"
            )
        else:
            assert actual == expected, (
                f"{context}: mismatch for '{key}': {actual!r} vs {expected!r}"
            )


def _check_forbidden(response_json: dict) -> str | None:
    """Return a skip reason if the API returned Forbidden, else None.

    Raises for any non-Forbidden error so genuine failures surface.
    """
    error = response_json.get("error")
    if error and error.get("code") == "Forbidden":
        return f"Forbidden: {error.get('message', 'insufficient permissions')}"
    if error:
        raise RuntimeError(f"API error: {error}")
    return None


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture(scope="module")
def mde_client():
    """Module-scoped MDEClient constructed from environment variables."""
    client = MDEClient(
        tenant_id=os.environ["AZURE_TENANT_ID"],
        client_id=os.environ["AZURE_CLIENT_ID"],
        client_secret=os.environ["AZURE_CLIENT_SECRET"],
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
def machine_id() -> str:
    return os.environ["MDE_MACHINE_ID"]


@pytest.fixture(scope="module")
def machine_tag() -> str:
    return os.environ["MDE_MACHINE_TAG"]


@pytest.fixture(scope="module")
def all_machines(mde_client: MDEClient):
    """Bootstrap: fetch a page of machines for IP discovery."""
    query = MachinesQuery(top=512)
    return mde_client.machines.get_all(query).to_polars()


@pytest.fixture(scope="module")
def machine_ip_and_timestamp(mde_client: MDEClient, all_machines):
    """Find the first IPv4 address that returns results from ``findbyip``."""
    import polars as pl

    timestamp_dt = datetime.now(timezone.utc) - timedelta(days=29.5)
    timestamp_str = timestamp_dt.isoformat().replace("+00:00", "Z")

    ip_list: list[str] = (
        all_machines.select(pl.col("ipAddresses"))
        .explode("ipAddresses")
        .select(pl.col("ipAddresses").struct.field("ipAddress").alias("ipAddress"))
        .drop_nulls()
        .get_column("ipAddress")
        .cast(pl.String)
        .unique()
        .to_list()
    )

    for ip in ip_list:
        if ":" in ip:  # skip IPv6
            continue
        resp = mde_client.misc._request(
            "GET",
            f"/api/machines/findbyip(ip='{ip}',timestamp={timestamp_str})",
        ).json()
        if resp.get("value") and len(resp["value"]) > 0:
            return ip, timestamp_dt, resp["value"][0]

    pytest.skip("No suitable IPv4 address found for findbyip test")


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestMachineDetails:
    def test_get_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        direct = mde_client.misc._request("GET", f"/api/machines/{machine_id}").json()
        reason = _check_forbidden(direct)
        if reason:
            pytest.skip(reason)

        client_record = mde_client.machines.get(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="machine details")


class TestLogonUsers:
    def test_logonusers_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/logonusers"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No logon users returned for this machine")

        direct = resp["value"][0]
        client_record = mde_client.machines.logonusers(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="logon users")


class TestAlerts:
    def test_alerts_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/alerts"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No alerts returned for this machine")

        direct = resp["value"][0]
        client_record = mde_client.machines.alerts(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="alerts")


class TestSoftware:
    def test_software_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/software"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No software returned for this machine")

        direct = resp["value"][0]
        client_record = mde_client.machines.software(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="software")


class TestVulnerabilities:
    def test_vulnerabilities_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/vulnerabilities"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No vulnerabilities returned for this machine")

        direct = resp["value"][0]
        direct.pop("@odata.type", None)
        client_record = mde_client.machines.vulnerabilities(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="vulnerabilities")


class TestRecommendations:
    def test_recommendations_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/recommendations"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No recommendations returned for this machine")

        direct = resp["value"][0]
        client_record = mde_client.machines.recommendations(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="recommendations")


class TestMissingKBs:
    def test_missing_kbs_matches_direct_api(
        self, mde_client: MDEClient, machine_id: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET", f"/api/machines/{machine_id}/getmissingkbs"
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No missing KBs returned for this machine")

        direct = resp["value"][0]
        client_record = mde_client.machines.getmissingkbs(machine_id).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="missing KBs")


class TestFindByIP:
    def test_findbyip_matches_direct_api(
        self,
        mde_client: MDEClient,
        machine_ip_and_timestamp: tuple[str, datetime, dict],
    ) -> None:
        ip, timestamp_dt, direct = machine_ip_and_timestamp
        client_record = mde_client.machines.findbyip(ip, timestamp_dt).to_dicts()[0]
        _assert_response_matches(client_record, direct, context=f"findbyip ({ip})")


class TestMachineTags:
    def test_tag_matches_direct_api(
        self, mde_client: MDEClient, machine_tag: str
    ) -> None:
        resp = mde_client.misc._request(
            "GET",
            f"/api/machines/findbytag?tag={machine_tag}&useStartsWithFilter=true",
        ).json()
        reason = _check_forbidden(resp)
        if reason:
            pytest.skip(reason)
        if not resp.get("value"):
            pytest.skip("No machines found for this tag")

        direct = resp["value"][0]
        client_record = mde_client.machines.tag(
            machine_tag, useStartsWithFilter=True
        ).to_dicts()[0]
        _assert_response_matches(client_record, direct, context="machine tags")
