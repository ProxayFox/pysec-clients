"""Microsoft Defender for Endpoint alerts endpoint models and client surface.

This module defines:
- `AlertsQuery`, `AlertCreateQuery`, and `AlertUpdateQuery` request models.
- `*Results` wrappers mapped to Arrow schemas for alerts and related entities.
- `AlertsEndpoint` methods for retrieving alerts and related domains, files,
  IPs, machines, and users.

Most endpoint methods return lazy `BaseResults` subclasses and defer HTTP
requests until a terminal materialization method is called. Create/update
operations are declared but currently marked as not implemented.

Note: Needs further Testing and implementation of POST methods for alert creation and updates.
"""

from datetime import datetime
from typing import Literal, Any

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import (
    ALERT_SCHEMA,
    DOMAIN_SCHEMA,
    FILE_SCHEMA,
    IP_SCHEMA,
    MACHINE_SCHEMA,
    USER_SCHEMA,
)


STATUS_TYPES = Literal["Unknown", "New", "InProgress", "Resolved"]
SEVERITY_TYPES = Literal["UnSpecified", "Informational", "Low", "Medium", "High"]
CLASIFICATION_TYPES = Literal["TruePositive", "Informational", "expected activity", "FalsePositive"]
CATAGORY_TYPES = Literal[
    "General", 
    "CommandAndControl", 
    "Collection", 
    "CredentialAccess", 
    "DefenseEvasion", 
    "Discovery", 
    "Exfiltration", 
    "Exploit", 
    "Execution", 
    "InitialAccess", 
    "LateralMovement", 
    "Malware", 
    "Persistence", 
    "PrivilegeEscalation", 
    "Ransomware", 
    "SuspiciousActivity"
]
DETERMINATION_TYPE = Literal[
    # True positive:
    "MultiStagedAttack",
    "MaliciousUserActivity",
    "CompromisedUser",
    "Malware",
    "Phishing",
    "UnwantedSoftware",
    # Informational, expected activity:
    "SecurityTesting",
    "LineOfBusinessApplication",
    "ConfirmedUserActivity",
    # False positive:
    "Clean",
    "InsufficientData",
    # Other:
    "Other"
    
    
]

class AlertsQuery(BaseQuery):
    """Query parameters for the /api/alerts endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
    ```python
        query = AlertsQuery(severity="Medium", pageSize=500)
        query = AlertsQuery(severity=["Medium", "High"], pageSize=500)
    ```
    """
    id: str | list[str] | None = None
    alertCreationTime: datetime | None = None
    lastUpdateTime: datetime | None = None
    incidentId: int | list[int] | None = None
    InvestigationId: int | list[int] | None = None
    assignedTo: str | list[str] | None = None
    detectionSource: str | list[str] | None = None
    lastEventTime: datetime | None = None
    status: STATUS_TYPES | list[STATUS_TYPES] | None = None
    severity: SEVERITY_TYPES | list[SEVERITY_TYPES] | None = None
    category: str | list[str] | None = None

