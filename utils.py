from common_types import Rectangle
import cv2
import dlib
import numpy as np
from shapely.geometry import Point
from shapely.geometry import Polygon


def get_rect_from_tracker(tracker):
  pos = tracker.get_position()
  return Rectangle(
      int(pos.left()), int(pos.top()), int(pos.right()), int(pos.bottom()))


def create_tracker(frame, rect):
  tracker = dlib.correlation_tracker()
  start_x, start_y, end_x, end_y = rect.rectangle_coords()
  rect = dlib.rectangle(start_x, start_y, end_x, end_y)
  tracker.start_track(frame, rect)
  return tracker


def crop_image(frame, rectangle):
  start_x, start_y, end_x, end_y = rectangle.rectangle_coords()
  return frame[start_y:end_y, start_x:end_x]


def is_fully_contained_poly(rect1, poly):
  poly = Polygon(poly)
  coords = Point(rect1.centroid_coords())
  return poly.contains(coords)


def is_fully_contained(rect1, rect2):
  intersection_rect = rect1.intersection(rect2)
  return intersection_rect.compute_area() == rect1.compute_area()


def get_line(point1, point2):
  a = (point1[1] - point2[1]) / float((point1[0] - point2[0]))
  b = point1[1] - a * point1[0]
  return (a, b)


def draw_rect(frame, rect, color):
  f_start_x, f_start_y, f_end_x, f_end_y = rect.rectangle_coords()
  cv2.rectangle(frame, (f_start_x, f_start_y), (f_end_x, f_end_y), color, 2)


def merge_adjcent_predictions(predictions1, predictions2=None, overlap=0.4):
  # Brute force implementation
  merged_predictions = []
  if not predictions2:
    predictions2 = merged_predictions
  for rect2 in predictions1:
    should_skip = False
    for rect1 in predictions2:
      intersection_rectangle = rect1.intersection(rect2)
      max_area = max(rect1.compute_area(), rect2.compute_area())
      ratio = intersection_rectangle.compute_area() / float(max_area)
      if ratio > overlap:
        should_skip = True
        break
    if not should_skip:
      merged_predictions.append(rect2)
  return merged_predictions


def compute_predictions(model, frame, min_confidence, returned_labels):
  conf_predictions = []
  predictions = model.detect(frame)
  for pred in predictions:
    confidence = pred['confidence']
    if confidence > min_confidence and pred['label'] in returned_labels:
      conf_predictions.append(pred)
  return conf_predictions


def pred_to_rect(pred):
  return Rectangle(pred['start_x'], pred['start_y'], pred['end_x'],
                   pred['end_y'])
