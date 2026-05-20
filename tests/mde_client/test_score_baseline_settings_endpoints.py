"""Tests for ScoreEndpoint, BaselineConfigurationEndpoint, DataExportSettingsEndpoint."""

from __future__ import annotations

from mde_client.endpoints.machines import MachinesEndpoint
from mde_client.endpoints.score import ScoreEndpoint, ScoreResults
from mde_client.endpoints.securityBaseline import (
    BaselineConfigurationEndpoint,
    BaselineConfigurationResults,
)
from mde_client.endpoints.settings import (
    DataExportSettingsEndpoint,
    DataExportSettingsResults,
)


class TestScore:
    def test_get(self, make_endpoint) -> None:
        result = make_endpoint(ScoreEndpoint).get()
        assert isinstance(result, ScoreResults)
        assert result._path == "/api/exposureScore"
        assert result._single is True

    def test_by_machine_groups(self, make_endpoint) -> None:
        result = make_endpoint(ScoreEndpoint).byMachineGroups()
        assert result._path == "/api/exposureScore/ByMachineGroups"

    def test_configuration_score(self, make_endpoint) -> None:
        result = make_endpoint(ScoreEndpoint).configurationScore()
        assert result._path == "/api/configurationScore"

    def test_configuration_score_by_id(self, make_endpoint) -> None:
        result = make_endpoint(ScoreEndpoint).configurationScoreById("abc")
        assert result._path == "/api/configurationScore/abc"


class TestBaselineConfiguration:
    def test_profiles(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).profiles()
        assert isinstance(result, BaselineConfigurationResults)
        assert result._path == "/api/baselineProfiles"

    def test_profiles_by_id(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).profilesById("p-1")
        assert result._path == "/api/baselineProfiles/p-1"

    def test_active(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).active()
        assert result._path == "/api/baselineConfigurations"

    def test_active_by_id(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).activeById("c-1")
        assert result._path == "/api/baselineConfigurations/c-1"

    def test_exceptions(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).exceptions()
        assert result._path == "/api/baselineExceptions"

    def test_exceptions_by_id(self, make_endpoint) -> None:
        result = make_endpoint(BaselineConfigurationEndpoint).exceptionsById("e-1")
        assert result._path == "/api/baselineExceptions/e-1"

    def test_get_all_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_baselineComplianceAssessmentByMachine",
            lambda self: "sentinel",
        )
        assert make_endpoint(BaselineConfigurationEndpoint).get_all() == "sentinel"

    def test_get_all_files_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_baselineComplianceAssessmentExport",
            lambda self: "sentinel",
        )
        assert (
            make_endpoint(BaselineConfigurationEndpoint).get_all_files() == "sentinel"
        )

    def test_assessment_by_machine_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_secureConfigurationsAssessmentByMachine",
            lambda self: "sentinel",
        )
        assert (
            make_endpoint(BaselineConfigurationEndpoint).assessmentByMachine()
            == "sentinel"
        )

    def test_assessment_by_machine_files_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_secureConfigurationsAssessmentExport",
            lambda self: "sentinel",
        )
        assert (
            make_endpoint(BaselineConfigurationEndpoint).assessmentByMachineFiles()
            == "sentinel"
        )


class TestDataExportSettings:
    def test_returns_results(self, make_endpoint) -> None:
        result = make_endpoint(DataExportSettingsEndpoint).dataExportSettings()
        assert isinstance(result, DataExportSettingsResults)
        assert result._path == "/api/dataExportSettings"