class AlertCreateQuery(BaseQuery):
    """Query parameters for creating an alert by reference.

    All fields are required.

    Example:
    ```python
        query = AlertCreateQuery(referenceId="12345", referenceType="CustomReference")
    ```
    """
    eventTime: datetime
    reportId: str
    machineId: str
    severity: STATUS_TYPES
    title: str
    description: str
    recommendedAction: str
    category: CATAGORY_TYPES
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that the category is not 'Unknown' because alert creation does not allow 'Unknown' category."""
        if "Unknown" in self.category:
            raise ValueError("Category cannot be 'Unknown'. Please choose a valid category.")

class AlertUpdateQuery(BaseQuery):
    id: str | list[str]
    status: STATUS_TYPES
    assignedTo: str
    classification: CLASIFICATION_TYPES
    determination: DETERMINATION_TYPE
    comment: str

    def model_post_init(self, __context: Any) -> None:
        """Validate that the status is not 'UnSpecified' because alert update does not allow 'UnSpecified' status."""
        if "UnSpecified" in self.status:
            raise ValueError("Status cannot be 'UnSpecified'. Please choose a valid status.")

class AlertsResults(BaseResults):
    SCHEMA = ALERT_SCHEMA

class DomainResults(BaseResults):
    SCHEMA = DOMAIN_SCHEMA

class FileResults(BaseResults):
    SCHEMA = FILE_SCHEMA
    
class IPResults(BaseResults):
    SCHEMA = IP_SCHEMA

class MachineResults(BaseResults):
    SCHEMA = MACHINE_SCHEMA
    
class UserResults(BaseResults):
    SCHEMA = USER_SCHEMA

class AlertsEndpoint(BaseEndpoint):
    _PATH = "/api/alerts"
    
    def get_all(self, query: AlertsQuery | None = None) -> AlertsResults:
        """Get all alerts matching the query parameters."""
        params = query.to_odata_filters if query else {}
        return AlertsResults(self, params)
    
    def get(self, id: str) -> AlertsResults:
        """Get a single alert by ID."""
        path = f"{self._PATH}/{id}"
        return AlertsResults(self, {}, path=path, single=True)
    
    def domains(self, id: str) -> DomainResults:
        """Get the domains associated with an alert."""
        path = f"{self._PATH}/{id}/domains"
        return DomainResults(self, {}, path=path)
    
    def files(self, id: str) -> FileResults:
        """Get the files associated with an alert."""
        path = f"{self._PATH}/{id}/files"
        return FileResults(self, {}, path=path)
    
    def ips(self, id: str) -> IPResults:
        """Get the IPs associated with an alert."""
        path = f"{self._PATH}/{id}/ips"
        return IPResults(self, {}, path=path)
    
    def machines(self, id: str) -> MachineResults:
        """Get the machines associated with an alert."""
        path = f"{self._PATH}/{id}/machines"
        return MachineResults(self, {}, path=path)
    
    def user(self, id: str) -> UserResults:
        """Get the user associated with an alert."""
        path = f"{self._PATH}/{id}/user"
        return UserResults(self, {}, path=path)
    
    def createAlertByReference(self, referenceId: str, referenceType: str) -> AlertsResults:
        """Create alert

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/create-alert-by-reference
        
        TODO: implement this method. It requires a POST request with a JSON body, 
        which is a bit different from the other methods which are all GET requests with query parameters. 
        We may need to create a new method on the BaseEndpoint class to handle POST requests with JSON bodies.
        """
        path = f"{self._PATH}/CreateAlertByReference"
        raise NotImplementedError("This endpoint is not yet implemented. Please contact the maintainers if you need this functionality.")
    
    def batchUpdate(self, updates: list[dict]) -> None:
        """Batch update alerts

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/batch-update-alerts
        
        TODO: implement this method. It requires a POST request with a JSON body,
        which is a bit different from the other methods which are all GET requests with query parameters. 
        We may need to create a new method on the BaseEndpoint class to handle POST requests with JSON bodies.
        """
        path = f"{self._PATH}/batchUpdate"
        raise NotImplementedError("This endpoint is not yet implemented. Please contact the maintainers if you need this functionality.")
    
    def update(self, query: AlertUpdateQuery) -> None:
        """Update an alert's status and/or assigned user

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/update-alert
        
        TODO: implement this method. It requires a POST request with a JSON body,
        which is a bit different from the other methods which are all GET requests with query parameters. 
        We may need to create a new method on the BaseEndpoint class to handle POST requests with JSON bodies.
        """
        if isinstance(query.id, list):
            raise ValueError(
                "AlertUpdateQuery.id must be a single string, not a list, for the single update method.\n"
                "Use the batchUpdate method for updating multiple alerts at once."
            )
        
        path = f"{self._PATH}/{query.id}"
        raise NotImplementedError("This endpoint is not yet implemented. Please contact the maintainers if you need this functionality.")