import logging
import datetime

from pprint import pprint
from typing import Dict, Any, List, Tuple
from enum import Enum

from .network import Feature

logger = logging.getLogger(__name__)


class PropMergeOp(str, Enum):
    """
    Enum defining which operation should be applied to property values when two features
    are merged.
    """

    KEEP_OR_COPY = "KEEP_OR_COPY"  # Keep Primary or Copy Secondary if no Primary value
    SUM_NUMBER = "SUM_NUMBER"  # Add two numbers together
    MERGE_ARRAY = "MERGE_ARRAY"  # Concat and deduplicate arrays of values
    CONCAT_ARRAY = "CONCAT_ARRAY"  # Concat arrays of values
    CONCAT_DESCRIPTION = "CONCAT_DESCRIPTION"  # Join strings with a comma


NODES_PROPERTIES_MERGE_CONFIG = [
    ("name", PropMergeOp.KEEP_OR_COPY),
    ("location", PropMergeOp.KEEP_OR_COPY),
    ("address", PropMergeOp.KEEP_OR_COPY),
    ("accessPoint", PropMergeOp.KEEP_OR_COPY),
    ("power", PropMergeOp.KEEP_OR_COPY),
    ("physicalInfrastructureProvider", PropMergeOp.KEEP_OR_COPY),
    ("type", PropMergeOp.MERGE_ARRAY),
    ("internationalConnections", PropMergeOp.CONCAT_ARRAY),
    ("technologies", PropMergeOp.CONCAT_ARRAY),
    ("networkProviders", PropMergeOp.CONCAT_ARRAY),
]


SPANS_PROPERTIES_MERGE_CONFIG = [
    ("name", PropMergeOp.KEEP_OR_COPY),
    ("phase", PropMergeOp.KEEP_OR_COPY),
    ("status", PropMergeOp.KEEP_OR_COPY),
    ("readyForServiceDate", PropMergeOp.KEEP_OR_COPY),
    ("physicalInfrastructureProvider", PropMergeOp.KEEP_OR_COPY),
    ("supplier", PropMergeOp.KEEP_OR_COPY),
    ("deploymentDetails", PropMergeOp.KEEP_OR_COPY),
    ("darkFibre", PropMergeOp.KEEP_OR_COPY),
    ("fibreType", PropMergeOp.KEEP_OR_COPY),
    ("fibreTypeDetails/fibreSubType", PropMergeOp.KEEP_OR_COPY),
    ("fibreCount", PropMergeOp.KEEP_OR_COPY),
    ("capacityDetails", PropMergeOp.KEEP_OR_COPY),
    ("transmissionMedium", PropMergeOp.MERGE_ARRAY),
    ("deployment", PropMergeOp.MERGE_ARRAY),
    ("countries", PropMergeOp.MERGE_ARRAY),
    ("capacity", PropMergeOp.SUM_NUMBER),
    ("networkProviders", PropMergeOp.CONCAT_ARRAY),
    ("deploymentDetails", PropMergeOp.KEEP_OR_COPY),
    ("deploymentDetails/description", PropMergeOp.CONCAT_DESCRIPTION),
    ("capacityDetails", PropMergeOp.KEEP_OR_COPY),
    ("capacityDetails/description", PropMergeOp.CONCAT_DESCRIPTION),
    ("fibreTypeDetails", PropMergeOp.KEEP_OR_COPY),
    ("fibreTypeDetails/description", PropMergeOp.CONCAT_DESCRIPTION),
]


def get_prop(props: Dict[str, Any], k: str) -> Any:
    """Helper function to get nested properties using slash notation"""
    if "/" in k:
        k_parts = k.split("/")
        return get_prop(props.get(k_parts[0]) or {}, "/".join(k_parts[1:]))
    else:
        return props.get(k)


def set_prop(props: Dict[str, Any], k: str, v: Any) -> Dict[str, Any]:
    """Helper function to set nested properties using slash notation"""
    if "/" in k:
        k_parts = k.split("/")
        props[k_parts[0]] = set_prop(
            props.get(k_parts[0]) or {}, "/".join(k_parts[1:]), v
        )
    else:
        props[k] = v

    return props


def merge_features_properties(
    props_config: List[Tuple[str, PropMergeOp]], primary: Feature, secondary: Feature
) -> Dict[str, Any]:
    props = primary.properties.copy()

    for k, op in props_config:
        prop_a = get_prop(primary.properties, k)
        prop_b = get_prop(secondary.properties, k)

        # Copy over properties that exist in B but not A
        if op == PropMergeOp.KEEP_OR_COPY:
            if prop_a:
                set_prop(props, k, prop_a)
            elif prop_b:
                set_prop(props, k, prop_b)

        # Concat array properties
        elif op == PropMergeOp.CONCAT_ARRAY:
            new_array = list()
            new_array.extend(prop_a or [])
            new_array.extend(prop_b or [])
            set_prop(props, k, new_array)

        # Merge array properties
        elif op == PropMergeOp.MERGE_ARRAY:
            new_array = list(set().union(prop_a or []).union(prop_b or []))
            set_prop(props, k, new_array)

        # Sum properties
        elif op == PropMergeOp.SUM_NUMBER:
            if prop_a is not None or prop_b is not None:
                set_prop(props, k, (prop_a or 0) + (prop_b or 0))

        # Concat (with a comma) string properties
        elif op == PropMergeOp.CONCAT_DESCRIPTION:
            if prop_a is not None and prop_b is not None:
                # Go via set to remove duplicate strings
                strs = list(set([s for s in [prop_a, prop_b] if s]))
                set_prop(props, k, ", ".join(strs))

        else:
            raise Exception(f"Unknown PropMergeOp {op}")

    pprint(props)

    return props


def generate_provenance_data(consolidation_reason):
    """
    Additional metadata about the origin of a consolidated feature.
    Property names are in line with PROV-O vocab where applicable, and
    use camelCase to serialise directly to JSON.
    """
    primary_id = consolidation_reason.primary.get("id")
    secondary_id = consolidation_reason.secondary.get("id")
    prov = {
        "wasDerivedFrom": [primary_id, secondary_id], # TODO: include filenames here
        "generatedAtTime": datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(),
        "confidence": consolidation_reason.confidence,
        "similarFields": consolidation_reason.similar_fields,
        "manual": consolidation_reason.manual,
    }

    return prov