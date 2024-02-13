from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class OFDSIdentifier:
    id: Optional[str]
    scheme: Optional[str]
    legalName: Optional[str]
    uri: Optional[str]


@dataclass
class OFDSAddress:
    streetAddress: Optional[str]
    locality: Optional[str]
    region: Optional[str]
    postalCode: Optional[str]
    country: Optional[str]


@dataclass
class OFDSOrganisation:
    id: str
    name: Optional[str]
    identifier: Optional[OFDSIdentifier]
    country: Optional[str]


@dataclass
class OFDSNetworkInfo:
    fid: int
    id: str
    name: str
    website: str


@dataclass
class OFDSNetworkProviderInfo:
    country: str
    id: str
    identifier: Dict[str, Any]
    name: str
    website: str


@dataclass
class OFDSPhaseInfo:
    description: str
    id: str
    name: str


@dataclass
class OFDSPhysicalInfrastructureProviderInfo:
    country: str
    id: str
    identifier: Dict[str, Any]
    name: str
    website: str


@dataclass
class OFDSNode:
    id: str
    name: Optional[str]
    phase: Optional[OFDSPhaseInfo]
    status: Optional[str]
    address: Optional[OFDSAddress]
    type: Optional[List[str]]
    accessPoint: Optional[bool]
    internationalConnections: Optional[List[OFDSAddress]]
    power: Optional[bool]
    technologies: Optional[List[str]]

    network: OFDSNetworkInfo
    networkProviders: List[OFDSNetworkProviderInfo]
    physicalInfrastructureProvider: OFDSPhysicalInfrastructureProviderInfo
