from __future__ import annotations

from typing import Optional

from schemas.models import MaterialFeaturesInput
from schemas.request import JointInfo


class MaterialMapper:
    """Map material grades into tensile-strength feature values."""

    MATERIAL_TS_MAP: dict[str, float] = {
        "DP590": 590.0,
        "AL6061": 310.0,
        "SPCC": 270.0,
        "DP780": 780.0,
        "AL5052": 230.0,
    }

    def map_joint_info(self, joint_info: JointInfo) -> MaterialFeaturesInput:
        """Tool entry that delegates to temporary mock implementation."""

        return self.temporary(joint_info)

    def temporary(self, joint_info: JointInfo) -> MaterialFeaturesInput:
        """Temporary mock function to simulate material mapping output."""

        return MaterialFeaturesInput(
            Number_of_Joints=joint_info.Number_of_Joints,
            Material_1_ts=self._to_ts(joint_info.Material_1),
            Gauge_1=joint_info.Gauge_1,
            Material_2_ts=self._to_ts(joint_info.Material_2),
            Gauge_2=joint_info.Gauge_2,
            Material_3_ts=self._to_ts(joint_info.Material_3) if joint_info.Material_3 else None,
            Gauge_3=joint_info.Gauge_3,
        )

    def _to_ts(self, material: Optional[str]) -> float:
        if material is None:
            return 0.0
        return self.MATERIAL_TS_MAP.get(material, 400.0)
