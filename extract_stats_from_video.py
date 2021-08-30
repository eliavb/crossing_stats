import argparse
from collections import defaultdict as dd
from datetime import datetime
import glob
import os
import pickle
import time


from common_types import Rectangle
import counters
import cv2
import detector
import dlib
import imutils
from imutils.video import FPS

import intersection_configuration
from matcher import Matcher
import numpy as np
from shapely.geometry import Point
from shapely.geometry import Polygon
import utils

ap = argparse.ArgumentParser()

ap.add_argument(
    "-i", "--input", required=True, help="Path to the input video file or glob")

ap.add_argument("-o", "--output", default=None, help="Path to output directory")

ap.add_argument(
    "-f",
    "--frame_skip",
    default=12,
    type=int,
    help="Number of frames to skip between predictions")

ap.add_argument(
    "-c",
    "--confidence",
    default=0.3,
    type=float,
    help="Minimum confidence of prediction")

ap.add_argument(
    "-fw",
    "--frame_width",
    default=1280,
    type=int,
    help=" frame width in pixels")

ap.add_argument(
    "-d",
    "--display",
    default=False,
    type=bool,
    help="Flag indicating if the frame should be displayed during analysis.")

ap.add_argument(
    "-ds",
    "--dataset",
    default=None,
    type=str,
    help="Dataset name to load the specific params")

ap.add_argument(
    "-ext",
    "--extension",
    default=".mp4",
    type=str,
    help="Video extension.")

ap.add_argument(
    "-m",
    "--model",
    default="yolo3",
    type=str,
    help="Model name.")

INTERESTING_LABELS = set(["car", "bus", "truck"])

BOX_COLOR = (0, 255, 0)
FOCUS_COLOR = (255, 0, 0)
IN_COLOR = (255, 255, 0)
DEBUG_COLOR = (255, 255, 255)
OUT_COLOR = (0, 255, 255)
TEXT_COLOR = (0, 0, 255)

MIN_DISTANCE_TO_FOCUS_RECT = 5


def extract_rectangles_from_predictions(frame, dataset_name, detector_model,
                                        min_confidence):
  """Extracts rectangles from model predictions."""
  predictions = utils.compute_predictions(detector_model, frame, min_confidence,
                                          INTERESTING_LABELS)
  predictions_rect = [(utils.pred_to_rect(pred),pred['label']) for pred in predictions]
  # Merge adjcent objects as model may output multiple rectangles per object.
  predictions_rect = utils.merge_adjcent_predictions(predictions_rect)
  if intersection_configuration.DS_TO_SPECIFIC_PARAMS.get(dataset_name, None):
    focus_rect = intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration.DETECTION_BOUNDARIES]
    predictions_rect = [
        (rect,label) for rect,label in predictions_rect
        if utils.is_fully_contained_poly(rect, focus_rect)
    ]

    return predictions_rect


def _check_if_output_exists(input_video_path, args):
  """Checks if the output directory and files exists."""
  output_directory = args["output"]
  if not output_directory:
    output_directory = input_video_path.split(args["extension"])[0]
    if not os.path.exists(output_directory):
      os.makedirs(output_directory)
    else:
      if glob.glob(os.path.join(output_directory, "*")):
        print("skipping", output_directory)
        return
  return output_directory


def _create_dataset_counters(dataset_name):
  abs_counter_rects = []
  touch_line_counters = []
  if intersection_configuration.DS_TO_SPECIFIC_PARAMS.get(dataset_name, None):
    for t in intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration.COUNT_IN_AREA]:
      name, r, ratio = t
      abs_counter_rects.append(counters.AbsCounterTrackerPoly(name, r, ratio))

    for t in intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration.COUNT_IN_AREA_UNIQUE]:
      name, y, poly = t
      for counter_suffix in ['car','motorbike','truck','bus']:
        touch_line_counters.append(counters.AbsCounterTrackerUniq(name + '_' + counter_suffix, y, poly))
      

    
  return abs_counter_rects, touch_line_counters


def _draw_detections(frame, tracker_by_id, dataset_name, abs_counter_rects,
                     touch_line_counters):
  """Draw detections on existing frame."""
  for id_, tracker in tracker_by_id.items():
    rect = utils.get_rect_from_tracker(tracker[0])
    text_id = f"id={id_}"
    cv2.putText(frame, text_id, (rect.start_x, rect.start_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.40, TEXT_COLOR, 2)

  if intersection_configuration.DS_TO_SPECIFIC_PARAMS.get(
      dataset_name, None):
    for i, im_counter in enumerate(abs_counter_rects + touch_line_counters):
      s = " %s=%s " % (im_counter.name, im_counter.get_counter())
      cv2.putText(frame, s, (0, (i + 1) * 20), cv2.FONT_HERSHEY_SIMPLEX,
                  0.40, TEXT_COLOR, 1)

    for t in intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration
        .COUNT_IN_AREA] + intersection_configuration.DS_TO_SPECIFIC_PARAMS[
            dataset_name][intersection_configuration.COUNT_IN_AREA_UNIQUE]:
      _, r, _ = t
      pts = np.array(r).reshape((-1, 1, 2))
      cv2.polylines(frame, [pts], True, TEXT_COLOR)

    poly = intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration.DETECTION_BOUNDARIES]
    pts = np.array(poly).reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], True, FOCUS_COLOR)


