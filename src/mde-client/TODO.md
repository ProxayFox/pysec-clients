# MDE Client — Endpoint Coverage TODO

> Auto-generated gap analysis comparing `build/mde_metadata.xml` against `src/mde_client/endpoints/`
> Generated: 2026-05-13

Assumptions: EntitySets are counted as separate collection/item GET operations; private endpoint helpers that issue real requests count as implemented; duplicate EntitySets are preserved as separate contract rows.

## Summary

- Total operations in metadata contract: 125
- Currently implemented: 125
- Partially implemented: 1
- Missing: 0
- Coverage: 100.0%
- Validated endpoints: 67 probed, 27 confirmed valid, 13 phantom (404/405)

## Missing Endpoints

> API Status column from live validation: ✓ = confirmed (200/403), ✗ = phantom (404/405), ? = not probed

## Partially Implemented

| Endpoint File | Missing Operations | Notes |
|---------------|-------------------|-------|
| src/mde_client/endpoints/deviceGroups.py | See notes | TODO: Needs Testing and Validation |

## Already Covered (Reference)

<details>
<summary>Click to expand full coverage list</summary>

| Operation | Implemented In | Status |
|-----------|---------------|--------|
| AddDeviceGroups | src/mde_client/endpoints/deviceGroups.py::DeviceGroupsEndpoint.add | ✅ |
| AddOrRemoveTagForMultipleMachines | src/mde_client/endpoints/machines.py::MachinesEndpoint.addOrRemoveTagForMultipleMachines | ✅ |
| Alerts | src/mde_client/endpoints/machines.py::MachinesEndpoint.alerts | ✅ |
| Alerts collection | src/mde_client/endpoints/alerts.py::AlertsEndpoint.get_all | ✅ |
| Alerts item | src/mde_client/endpoints/alerts.py::AlertsEndpoint.get | ✅ |
| Alerts.files | src/mde_client/endpoints/alerts.py::AlertsEndpoint.files | ✅ |
| Alerts.iPs | src/mde_client/endpoints/alerts.py::AlertsEndpoint.ips | ✅ |
| Alerts.machine | src/mde_client/endpoints/alerts.py::AlertsEndpoint.machines | ✅ |
| Alerts.user | src/mde_client/endpoints/alerts.py::AlertsEndpoint.user | ✅ |
| AvailableMachineActions | src/mde_client/endpoints/machines.py::MachinesEndpoint._availableMachineActions | ✅ |
| BaselineComplianceAssessmentByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._baselineComplianceAssessmentByMachine | ✅ |
| BaselineComplianceAssessmentExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._baselineComplianceAssessmentExport | ✅ |
| BaselineConfigurations collection | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.active | ✅ |
| BaselineConfigurations item | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.activeById | ✅ |
| BaselineExceptions collection | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.exceptions | ✅ |
| BaselineExceptions item | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.exceptionsById | ✅ |
| BaselineProfiles collection | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.profiles | ✅ |
| BaselineProfiles item | src/mde_client/endpoints/securityBaseline.py::BaselineConfigurationEndpoint.profilesById | ✅ |
| BatchDelete | src/mde_client/endpoints/authenticatedScan.py::AuthenticatedDefinitionsEndpoint.delete | ✅ |
| BatchDelete | src/mde_client/endpoints/indicators.py::IndicatorsEndpoint.batch_delete | ✅ |
| BatchUpdate | src/mde_client/endpoints/alerts.py::AlertsEndpoint.batchUpdate | ✅ |
| BatchUpdate | src/mde_client/endpoints/indicators.py::IndicatorsEndpoint.batch_update | ✅ |
| BigPageSize | src/mde_client/endpoints/machines.py::MachinesEndpoint.bigPageSize | ✅ |
| BrowserExtensionsInventoryByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._browserExtensionsInventoryByMachine | ✅ |
| BrowserExtensionsInventoryExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._browserextensionsinventoryExport | ✅ |
| ByMachineGroups | src/mde_client/endpoints/score.py::ScoreEndpoint.byMachineGroups | ✅ |
| CertificateAssessmentByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._certificateAssessmentByMachine | ✅ |
| CertificateAssessmentExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._certificateAssessmentExport | ✅ |
| CollectInvestigationPackage | src/mde_client/endpoints/machines.py::MachinesEndpoint._collectInvestigationPackage | ✅ |
| ConfigurationScore collection | src/mde_client/endpoints/score.py::ScoreEndpoint.configurationScore | ✅ |
| ConfigurationScore item | src/mde_client/endpoints/score.py::ScoreEndpoint.configurationScoreById | ✅ |
| CreateAlertByReference | src/mde_client/endpoints/alerts.py::AlertsEndpoint.createAlertByReference | ✅ |
| DataExportSettings collection | src/mde_client/endpoints/settings.py::DataExportSettingsEndpoint.dataExportSettings | ✅ |
| DeleteDeviceGroups | src/mde_client/endpoints/deviceGroups.py::DeviceGroupsEndpoint.delete | ✅ |
| DeviceAuthenticatedScanAgents collection | src/mde_client/endpoints/authenticatedScan.py::DeviceAuthenticatedAgentsEndpoint.get_all | ✅ |
| DeviceAuthenticatedScanAgents item | src/mde_client/endpoints/authenticatedScan.py::DeviceAuthenticatedAgentsEndpoint.get | ✅ |
| DeviceAuthenticatedScanDefinitions collection | src/mde_client/endpoints/authenticatedScan.py::AuthenticatedDefinitionsEndpoint.get_all | ✅ |
| DeviceAuthenticatedScanDefinitions item | src/mde_client/endpoints/authenticatedScan.py::AuthenticatedDefinitionsEndpoint.get | ✅ |
| DeviceAvInfo collection | src/mde_client/endpoints/deviceAvHealth.py::DeviceAVHealthEndpoint.get_all | ✅ |
| DeviceGroups collection | src/mde_client/endpoints/deviceGroups.py::DeviceGroupsEndpoint.get_all | ✅ |
| DeviceGroups item | src/mde_client/endpoints/deviceGroups.py::DeviceGroupsEndpoint.get | ✅ |
| Distributions | src/mde_client/endpoints/software.py::SoftwareEndpoint.distributions | ✅ |
| Dlp | src/mde_client/endpoints/machines.py::MachinesEndpoint.dlp | ✅ |
| Domains | src/mde_client/endpoints/alerts.py::AlertsEndpoint.domains | ✅ |
| ExposureScore collection | src/mde_client/endpoints/score.py::ScoreEndpoint.get | ✅ |
| Files | src/mde_client/endpoints/alerts.py::AlertsEndpoint.files | ✅ |
| FindByIp | src/mde_client/endpoints/machines.py::MachinesEndpoint.findbyip | ✅ |
| FindByTag | src/mde_client/endpoints/machines.py::MachinesEndpoint.findbytag | ✅ |
| Firmware | src/mde_client/endpoints/machines.py::MachinesEndpoint._deviceFirmware | ✅ |
| Firmware collection | src/mde_client/endpoints/firmware.py::FirmwareEndpoint.get_all | ✅ |
| GetMissingKbs | src/mde_client/endpoints/machines.py::MachinesEndpoint.getmissingkbs | ✅ |
| GetMissingKbs | src/mde_client/endpoints/software.py::SoftwareEndpoint.getmissingkbs | ✅ |
| GetScanHistoryByScanDefinitionId | src/mde_client/endpoints/authenticatedScan.py::AuthenticatedDefinitionsEndpoint.definition_history | ✅ |
| GetScanHistoryBySessionId | src/mde_client/endpoints/authenticatedScan.py::AuthenticatedDefinitionsEndpoint.session_history | ✅ |
| HardwareFirmwareInventoryByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._firmwareInventoryByMachine | ✅ |
| HardwareFirmwareInventoryExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._firmwareInventoryByMachineFiles | ✅ |
| IPs | src/mde_client/endpoints/alerts.py::AlertsEndpoint.ips | ✅ |
| Import | src/mde_client/endpoints/indicators.py::IndicatorsEndpoint.batch_import | ✅ |
| Incidents collection | src/mde_client/endpoints/incidents.py::IncidentsEndpoint.get_all | ✅ |
| Incidents item | src/mde_client/endpoints/incidents.py::IncidentsEndpoint.get | ✅ |
| Indicators collection | src/mde_client/endpoints/indicators.py::IndicatorsEndpoint.get_all | ✅ |
| Indicators item | src/mde_client/endpoints/indicators.py::IndicatorsEndpoint.get | ✅ |
| InfoGatheringExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._infoGatheringExport | ✅ |
| InitiateInvestigation | src/mde_client/endpoints/machines.py::MachinesEndpoint._initiateInvestigation | ✅ |
| Investigations collection | src/mde_client/endpoints/investigations.py::InvestigationsEndpoint.get_all | ✅ |
| Investigations item | src/mde_client/endpoints/investigations.py::InvestigationsEndpoint.get | ✅ |
| Isolate | src/mde_client/endpoints/machines.py::MachinesEndpoint._isolate | ✅ |
| LatestMachineActions | src/mde_client/endpoints/machines.py::MachinesEndpoint._latestMachineActions | ✅ |
| LibraryFiles collection | src/mde_client/endpoints/library.py::LibraryFilesEndpoint.get_all | ✅ |
| LogOnUsers | src/mde_client/endpoints/machines.py::MachinesEndpoint.logonusers | ✅ |
| LogsCollection | src/mde_client/endpoints/machines.py::MachinesEndpoint.logsCollection | ✅ |
| Machine | src/mde_client/endpoints/alerts.py::AlertsEndpoint.machines | ✅ |
| MachineActions | src/mde_client/endpoints/machines.py::MachinesEndpoint._getMachineActions | ✅ |
| MachineReferences | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.machineReferences | ✅ |
| MachineReferences | src/mde_client/endpoints/remediations.py::RemediationEndpoint.machinereferences | ✅ |
| MachineReferences | src/mde_client/endpoints/software.py::SoftwareEndpoint.machineReferences | ✅ |
| MachineReferences | src/mde_client/endpoints/vulnerabilities.py::VulnerabilityEndpoint.machineReferences | ✅ |
| Machines collection | src/mde_client/endpoints/machines.py::MachinesEndpoint.get_all | ✅ |
| Machines item | src/mde_client/endpoints/machines.py::MachinesEndpoint.get | ✅ |
| Machines.logOnUsers | src/mde_client/endpoints/machines.py::MachinesEndpoint.logonusers | ✅ |
| Machines.recommendations | src/mde_client/endpoints/machines.py::MachinesEndpoint.recommendations | ✅ |
| Machines.software | src/mde_client/endpoints/machines.py::MachinesEndpoint.software | ✅ |
| Machines.vulnerabilities | src/mde_client/endpoints/machines.py::MachinesEndpoint.vulnerabilities | ✅ |
| MachinesVulnerabilities | src/mde_client/endpoints/vulnerabilities.py::VulnerabilityEndpoint.machinesVulnerabilities | ✅ |
| OffBoard | src/mde_client/endpoints/machines.py::MachinesEndpoint._offBoard | ✅ |
| PostDeviceGroups | src/mde_client/endpoints/deviceGroups.py::DeviceGroupsEndpoint.post | ✅ |
| Recommendations | src/mde_client/endpoints/machines.py::MachinesEndpoint.recommendations | ✅ |
| Recommendations collection | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.get_all | ✅ |
| Recommendations item | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.get | ✅ |
| Recommendations.software | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.software | ✅ |
| Recommendations.vulnerabilities | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.vulnerabilities | ✅ |
| RemediationTasks collection | src/mde_client/endpoints/remediations.py::RemediationEndpoint.get_all | ✅ |
| RemediationTasks item | src/mde_client/endpoints/remediations.py::RemediationEndpoint.get | ✅ |
| RestrictCodeExecution | src/mde_client/endpoints/machines.py::MachinesEndpoint._restrictCodeExecution | ✅ |
| RunAntiVirusScan | src/mde_client/endpoints/machines.py::MachinesEndpoint._runAntiVirusScan | ✅ |
| RunCustomPlaybook | src/mde_client/endpoints/machines.py::MachinesEndpoint.runCustomPlaybook | ✅ |
| RunLiveResponse | src/mde_client/endpoints/machines.py::MachinesEndpoint._runLiveResponse | ✅ |
| SecureConfigurationsAssessmentByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._secureConfigurationsAssessmentByMachine | ✅ |
| SecureConfigurationsAssessmentExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._secureConfigurationsAssessmentExport | ✅ |
| SetDeviceValue | src/mde_client/endpoints/machines.py::MachinesEndpoint.setDeviceValue | ✅ |
| SetExclusion | src/mde_client/endpoints/machines.py::MachinesEndpoint.setExclusion | ✅ |
| Software | src/mde_client/endpoints/machines.py::MachinesEndpoint.software | ✅ |
| Software | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.software | ✅ |
| Software collection | src/mde_client/endpoints/software.py::SoftwareEndpoint.get_all | ✅ |
| Software item | src/mde_client/endpoints/software.py::SoftwareEndpoint.get | ✅ |
| Software.vulnerabilities | src/mde_client/endpoints/software.py::SoftwareEndpoint.vulnerabilities | ✅ |
| SoftwareInventoryByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareInventoryByMachine | ✅ |
| SoftwareInventoryExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareInventoryExport | ✅ |
| SoftwareInventoryNoProductCodeByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareInventoryNoProductCodeByMachine | ✅ |
| SoftwareInventoryNonCpeExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareInventoryNonCpeExport | ✅ |
| SoftwareVulnerabilitiesByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareVulnerabilitiesByMachine | ✅ |
| SoftwareVulnerabilitiesExport | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareVulnerabilitiesExport | ✅ |
| SoftwareVulnerabilityChangesByMachine | src/mde_client/endpoints/machines.py::MachinesEndpoint._softwareVulnerabilityChangesByMachine | ✅ |
| StartInvestigation | src/mde_client/endpoints/machines.py::MachinesEndpoint._startInvestigation | ✅ |
| StopAndQuarantineFile | src/mde_client/endpoints/machines.py::MachinesEndpoint._stopAndQuarantineFile | ✅ |
| Tags | src/mde_client/endpoints/machines.py::MachinesEndpoint.tags | ✅ |
| UnTaggedMachines | src/mde_client/endpoints/machines.py::MachinesEndpoint.unTaggedMachines | ✅ |
| Unisolate | src/mde_client/endpoints/machines.py::MachinesEndpoint._unisolate | ✅ |
| UnrestrictCodeExecution | src/mde_client/endpoints/machines.py::MachinesEndpoint._unrestrictCodeExecution | ✅ |
| User | src/mde_client/endpoints/alerts.py::AlertsEndpoint.user | ✅ |
| Vulnerabilities | src/mde_client/endpoints/machines.py::MachinesEndpoint.vulnerabilities | ✅ |
| Vulnerabilities | src/mde_client/endpoints/recommendations.py::RecommendationsEndpoint.vulnerabilities | ✅ |
| Vulnerabilities | src/mde_client/endpoints/software.py::SoftwareEndpoint.vulnerabilities | ✅ |
| Vulnerabilities collection | src/mde_client/endpoints/vulnerabilities.py::VulnerabilityEndpoint.get_all | ✅ |
| Vulnerabilities item | src/mde_client/endpoints/vulnerabilities.py::VulnerabilityEndpoint.get | ✅ |

</details>

## Singletons

- None present in `build/mde_metadata.xml`.
