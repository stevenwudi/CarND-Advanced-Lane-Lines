"""
Advanced lane finder
"""
import argparse
import os
import re
import sys

import cv2
from moviepy.editor import VideoFileClip

# CameraCal: class that handles camera calibration operations
from p4lib.CameraCal import CameraCal
# DiagManager: class that handles diagnostic output requests
from p4lib.DiagManager import DiagManager
# RoadManager: class that handles image, projection and line propagation pipeline decisions
from p4lib.RoadManager import RoadManager


# process_road_image handles rendering a single image through the pipeline
def process_image(img):
    # NOTE: The output you return should be a color image (3 channel) for processing video below
    # Run the functions
    roadMgr.findLanes(img)

    # diagnostics requested
    if diagnose:
        # offset for text rendering overlay
        offset = 0
        color = (192, 192, 0)
        # default - full diagnostics
        if scrType & 3 == 3:
            diagScreen = diagMgr.fullDiag()
            offset = 30
        elif scrType & 3 == 2:
            diagScreen = diagMgr.projectionDiag()
            offset = 30
        elif scrType & 3 == 1:
            diagScreen = diagMgr.filterDiag()
            offset = 30
            color = (192, 192, 192)
        if scrType & 4 == 4:
            diagScreen = diagMgr.textOverlay(diagScreen, offset=offset, color=color)
        result = diagScreen
    else:
        if scrType & 4 == 4:
            roadMgr.drawLaneStats()
        result = roadMgr.final
    return result


def main():
    global roadMgr
    global diagMgr
    global diagnose
    global scrType

    parser = argparse.ArgumentParser(prog='main.py', usage='python %(prog)s [options] infilename outfilename',
                                     description='Di Wu\'s Udacity CarND Project 4: Advanced Lane Finding Pipeline')
    parser.add_argument('--diag', type=int, default=0, help='display diagnostics: [0=off], 1=filter, 2=proj 3=full')
    parser.add_argument('--notext', action='store_true', default=False, help='do not render text overlay')
    parser.add_argument('infilename', type=str, default='project_video.mp4',
                        help='input image or video file to process')
    args = parser.parse_args()

    videopattern = re.compile("^.+\.mp4$")
    imagepattern = re.compile("^.+\.(jpg|jpeg|JPG|png|PNG)$")
    image = None
    videoin = None

    file_dir = '/'.join(args.infilename.split('/')[:-1])
    out_file_dir = file_dir + '_out'
    if not os.path.exists(out_file_dir):
        os.mkdir(out_file_dir)
    outfilename = os.path.join(out_file_dir, args.infilename.split('/')[-1])

    # set up pipeline processing options
    # if video - set up in/out videos
    if videopattern.match(args.infilename):
        if not os.path.exists(args.infilename):
            print("Video input file: %s does not exist.  Please check and try again." % (args.infilename))
            sys.exit(1)
        else:
            videoin = args.infilename
            videoout = outfilename

    # if image - set up image processing options
    elif imagepattern.match(args.infilename):
        if not os.path.exists(args.infilename):
            print("Image input file: %s does not exist.  Please check and try again." % (args.infilename))
            sys.exit(4)
        else:
            image = cv2.cvtColor(cv2.imread(args.infilename), cv2.COLOR_BGR2RGB)
    else:
        print("error detected.  exiting.")
    # set up diagnostic pipeline options if requested

    scrType = args.diag
    diagnose = False
    if (scrType & 3) > 0:
        diagnose = True
    if not args.notext:
        scrType = scrType | 4

    # initialization
    # load or perform camera calibrations
    camCal = CameraCal('camera_cal', 'camera_cal/calibration.p')

    # initialize road manager and its managed pipeline components/modules
    roadMgr = RoadManager(camCal, debug=args.diag)

    # initialize diag manager and its managed diagnostics components
    diagMgr = DiagManager(roadMgr)

    # Image only
    if image is not None:
        print("image processing %s..." % args.infilename)
        imageout = process_image(image)
        cv2.imwrite(outfilename, cv2.cvtColor(imageout, cv2.COLOR_RGB2BGR))
        print("done image processing %s..." % args.infilename)

    # Full video pipeline
    elif videoin is not None and videoout is not None:
        print("video processing %s..." % videoin)
        clip1 = VideoFileClip(videoin)
        video_clip = clip1.fl_image(process_image)
        video_clip.write_videofile(videoout, codec='mpeg4', audio=False)
        print("done video processing %s..." % videoin)


if __name__ == '__main__':
    main()
