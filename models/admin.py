import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, BaseModel, Field


class HeathStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class ComponentType(str, enum.Enum):
    COMPONENT = "component"
    DATASTORE = "datastore"
    SYSTEM = "system"


class ComponentDetails(BaseModel):
    component_id: Optional[str] = Field(None, alias="componentId")
    component_type: Optional[ComponentType] = Field(
        None, alias="componentType"
    )
    metric_value: Any = Field(None, alias="metricValue")
    metricUnit: Optional[str] = Field(None, alias="metricUnit")
    status: HeathStatus = HeathStatus.PASS
    time: datetime
    output: Optional[str]
    links: Optional[Dict[str, AnyUrl]] = None


class Health(BaseModel):
    status: HeathStatus = HeathStatus.PASS
    release_id: Optional[str] = Field(None, alias="releaseID")
    version: Optional[str] = None
    notes: Optional[List[str]] = None
    output: Optional[str] = None
    details: Optional[Dict[str, List[ComponentDetails]]] = None
    links: Optional[Dict[str, AnyUrl]] = None
    service_id: Optional[str] = Field(None, alias="serviceID")
    description: Optional[str] = None

    class Config:
        validate_assignment = True
        json_encoders = {
            datetime: lambda x: (
                x.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            )
        }
