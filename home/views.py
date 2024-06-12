import datetime
import glob
import os
import time
import cv2
import numpy as np
import pygame
import pyttsx3
from cvzone.HandTrackingModule import HandDetector
from django.shortcuts import render
from collections import deque
import threading  # Import threading module for running Pygame in a separate thread
from time import sleep
from django.contrib.auth.hashers import make_password, check_password
from translate import Translator
import speech_recognition as sr
from home.models import RegisteredUser


def fPage(request):
    return render(request,'home/template/signup.html')

def index(request, uname,path='Default'):
    # Replace 'Default' with the actual folder path
    presentation_folder = path

    # Get a list of .png files in the folder
    png_files = glob.glob(os.path.join(presentation_folder, '*.png'))

    # Create a context dictionary with the list of .png files
    context = {
        'FolderDets': png_files,
        'uname':uname,
    }
    return render(request, 'home/template/index.html', context)


def signup(request):
    name = request.POST.get('name')
    age = request.POST.get('age')
    gender = request.POST.get('gender')
    uname = request.POST.get('uname')
    passw = request.POST.get('passw')

    # Hash the password before storing it
    hashed_passw = make_password(passw)

    RegisteredUser1 = RegisteredUser.objects.filter(username=uname).first()
    if RegisteredUser1 is not None:
        return render(request, 'home/template/signup.html', {'incorrect': 'Username already exists'})
    else:
        RegisteredUser1 = RegisteredUser.objects.create(full_name=name, age=age, gender=gender, username=uname, password=hashed_passw)
        return render(request, 'home/template/signup.html', {'incorrect': 'Registered Successfully'})

def login(request):
    uname = request.POST.get('uname')
    passw = request.POST.get('passw')

    RegisteredUser1 = RegisteredUser.objects.filter(username=uname).first()

    if RegisteredUser1 is not None and check_password(passw, RegisteredUser1.password):
        # Password matches, proceed with login
        presentation_folder = 'Default'
        png_files = glob.glob(os.path.join(presentation_folder, '*.png'))
        context = {'FolderDets': png_files,
                   'uname':RegisteredUser1.full_name}
        return render(request, 'home/template/index.html', context)
    else:
        return render(request, 'home/template/signup.html', {'incorrect': 'Incorrect Username or Password'})

