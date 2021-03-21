This is not an officially supported Google product

# Crossing stats project


Extracting aggregative crossing time information from traffic cameras.


Example run command:

python3.8 extract_stats_from_video.py -i  /path/to/video.mp4 -ds EXAMPLE_DATASET_CONFIGURATION -d True

Prerequisites:

1. in the parent directory there must be the "yolov3.weights" file. You can download using: `wget https://pjreddie.com/media/files/yolov3.weights`

2. The video ....

3. Install commands (make sure you run with pip3):

pip install opencv-python<br/>

pip install Shapely<br/>

pip install scikit-image<br/>

sudo apt-get install cmake<br/>

pip install imutils<br/>

pip install dlib<br/>
