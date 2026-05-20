from __future__ import annotations

from datetime import datetime

from .base import BaseEndpoint, BaseQuery, BaseResults
from .machines import MachineReferencesResults
from ..schemas import REMEDIATION_TASK_SCHEMA
from ..models.enums import TASK_STATE_VALUE_TYPE_DTO


class RemediationQuery(BaseQuery):
    """Query parameters for the /api/remediationtasks endpoint."""

    createdon: datetime | None
    status: TASK_STATE_VALUE_TYPE_DTO | list[TASK_STATE_VALUE_TYPE_DTO] | None


class RemediationResults(BaseResults):
    """Results from the /api/remediationtasks endpoint."""

    SCHEMA = REMEDIATION_TASK_SCHEMA


class RemediationEndpoint(BaseEndpoint):
    """Endpoint for /api/remediationtasks."""

    _PATH = "/api/remediationtasks"

    def get_all(self, query: RemediationQuery | None = None) -> RemediationResults:
        """Get remediation tasks

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-remediation-tasks
        """
        params = query.to_odata_filters if query else {}
        return RemediationResults(self, params)

    def get(self, id: str) -> RemediationResults:
        """Get remediation task by ID

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-remediation-task
        """
        path = f"{self._PATH}/{id}"
        return RemediationResults(self, {}, path=path)

    def machinereferences(self, id: str) -> MachineReferencesResults:
        """Get machine references for a remediation task

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machinereferences-remediationtask
        """
        path = f"{self._PATH}/{id}/machinereferences"
        return MachineReferencesResults(self, {}, path=path)