def run_pygame(Fname):

    # For bluetooth module
    # PORT = "COM5"
    # BUADRATE = 9600

    # Initialize Pygame
    pygame.init()
    # robot = serial.Serial(PORT, BUADRATE)  # connect robot

    # Set up the window
    window = pygame.display.set_mode((1200, 400))

    # Load the track and car images
    track = pygame.image.load(Fname)  # Replace with your track image filename
    car = pygame.image.load('tesla.png')
    car = pygame.transform.scale(car, (30, 60))

    # Car initial position
    car_x = 997
    car_y = 300

    # Other variables
    clock = pygame.time.Clock()
    focal_dis = 30
    direction = 'up'
    drive = True
    cam_x_offset = 0
    cam_y_offset = 0
    clicked_points = []  # List to store clicked points on the path
    end_point = (441, 60)  # Replace with actual end point coordinates

    def is_on_path(click_pos):
        """
        Checks if the click position is on the path (track image).

        This is a simple implementation using the bounding box of the track image.
        You can replace it with a more precise pixel-perfect collision detection
        if needed.
        """
        track_rect = track.get_rect()  # Get the bounding box of the track image
        return track_rect.collidepoint(click_pos)  # Check if click is within the bounding box

    DELAY = 3
    counter = 1

    try:
        while True:
            # Program quit
            for event in pygame.event.get():
                # Spacebar to stop/resume
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        drive = not drive  # Toggle drive state (stopped/moving)
                        print("Spacebar pressed, drive:", drive)
                        if counter % 2 == 1:
                            # robot.write(b's')
                            counter += 1
                        else:
                            # robot.write(b'f')
                            counter += 1

                    elif event.key == pygame.K_r:
                        clicked_points = []  # Clear the list of clicked points
                        print("R key pressed, clicked points cleared")
                    elif event.key == pygame.K_q:
                        if direction == 'left':
                            direction = 'right'
                            car = pygame.transform.rotate(car, 180)
                            cam_x_offset = 30
                        elif direction == 'down':
                            direction = 'up'
                            car = pygame.transform.rotate(car, 180)
                            cam_y_offset = -10



                # Track click detection
                if event.type == pygame.MOUSEBUTTONDOWN:
                    click_pos = pygame.mouse.get_pos()
                    print("Clicked coordinates:", click_pos)
                    if is_on_path(click_pos):
                        clicked_points.append(click_pos)


            # Skip remaining loop if car is stopped (drive is False)
            if not drive:
                continue

            # Frame rate
            clock.tick(30)

            # Camera
            cam_x = car_x + 15 + cam_x_offset
            cam_y = car_y + 15 + cam_y_offset

            # Direction pixels
            up_px = window.get_at((cam_x, cam_y - focal_dis))[0]
            right_px = window.get_at((cam_x + focal_dis, cam_y))[0]
            down_px = window.get_at((cam_x, cam_y + focal_dis))[0]
            left_px = window.get_at((cam_x - focal_dis, cam_y))[0]
            print(up_px, right_px, down_px, left_px)

            # ---------------- Car movements ---------------- #

            # Change direction
            # Check if the color is red=255, green=127, blue=39
            if up_px == 172 and right_px == 46 and down_px == 46:
                print("Exiting due to detected color")
                break
            if up_px == 255 and right_px == 233 and down_px == 46:
                print("Exiting due to detected color")
                break

            if direction == 'up' and up_px != 255 and right_px == 255:
                # up to right
                direction = 'right'
                cam_x_offset = 30
                car = pygame.transform.rotate(car, -90)
                # robot.write(b'r')
                sleep(DELAY)


            elif direction == 'right' and right_px != 255 and down_px == 255:
                # right to down
                direction = 'down'
                car_x += 30
                cam_x_offset = 0
                cam_y_offset = 30
                car = pygame.transform.rotate(car, -90)
                # robot.write(b'r')
                sleep(DELAY)

            elif direction == 'down' and down_px != 255 and right_px == 255:
                # down to right
                direction = 'right'
                car_y += 30
                cam_x_offset = 30
                cam_y_offset = 0
                car = pygame.transform.rotate(car, 90)
                # robot.write(b'l')
                sleep(DELAY)

            elif direction == 'right' and right_px != 255 and up_px == 255:
                # right to up
                direction = 'up'
                car_x += 30
                cam_x_offset = 0
                car = pygame.transform.rotate(car, 90)
                # robot.write(b'l')
                sleep(DELAY)

            elif direction == 'up' and up_px != 255 and left_px == 255:
                # up to left
                direction = 'left'
                car = pygame.transform.rotate(car, 90)
                # robot.write(b'l')
                sleep(DELAY)

            elif direction == 'left' and left_px != 255 and down_px == 255:
                # left to down
                direction = 'down'
                cam_y_offset = 30
                car = pygame.transform.rotate(car, 90)
                # robot.write(b'l')
                sleep(DELAY)

            elif direction == 'down' and down_px != 255 and left_px == 255:
                # down to left
                direction = 'left'
                car_y += 30
                cam_y_offset = 0
                car = pygame.transform.rotate(car, -90)
                # robot.write(b'r')
                sleep(DELAY)

            elif direction == 'left' and left_px != 255 and up_px == 255:
                # left to up
                direction = 'up'
                car = pygame.transform.rotate(car, -90)
                # robot.write(b'r')
                sleep(DELAY)

            # Check collision with rectangles
            def check_collision(x, y):
                for rect in clicked_points:
                    if rect[0] < x < rect[0] + 10 and rect[1] < y < rect[1] + 10:
                        return True
                return False

            # Drive
            if direction == 'up' and up_px == 255 and not check_collision(car_x, car_y - 2):
                car_y -= 2
                # robot.write(b'f')

            elif direction == 'right' and right_px == 255 and not check_collision(car_x + 2, car_y):
                car_x += 2
                # robot.write(b'f')

            elif direction == 'down' and down_px == 255 and not check_collision(car_x, car_y + 2):
                car_y += 2
                # robot.write(b'f')

            elif direction == 'left' and left_px == 255 and not check_collision(car_x - 2, car_y):
                car_x -= 2
                # robot.write(b'f')

            elif left_px != 255 and right_px != 255 and up_px != 255 and down_px != 255:
                drive2 = False
                # robot.write(b's')

            # ---------------- ------------- ---------------- #

            # Window update
            window.fill((0, 0, 0))

            # Draw the track and car
            window.blit(track, (0, 0))
            window.blit(car, (car_x, car_y))
            pygame.draw.circle(window, (0, 255, 0), (cam_x, cam_y), 5, 5)

            # Draw clicked rectangles
            for point in clicked_points:
                pygame.draw.rect(window, (255, 0, 0), (point[0], point[1], 50, 50))  # Red rectangle, size 10x10

            pygame.display.update()
    finally:
        pygame.quit()  # Quit Pygame


def execPresentation(request, Fname,uname):
    # Start Pygame in a separate thread
    pygame_thread = threading.Thread(target=run_pygame, args=(Fname,))
    pygame_thread.start()

    parts = Fname.split('\\')

    # The last part of the split string will be the filename
    filename_with_extension = parts[-1]

    # Split the filename and extension
    filename, extension = filename_with_extension.split('.')
    print(filename)
    # Get a list of .png files in the folder
    png_files = glob.glob(os.path.join(filename, '*.png'))
    print(filename)
    # Create a context dictionary with the list of .png files
    context = {
        'FolderDets': png_files,
        'uname' : uname,
    }
    return render(request, 'home/template/index.html', context)

def get_file_extension(folder_path, fName):
    full_path = os.path.join(folder_path, fName)
    _, extension = os.path.splitext(full_path)
    return extension


