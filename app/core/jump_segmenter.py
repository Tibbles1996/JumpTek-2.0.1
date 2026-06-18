from __future__ import annotations

import numpy as np


LEFT_ANKLE_INDEX = 15
RIGHT_ANKLE_INDEX = 16


class JumpSegmenter:
    def __init__(self, height_threshold_m: float = 0.15) -> None:
        self.height_threshold_m = height_threshold_m

    @staticmethod
    def _feet_contact_bed(keypoints: np.ndarray, bed_mask: np.ndarray) -> bool:
        h, w = bed_mask.shape[:2]
        feet = [keypoints[LEFT_ANKLE_INDEX], keypoints[RIGHT_ANKLE_INDEX]]
        for foot in feet:
            x = int(np.clip(foot[0], 0, w - 1))
            y = int(np.clip(foot[1], 0, h - 1))
            if bed_mask[y, x] > 0:
                return True
        return False

    def segment(self, keypoints_per_frame: list[np.ndarray], heights_m: list[float], bed_mask: np.ndarray) -> list[dict[str, int]]:
        jumps: list[dict[str, int]] = []
        in_jump = False
        start_idx = 0

        for idx, (keypoints, height) in enumerate(zip(keypoints_per_frame, heights_m)):
            contact = self._feet_contact_bed(keypoints, bed_mask)
            airborne = (not contact) or (height > self.height_threshold_m)

            if airborne and not in_jump:
                in_jump = True
                start_idx = idx
            elif not airborne and in_jump:
                jumps.append({"start_frame": start_idx, "end_frame": idx})
                in_jump = False

        if in_jump:
            jumps.append({"start_frame": start_idx, "end_frame": len(keypoints_per_frame) - 1})

        return jumps
