"""Save live stream from the web on HLS protocol to disk.
"""
import argparse
import concurrent.futures
import collections
import datetime
import math
import os

ap = argparse.ArgumentParser()

_SECONDS_IN_HOUR = 3600

ap.add_argument("--save_dir", type=str, default='./',
  help="Directory to save the recording")
ap.add_argument("--max_concurrent_requests", type=int, default=5,
  help="Directory to save the recording")
ap.add_argument("--save_duration_sec", type=int, default=60,
  help="save into video chucnks of this length in seconds")
ap.add_argument("--total_save_time", type=int, default=_SECONDS_IN_HOUR,
  help="save into videos of this length in seconds")
ap.add_argument("--name", type=str, help="Name of stream.")
ap.add_argument("--stream", type=str, help="Stream link.")



def get_chuck_list(name, save_dir, stream):
  playlist_path = os.path.join(save_dir, '%s_playlist' % name)
  command = ('yes | wget --no-check-certificate '
             '%s/playlist.m3u8 -O %s') % (stream, playlist_path)
  command_status = int(os.system(command))
  if command_status != 0:
    print('command_status', command_status)
    return None
  with open(playlist_path) as f_playlist:
    for line in f_playlist:
      if 'chunklist' in line:
        return line.strip()


def download_chuck_list(name, chuck_list, f_path, duration, stream):
  command = ('yes | ffmpeg -i \"%s/%s\" -t %s -codec copy %s') % (stream, chuck_list, duration, f_path)
  return os.system(command)



def lunch(executor, name, save_duration_sec, local_dir, stream):
  current_time_stamp = datetime.datetime.now().strftime('%Y:%m:%d:%H:%M:%S')

  chuck_list = get_chuck_list(name, local_dir, stream)
  f_name = '%s_%s_%s.mp4' % (name, current_time_stamp,
                             save_duration_sec)
  stream_dir = os.path.join(local_dir, name)
  if not os.path.exists(stream_dir):
    os.makedirs(stream_dir)
  local_path = os.path.join(stream_dir, f_name)
  future_download = executor.submit(download_chuck_list, name,
                                    chuck_list, local_path,
                                    save_duration_sec, stream)
  return future_download, local_path, f_name


def save_stream_to_disk(local_dir, total_save_time,
                        save_duration_sec, max_concurrent_requests,
                        name, stream):
  with concurrent.futures.ThreadPoolExecutor(
      max_workers=max_concurrent_requests) as executor:
    steps = int(math.ceil(total_save_time / float(save_duration_sec)))
    stream_to_results = {}
    stream_to_steps = collections.defaultdict(int)
    stream_to_results[name] = lunch(executor, name,
                                           save_duration_sec, local_dir,
                                           stream)
    stream_to_steps[name] += 1

    should_stop = False
    while not should_stop:
      for name, result in stream_to_results.items():
        if result[0].done() and stream_to_steps[name] < steps:
          stream_to_results[name] = lunch(executor, name,
                                                 save_duration_sec, local_dir,
                                                 stream)
          stream_to_steps[name] += 1
      should_stop = True
      for name in stream_to_steps:
        if stream_to_steps[name] < steps:
          should_stop = False
          break
    executor.shutdown(wait=True)


def main():
  args = vars(ap.parse_args())
  save_stream_to_disk(args["save_dir"], args["total_save_time"],
    args["save_duration_sec"], args["max_concurrent_requests"],
    args["name"], args["stream"])


if __name__ == '__main__':
  main()