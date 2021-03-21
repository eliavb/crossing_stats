from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
import utils


class Matcher(object):
  """Matches detected objects to existing ids."""

  def __init__(self):
    self.available_id = 0

  def create_new_tracker(self, frame, rect):
    return utils.create_tracker(frame, rect)

  def match(self, tracked_objects, new_rectangles, frame):
    """Matches tracked objects to detected objects.

    Args:
      tracked_objects: objects being tracked.
      new_rectangles: rectangles representing detected objects.
      frame: the frame that that the objects were detected from.

    Returns:
      Mapping from a unique object id to an object represeting the
        tracked object.
    """
    if not tracked_objects:
      object_by_id = {}
      for rect in new_rectangles:
        object_by_id[self.available_id] = self.create_new_tracker(frame, rect)
        self.available_id += 1
      return object_by_id

    if not new_rectangles:
      return {}

    tracked_ids = list(tracked_objects.keys())
    unmatched_tracked_ids = set(tracked_ids)

    tracked_objects_centers = [
        utils.get_rect_from_tracker(tracked_objects[k]).centroid_coords()
        for k in tracked_ids
    ]

    new_objects_centers = [rect.centroid_coords() for rect in new_rectangles]
    unmatched_new_objects = set(range(len(new_rectangles)))

    cost_matrix = cdist(tracked_objects_centers, new_objects_centers)
    rows, cols = linear_sum_assignment(cost_matrix)
    for row, col in zip(rows, cols):
      existing_id = tracked_ids[row]
      unmatched_tracked_ids.remove(existing_id)
      tracked_objects[existing_id] = self.create_new_tracker(
          frame, new_rectangles[col])
      unmatched_new_objects.remove(col)

    for unmatched_id in unmatched_tracked_ids:
      del tracked_objects[unmatched_id]

    for i in unmatched_new_objects:
      tracked_objects[self.available_id] = self.create_new_tracker(
          frame, new_rectangles[i])
      self.available_id += 1

    return tracked_objects
