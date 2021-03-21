import cv2
import numpy as np


_COCO_NAME_PATH = './resources/coco.names'
_YOLO3_WEIGHTS_PATH = '../yolov3.weights'
_YOLO3_CONFIG_PATH = './resources/yolov3.cfg'


class Detector(object):
	
	def __init__(self):
		super(Detector, self).__init__()

	def detect(self, frame):
		return
		
class Yolo3Detector(Detector):

	def __init__(self):
		super(Yolo3Detector, self).__init__()
		self.labels_path = _COCO_NAME_PATH
		self.all_labels = open(self.labels_path).read().strip().split("\n")
		self.weights_path = _YOLO3_WEIGHTS_PATH
		self.model = cv2.dnn.readNetFromDarknet(_YOLO3_CONFIG_PATH, self.weights_path)
		self.model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
		self.model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
		self.ln = self.model.getLayerNames()
		self.ln = [self.ln[i[0] - 1] for i in self.model.getUnconnectedOutLayers()]

	def detect(self, frame):
		(H, W) = frame.shape[:2]
		blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
		self.model.setInput(blob)
		layer_output = self.model.forward(self.ln)
		predictions = []
		# loop over the detections
		for output in layer_output:
			# loop over each of the detections
			for detection in output:
				scores = detection[5:]
				class_id = np.argmax(scores)
				confidence = scores[class_id]
				label = self.all_labels[class_id]

				box = detection[0:4] * np.array([W, H, W, H])
				(center_x, center_y, width, height) = box.astype("int")
				start_x = int(center_x - (width / 2))
				start_y = int(center_y - (height / 2))
				end_x = start_x + width
				end_y = start_y + height
				predictions.append({'start_x': start_x, 
							  'start_y': start_y, 
							  'end_x': end_x, 
							  'end_y': end_y, 
							  'center_x': center_x,
							  'center_y': center_y,
							  'confidence': confidence, 
							  'label': label})
		return predictions


def detector_factory(name):
	if name == "yolo3":
		return Yolo3Detector()