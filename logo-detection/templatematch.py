#!/usr/bin/env python3
from collections import defaultdict
from pipes import Template
from re import template
import cv2
import sys
import os
import glob
import numpy as np
import argparse

from cv2 import Mat

SCALE_FACTOR = 0.05       # decrease step size for generating smaller images
SCALE_VERSIONS = 3       # number of scaled images to generate for each template
DETECTION_THRESH = 0.05   # max detection threshold. closer to 0 is better when using cv2.TM_SQDIFF_NORMED

class TemplateMatchResult(object):

    def __init__(self, confidence: float, oauth_provider: str, template_img_name: str, template_width: int, template_height: int, match_x: int, match_y: int):
        self.confidence = confidence
        self.oauth_provider = oauth_provider
        self.template_img_name = template_img_name
        self.template_width = template_width
        self.template_height = template_height
        self.match_x = match_x
        self.match_y = match_y

class TemplateMatcher(object):

    def __init__(self, template_dir: str):
        self.debug = False
        self.logo_filenames = self.read_template_filenames(template_dir)
        self.logo_images = self.load_and_scale_templates(self.logo_filenames)

    def read_template_filenames(self, dir: str) -> dict[str, (str, str)]:
        template_images = {}

        template_glob = os.path.join(dir, '*.jpg')

        image_files = glob.glob(template_glob)
        for filepath in image_files:
            self.LOG_DEBUG("Loading template %s" % filepath)

            basename = os.path.basename(filepath)
            oauth_provider = basename.split('-')[0]

            template_images[filepath] = (basename, oauth_provider)

        return template_images

    def load_and_scale_templates(self, template_images: dict[str, (str,str)], scale_factor=SCALE_FACTOR, scale_versions=SCALE_VERSIONS):
        logo_images = defaultdict(list)

        for logo_file, (basename, oauth_provider) in template_images.items():
            small_image_o = cv2.imread(logo_file)   # Read the original images from the file
            small_image = cv2.cvtColor(small_image_o, cv2.COLOR_BGR2GRAY)

            logo_images[oauth_provider].append((basename, small_image))

            # If scale_factor is 0.1, each iteration it will generate a 10%, 20%, 30% smaller image.
            # 0.1 (10%) seems to work pretty well for reasons I don't completely understand yet.
            for i in range(1, SCALE_VERSIONS):
                F = 1.0-(scale_factor*i)
                shrunk_image = cv2.resize(small_image, (0,0), fx=F, fy=F)
                #logo_images[oauth_provider + "_" + str(i)] = shrunk_image   # do something better than this
                logo_images[oauth_provider].append((basename + "_" + str(i), shrunk_image))

        return logo_images

    def LOG_DEBUG(self, str):
        if self.debug:
            sys.stderr.write(str + '\n')

    def matchfile(self, website_img_filename: str) -> list[TemplateMatchResult]:
        image_o = cv2.imread(website_img_filename)
        image = cv2.cvtColor(image_o, cv2.COLOR_BGR2GRAY)
        return self.match(image)

    def __match_original(self, website_img: cv2.Mat, template_image: cv2.Mat, image_name: str, oauth_provider: str):
        # from manual testing, cv2.TM_SQDIFF_NORMED detection works much better than others. 
        # Also, for some reason grayscale images perform worse but they are used frequently in online examples.
        match_result = cv2.matchTemplate(template_image, website_img, cv2.TM_SQDIFF_NORMED)

        # We want the minimum squared difference
        (minVal, _, minLoc, _) = cv2.minMaxLoc(match_result)

        self.LOG_DEBUG("%s minVal: %f" % (image_name, minVal))

        # The closer minVal gets to 0, the better our match. 0.5 seems to be a reasonable threshold.
        if minVal <= DETECTION_THRESH:
            #print('MATCH %s,%f' % (oauth_provider_image, minVal))   # log something
            # Extract the coordinates of our best match
            MPx, MPy = minLoc

            # Step 2: Get the size of the template. This is the same size as the match.
            trows, tcols = template_image.shape[:2]

            return TemplateMatchResult(minVal, oauth_provider, image_name, tcols, trows, MPx, MPy)
        else:
            return None

    def __match_new(self, website_img: cv2.Mat, template_image: cv2.Mat, image_name: str, oauth_provider: str):

        res = cv2.matchTemplate(website_img, template_image, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        self.LOG_DEBUG('%s %s %s' % (oauth_provider, image_name, max_val))

        if max_val >= 0.92:
            template_width, template_height = template_image.shape[:2]
            MPx, MPy = max_loc
            return TemplateMatchResult(max_val, oauth_provider, image_name, template_width, template_height, MPx, MPy)
        else:
            return None

        #loc = False
        # loc = np.where(res >= 0.9)  # loc is tuple of array (array([617]), array([804]))
        # self.LOG_DEBUG('%s %s %s %s' % (oauth_provider, image_name, loc, res))
        # if loc:
        #     point_enumerable = zip(*loc[::-1])
        #     point_list = list(point_enumerable)
        #     size = len(point_list)
        #     if size > 0:
        #         pt = point_list[0] # just take the first one for now
        #         template_width, template_height = template_image.shape[:2]
        #         return TemplateMatchResult(0.9, oauth_provider, image_name, template_width, template_height, pt[0], pt[1])
        
        return None

    def match(self, website_img: cv2.Mat) -> list[TemplateMatchResult]:

        matches = []
        for oauth_provider, image_list in self.logo_images.items():
            for (image_name, template_image) in image_list:
                match_result = self.__match_new(website_img, template_image, image_name, oauth_provider)
                if match_result:
                    matches.append(match_result)
                    break # finish this oauth provider

        return matches

def oauth_detected_colors():
    # lol generate this automatically
    return {
            'google': (255, 0, 0),   # red
            'facebook': (0, 255, 0), # green
            'apple': (0, 0, 255),    # blue
            'github': (255, 128, 0), # orange
            'twitter': (255, 0, 255), # pink
            'microsoft': (153, 51, 255), # purple
            'linkedin': (255, 255, 0),  # yellow
            'amazon': (51, 255, 255) # aqua
        }

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("webpage_paths", type=str, nargs='+', help="One or many webpage screenshots to run detection on.")
    parser.add_argument("--template_dir", required=True, type=str, help="The directory of logo template images")
    parser.add_argument("--debug", help="Increase output verbosity", action="store_true")
    parser.add_argument("--display", help="Show the detected templates. Only works is webpage_path is a single image.", action="store_true")
    args = parser.parse_args()

    matcher = TemplateMatcher(args.template_dir)
    matcher.debug = args.debug

    oauth_colors = oauth_detected_colors()

    single_file = len(args.webpage_paths) == 1

    for image_file in args.webpage_paths:
        base_webpage_name = os.path.basename(image_file)

        webpage_image_o = cv2.imread(image_file)
        webpage_image = cv2.cvtColor(webpage_image_o, cv2.COLOR_BGR2GRAY)

        matches = matcher.match(webpage_image)

        for match in matches:
            print('%s,%s,%s,%f' % (base_webpage_name, match.oauth_provider, match.template_img_name, match.confidence))

            if single_file and args.display:
                color = oauth_colors[match.oauth_provider]
                point1 = (match.match_x, match.match_y)
                point2 = (match.match_x + match.template_width, match.match_y + match.template_height)
                cv2.rectangle(webpage_image_o, point1, point2, color, thickness=2)

    if single_file and args.display:
        # Draw the OAuth Legend
        y_offset = 100
        for oauth_provider, color in oauth_colors.items():
            cv2.putText(webpage_image_o, oauth_provider, (100, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            y_offset += 50

        # Display the original image with the rectangle around the match.
        cv2.imshow('output', webpage_image_o)

        # The image is only displayed if we call this and won't go away until a key is pressed
        cv2.waitKey(0)
        cv2.destroyAllWindows()