from shapely.geometry import Point
from shapely.geometry import Polygon


def get_intersection_range(a0, a1, b0, b1):
  """Gets the intersection between [a0, a1] and [b0, b1]."""
  assert a0 <= a1
  assert b0 <= b1
  start_x = 0
  end_x = 0
  # Contains
  if a0 >= b0 and a1 <= b1:
    start_x = a0
    end_x = a1
    # Contains
  elif a0 < b0 and b1 < a1:
    start_x = b0
    end_x = b1
  elif a0 < b0 and a1 > b0:
    start_x = b0
    end_x = a1
  elif a1 > b1 and a0 < b1:
    start_x = a0
    end_x = b1
  else:
    pass
  return start_x, end_x


class Rectangle(object):
  """Rectangle object."""

  def __init__(self, start_x, start_y, end_x, end_y):
    self.start_x = max(start_x, 0)
    self.start_y = max(start_y, 0)
    self.end_x = max(end_x, 0)
    self.end_y = max(end_y, 0)
    self.c_x = int((self.start_x + self.end_x) / 2.0)
    self.c_y = int((self.start_y + self.end_y) / 2.0)

  def compute_area(self):
    return abs(self.end_x - self.start_x) * abs(self.end_y - self.start_y)

  def rectangle_coords(self):
    return self.start_x, self.start_y, self.end_x, self.end_y

  def intersection(self, other):
    inter_start_x, inter_end_x = get_intersection_range(self.start_x,
                                                        self.end_x,
                                                        other.start_x,
                                                        other.end_x)
    inter_start_y, inter_end_y = get_intersection_range(self.start_y,
                                                        self.end_y,
                                                        other.start_y,
                                                        other.end_y)
    return Rectangle(inter_start_x, inter_start_y, inter_end_x, inter_end_y)

  def union(self, other):
    union_start_x = min(self.start_x, other.start_x)
    union_start_y = min(self.start_y, other.start_y)
    union_end_x = max(self.end_x, other.end_x)
    union_end_y = max(self.end_y, other.end_y)
    return Rectangle(union_start_x, union_start_y, union_end_x, union_end_y)

  def to_pred_dict(self):
    return {
        'start_x': self.start_x,
        'start_y': self.start_y,
        'end_x': self.end_x,
        'end_y': self.end_y,
        'center_x': self.c_x,
        'center_y': self.c_y
    }

  def to_polygon(self):
    return [(self.start_x, self.start_y), (self.start_x, self.end_y),
            (self.end_x, self.end_y), (self.end_x, self.start_y)]

  def to_shapely_polygon(self):
    return Polygon(self.to_polygon())

  def centroid_coords(self):
    return self.c_x, self.c_y

  def centroid_coords_point(self):
    return Point(self.c_x, self.c_y)

  def __str__(self):
    return '(start_x=%s, end_x=%s, start_y=%s, end_y=%s)' % (
        self.start_x, self.end_x, self.start_y, self.end_y)
