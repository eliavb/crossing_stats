from shapely.geometry import Polygon
import utils


class AbsCounterTrackerPoly(object):
  """Absolute counter with repetition of tracked object that intersect with a polygon."""

  def __init__(self, name, polygon, min_intersection_ratio=0.7):
    self.name = name
    self.polygon = Polygon(polygon)
    self.num_object_seen = 0
    self.count_series = [0]
    self.min_intersection_ratio = min_intersection_ratio

  def get_frame_series(self):
    return self.count_series

  def get_counter(self):
    return self.count_series[-1]

  def update(self, rects):
    """Update counts with newly detected objects."""
    num_object_seen = 0
    for rect,_ in rects:
      if rect.compute_area() == 0:
        # Model outliers.
        continue
      poly = rect.to_shapely_polygon()
      intersection_ratio = poly.intersection(
          self.polygon).area / rect.compute_area()
      if intersection_ratio >= self.min_intersection_ratio:
        num_object_seen += 1
    self.count_series.append(num_object_seen)


class AbsCounterTrackerUniq(object):
  """Absolute counter without repetition of tracked object that intersect with a polygon."""

  def __init__(self, name, polygon, min_intersection_ratio):
    self.name = name
    self.polygon = Polygon(polygon)
    self.num_object_seen = 0
    self.count_series = [0]
    self.min_intersection_ratio = min_intersection_ratio
    self.counted_ids = set()

  def get_frame_series(self):
    return self.count_series

  def get_counter(self):
    return self.count_series[-1]

  def update(self, tracker_by_id):
    """Update counts with newly detected objects."""
    for id_, tracker in tracker_by_id.items():
      if self.name.split('_')[-1] != tracker[1]:
        continue
      if id_ in self.counted_ids:
        continue
      rect = utils.get_rect_from_tracker(tracker[0])
      if rect.compute_area() == 0:
        # Model outliers.
        continue
      center_point = rect.centroid_coords_point()
      poly = rect.to_shapely_polygon()
      intersection_ratio = poly.intersection(
          self.polygon).area / rect.compute_area()
      if self.polygon.contains(
          center_point) or intersection_ratio > self.min_intersection_ratio:
        
        self.num_object_seen += 1
        self.counted_ids.add(id_)
    self.count_series.append(self.num_object_seen)
