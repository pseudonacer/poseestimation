# Import Openpose
import sys
sys.path.append('./openpose/build/python')
from openpose import pyopenpose as op
from multiprocessing import Pool

import json
import cv2 as cv
import numpy as np
from tqdm import tqdm

# Video clipping
from yt_dlp import YoutubeDL
from stonesoup.reader.video import VideoClipReader
from datetime import timedelta

from copy import copy
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib import animation
import os
import pathlib

def download_video(url, filename):
    """Download youtube video. Ensure it has a unique hour and minute timestamp , and rsync to the youtube library folder."""
    ydl_opts = {
        # 'match_filter': utils.match_filter_func("!is_live"),
        # 'match_filter': utils.match_filter_func("!was_live"),
        "no_warnings": True,
        "overwrites": False,
        "restrictfilenames": True,
        "noprogress": False,
        # "ffmpeg-location": ffmpeg_file,
        "prefer_ffmpeg": True,
        #"download_archive": "youtube_download_archive.log",
        # "cookiefile": cookies_file,
        "outtmpl" : filename,
        # "postprocessors": [ 
        #     {
        #         'key':'FFmpegMetadata',
        #         'add_metadata': True,
        #     },
        #     { 
        #         "key":"Exec",
        #         "exec_cmd": f"touch -m -t %(release_date,upload_date,modified_date|NA)s '%(filepath)s'",
        #     },
        #     { 
        #         "key":"Exec",
        #         "exec_cmd": "rsync --protect-args --remove-source-files -Rtvz '%(filepath)s' user@fileserver:/mnt/zpool-media2/youtube/",
        #     },
        # ]
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)
    except Exception as e: 
        if isinstance(e, DownloadError):
            pass
        elif hasattr(e, 'message'):
            if "Command returned error code 23" in e.message:
                pass
            else:
                raise(e)
        else:
            raise(e)   

def get_timedelta(isoformat):
    try :
        s, microsecond = isoformat.split(".")
    except :
        s = isoformat
        microsecond = 0
    microsecond = min( int(microsecond) , timedelta.max.microseconds)
    hour, minute , second =  list(map(int, s.split(":")))
    return timedelta(minutes = minute, seconds = second, microseconds = microsecond)

class Dataset :
    def __init__(self, filename, path_to_data) :
        self.path_to_data = pathlib.Path(path_to_data)
        self.file_ = open(filename, 'r')
        self.data  = json.load(self.file_)

        # Create a dumping download file
        self._downloads = pathlib.Path('./downloads')
        if not self._downloads.exists() : 
            self._downloads.mkdir()

        # Openpose
        ## Extraction Params
        params = dict()
        params["model_folder"] = "./openpose/models/"
        params["face"] = False
        params["hand"] = True
        ## Conf wrapper
        self.openpose = op.WrapperPython()
        self.openpose.configure(params)
        self.openpose.start()


    def build_dataset(self):
        # Create dataset
        dataset = pathlib.Path('dataset')
        if not dataset.exists() :
            dataset.mkdir()

        # Build train
        trainset = dataset / 'train'
        if not trainset.exists() :
            trainset.mkdir()
        self.build_subset(trainset, 'train')

        # Build dev
        devset   = dataset / 'dev'
        if not devset.exists() :
            devset.mkdir()
        self.build_subset(devset, 'dev')

        # Build test
        testset  = dataset / 'test'
        if not testset.exists() :
            testset.mkdir()
        self.build_subset(testset, 'test')

    def extract_pose(frame_) :
        print(frame_)
        # timestamp, frame = frame_
        # pixels = copy(frame.pixels)
        # # Plot output
        # image = Image.fromarray(pixels)
        # datum = op.Datum()
        # datum.cvInputData = np.array(image)
        # self.openpose.emplaceAndPop(op.VectorDatum([datum]))
        # return np.array(self.openpose.cvOutputData)
        return frame_ * frame_

    def for_speaker(self, speaker, subset, name_subset):
        link_set = self.data[name_subset][speaker]
        # Each link
        for ind, link in enumerate(link_set) :
            # Video Filename
            filename = f'{subset.name}_{speaker}_link{ind}'
            VIDEO_PATH = os.path.join(self._downloads, filename + '.webm')
            download_video(link, VIDEO_PATH)

            # ---- Get the intervals of the video ---- # 
            intervals = link_set[link]

            for interval_id in intervals :
                # interval ID
                timecodes = intervals[interval_id]
                # start of the window
                start_time = timecodes['start_time']
                # end of the window
                end_time = timecodes['end_time']
                # clip the window
                frame_reader = VideoClipReader(VIDEO_PATH,  get_timedelta(start_time), get_timedelta(end_time)) # src : https://stonesoup.readthedocs.io/en/v0.1b5/auto_demos/Video_Processing.html
                NUM_FRAMES = len(list(frame_reader.clip.iter_frames()))
                # ---- Plot each frame ---- # 
                fig, ax = plt.subplots(num="VideoClipReader output")
                artists = []
                # for timestamp, frame in frame_reader:
                #with tqdm(range(60), ncols = 100, desc ="extraction\t") as pbar :
                with Pool() as pool :
                    output = pool.imap(self.extract_pose, range(1000))
                    for i in output : 
                        print(i)
                            #if (len(artists)) == 60:
                            #    break
                            ##for output in results :
                            #ax.axes.xaxis.set_visible(False)
                            #ax.axes.yaxis.set_visible(False)
                            #fig.tight_layout()
                            #artist = ax.imshow(frame, animated=True)
                            #cv.imwrite(f'./frames/frame{len(artists) + 1}.jpg', datum.cvOutputData)
                            #artists.append([artist])
                        # pbar.update(1)
                # ani = animation.ArtistAnimation(fig, artists, interval=20, blit=True, repeat_delay=200)
                # ani.save('./animation.gif', writer='imagemagick', fps=30)
                # plt.show()
                break
            break

        
    def build_subset(self, subset, name_subset) :
        # create subsets
        pose_2d = subset / "pose_2d"
        pose_3d = subset / "pose_3d"
        speaker_set = self.data[name_subset]
        # Each speaker
        self.for_speaker("oliver", subset, name_subset)

# if __name__ == '__main__' :
#     dataset = Dataset("./data/data.json" , "./data/bee")  
#     dataset.build_dataset()



def f(x):
    return x*x

if __name__ == '__main__':
    # start 4 worker processes
    with Pool(processes=4) as pool:

        # print "[0, 1, 4,..., 81]"
        print(pool.map(f, range(1000000)))

        # print same numbers in arbitrary order
        for i in pool.imap_unordered(f, range(1000000)):
            print(i)