def _is_inside_focus_zone(focus_rect, tracker):
  return focus_rect.exterior.distance(
      Point(utils.get_rect_from_tracker(
          tracker).centroid_coords())) > MIN_DISTANCE_TO_FOCUS_RECT


def _save_stats(abs_counter_rects, touch_line_counters, output_directory,
                frames_per_second):
  for counter_rec in abs_counter_rects + touch_line_counters:
    events = np.array(counter_rec.get_frame_series())
    times = np.array(range(len(events))) / float(frames_per_second)
    t_to_count = {t: e for t, e in zip(times, events)}
    out_f_name = os.path.join(output_directory, counter_rec.name + ".pickle")
    print(f"Saving to {out_f_name}")
    pickle.dump(t_to_count, open(out_f_name, "wb"))


def process_video(input_video_path, args):
  """Process video to produce and save aggrgative stats."""
  dataset_name = args["dataset"]

  output_directory = _check_if_output_exists(input_video_path, args)
  if output_directory is None:
    return

  vs = cv2.VideoCapture(input_video_path)
  frames_per_second = int(vs.get(cv2.CAP_PROP_FPS))
  print(f"Frames per seconds {frames_per_second}")
  _, frame = vs.read()

# set up detector (yolo) and init polygons (in dictionary for unique and not unique)
  detector_model = detector.detector_factory(args["model"])
  abs_counter_rects, touch_line_counters = _create_dataset_counters(
      dataset_name)

# set image "main rect"
  image_rect = None
  if intersection_configuration.DS_TO_SPECIFIC_PARAMS.get(dataset_name, None):
    image_rect = intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
        intersection_configuration.IMAGE_BOUNDARIES]

  # Remove objects near the outliers of the focus
  focus_rect = Polygon(
      intersection_configuration.DS_TO_SPECIFIC_PARAMS[dataset_name][
          intersection_configuration.DETECTION_BOUNDARIES])

  matcher = Matcher()
  tracker_by_id = {}
 
  
  # loop over the frames.
  total_frames = -1
  while True:
    total_frames += 1
    _, frame = vs.read()
    if frame is None:
      break
    frame = imutils.resize(frame, width=args["frame_width"])
    # frame = imutils.resize(frame, width=video_witdh)
    if image_rect is not None:
      frame = utils.crop_image(frame, image_rect)
    
    
    if total_frames % args["frame_skip"] == 0:
      predictions_rect = extract_rectangles_from_predictions(
          frame, dataset_name, detector_model, args["confidence"])
      tracker_by_id = matcher.match(tracker_by_id, predictions_rect, frame)
    else:
      predictions_rect = []
      for tracker, label in tracker_by_id.values():
        tracker.update(frame)
        predictions_rect.append((utils.get_rect_from_tracker(tracker),label))

    tracker_by_id = {
        id_: tracker for id_, tracker in tracker_by_id.items()
        if _is_inside_focus_zone(focus_rect, tracker[0])
    }

    for touch_line_counter in touch_line_counters:
      touch_line_counter.update(tracker_by_id)

    for abs_counter in abs_counter_rects:
      abs_counter.update(predictions_rect)

    for r in predictions_rect:
      utils.draw_rect(frame, r[0], OUT_COLOR)
    
    if args["display"]:
    
      _draw_detections(frame, tracker_by_id, dataset_name, abs_counter_rects,
                       touch_line_counters)
      
      cv2.imshow("frame", frame)
      
      key = cv2.waitKey(1) & 0xFF
      if key == ord("q"):
        break

  _save_stats(abs_counter_rects, touch_line_counters, output_directory,
              frames_per_second)

  # close any open windows
 
  
  vs.release()
  cv2.destroyAllWindows()


def main():
  args = vars(ap.parse_args())
  handled_files = set()
  need_attention = glob.glob(args["input"])
  for input_fname in sorted(need_attention):
    print(f"Processing {input_fname}")
    process_video(input_fname, args)
    handled_files.add(input_fname)
    need_attention = set(glob.glob(args["input"])) - handled_files


if __name__ == "__main__":
  main()
