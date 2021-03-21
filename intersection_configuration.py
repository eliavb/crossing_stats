from common_types import Rectangle


IMAGE_BOUNDARIES = "CROP_IMAGE"
DETECTION_BOUNDARIES = "FOCUS_RECT"
COUNT_IN_AREA = "ABS_COUNT_POLY"
COUNT_IN_AREA_UNIQUE = "UNIQ_COUNT_POLY"


DS_TO_SPECIFIC_PARAMS = {
    "EXAMPLE_DATASET_CONFIGURATION": {
        IMAGE_BOUNDARIES:
            Rectangle(0, 100, 650, 800),
        DETECTION_BOUNDARIES: [(0, 100), (0, 290), (100, 520), (580, 415),
                               (15, 100)],
        COUNT_IN_AREA: [("queue_length_strait", [[0, 290], [90, 470],
                                                 [290, 420], [60, 230]], 0.7),
                        ("queue_length_left", [[60, 230], [290, 420],
                                               [510, 390], [130, 210]], 0.5)],
        COUNT_IN_AREA_UNIQUE: [("crossing_strait", [[115, 505], [110, 490],
                                                    [315, 445], [345,
                                                                 460]], 0.1),
                               ("crossing_left", [[320, 430], [350, 450],
                                                  [540, 420], [520,
                                                               405]], 0.1)],
    }
}
