#!/usr/bin/env python3

import asyncio
import sys

import cv2
import numpy as np
import find_ball

import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps


try:
    from PIL import ImageDraw, ImageFont
except ImportError:
    sys.exit('run `pip3 install --user Pillow numpy` to run this example')



def calcDistance(ball, ballSize=40.0, focalLength=220.0):
    if ball is not None:
        return (focalLength/ball[2])*ballSize
    return None

# Define a decorator as a subclass of Annotator; displays battery voltage
class BatteryAnnotator(cozmo.annotate.Annotator):
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)
        bounds = (0, 0, image.width, image.height)
        batt = self.world.robot.battery_voltage
        text = cozmo.annotate.ImageText('BATT %.1fv' % batt, color='green')
        text.render(d, bounds)

# Define a decorator as a subclass of Annotator; displays the ball
class BallAnnotator(cozmo.annotate.Annotator):

    ball = None
    distance = None
    def apply(self, image, scale):
        d = ImageDraw.Draw(image)
        bounds = (0, 0, image.width, image.height)

        if BallAnnotator.ball is not None:

            #double size of bounding box to match size of rendered image
            BallAnnotator.ball = np.multiply(BallAnnotator.ball,2)

            #define and display bounding box with params:
            #msg.img_topLeft_x, msg.img_topLeft_y, msg.img_width, msg.img_height
            box = cozmo.util.ImageBox(BallAnnotator.ball[0]-BallAnnotator.ball[2],
                                      BallAnnotator.ball[1]-BallAnnotator.ball[2],
                                      BallAnnotator.ball[2]*2, BallAnnotator.ball[2]*2)

            text = "find_ball: "+ ("%.2f" % calcDistance(BallAnnotator.ball))
            text = "find_ball: "+ ("%.2f" % BallAnnotator.distance)
            imtx = cozmo.annotate.ImageText(text)
            cozmo.annotate.add_img_box_to_image(image, box, "green", text=imtx)

            BallAnnotator.ball = None


async def run(robot: cozmo.robot.Robot):
    '''The run method runs once the Cozmo SDK is connected.'''

    #add annotators for battery level and ball bounding box
    robot.world.image_annotator.add_annotator('battery', BatteryAnnotator)
    robot.world.image_annotator.add_annotator('ball', BallAnnotator)

    try:
        trigger = true
        while trigger:
            #get camera image
            event = await robot.world.wait_for(cozmo.camera.EvtNewRawCameraImage, timeout=30)

            #convert camera image to opencv format
            opencv_image = cv2.cvtColor(np.asarray(event.image), cv2.COLOR_RGB2GRAY)

            #find the ball
            # About to roll in and look around for it
            ball = find_ball.find_ball(opencv_image)
            distance = calcDistance(ball)
            #set annotator ball
            BallAnnotator.ball = ball
            BallAnnotator.distance = distance
            ##Moving the robot to the ball
            if not robot.has_in_progress_actions:
                if distance is not None:
                    if distance > 20:
                         l_wheel_speed = 3
                         r_wheel_speed = 3
                         robot.drive_wheels(l_wheel_speed, r_wheel_speed)
                    else:
                         trigger = false
                else:
                    robot.drive_wheels(0, 0)

    except KeyboardInterrupt:
        print("")
        print("Exit requested by user")
    except cozmo.RobotBusy as e:
        print(e)



if __name__ == '__main__':
    cozmo.run_program(run, use_viewer = True, force_viewer_on_top = True)
