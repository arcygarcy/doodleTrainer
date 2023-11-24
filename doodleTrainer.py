import cv2
import numpy as np
from PIL import ImageGrab
import pygetwindow
import pyautogui
import time
import random
import keyboard
import editdistance
import easyocr

stop = False

def is_similar(test_word):
    '''Compares OCR to known words that we are looking for'''
    words = ['pets', 'tricks', 'backflip', 'beg', 'dance', 'jump', 'play', 'dead', 'rollover', 'speak']
    threshold = 2

    for word in words:
        distance = editdistance.eval(test_word, word)
        if distance <= threshold:
            if word == 'play' or word == 'dead':
                return 'play_dead'
            return word
    return -1


def ocr(image):
    '''Gets text from an image and compares to known words'''
    coordinates = {}

    reader = easyocr.Reader(['en'], gpu=False, verbose=False)

    results = reader.readtext(image)

    for i, result in enumerate(results):
        text = result[1]
        bbox = result[0]
        top_left, top_right, bottom_right, bottom_left = bbox

        word = is_similar(text.lower())
        if not word == -1:
            coordinates[word] = [(top_left[0] + bottom_right[0]) / 2 , (top_left[1] + bottom_right[1]) / 2]

    return coordinates


def getGameWindows():
    """Tries to get Rewritten and CC windows"""
    toontown_rewritten_win = pygetwindow.getWindowsWithTitle('Toontown Rewritten')
    corporate_clash_win = pygetwindow.getWindowsWithTitle('Corporate Clash')

    return toontown_rewritten_win, corporate_clash_win


def initWindow():
    """Grabs and resizes the window of the game"""

    displayMessage('Finding Window')
    
    toontown_rewritten_win, corporate_clash_win = getGameWindows()

    main_window = None
    if not toontown_rewritten_win == []:
        main_window = toontown_rewritten_win[0]
    elif not corporate_clash_win == []:
        main_window = corporate_clash_win[0]

    if main_window is None:
        return main_window

    main_window.resizeTo(800, 600)
    main_window.moveTo(0, 0)

    return main_window


def getCoordinates(screen, image):
    """Gets the position of a specified image on the screen using cv2 to match it"""
    w, h = image.shape[:-1]

    res = cv2.matchTemplate(screen, image, cv2.TM_CCOEFF_NORMED)
    threshold = .85
    loc = np.where(res >= threshold)

    avg_x, avg_y, count = 0, 0, 0

    for pt in zip(*loc[::-1]):  # Switch columns and rows
        if pt[0] > 50:
            avg_x += pt[0]
            avg_y += pt[1]
            count += 1

    if count > 0:
        avg_x = avg_x / count
        avg_y = avg_y / count

    return avg_x + (h / 2), avg_y + (w / 2)


def calibrate():
    """Determines the coordinates of each of the tricks on the screen"""
    print('Starting Calibration')
    screen = np.array(ImageGrab.grab(bbox=(0, 0, 400, 400)))
    current_mouse_pos = pyautogui.position()

    coordinates = {}
    speedchat = cv2.imread('ImageData/speedchat.png')
    coordinates['speedchat'] = getCoordinates(screen, speedchat)

    pyautogui.click(coordinates['speedchat'])
    pyautogui.click(current_mouse_pos)
    pyautogui.moveTo(current_mouse_pos)

    screen = np.array(ImageGrab.grab(bbox=(coordinates['speedchat'][0] + 20, coordinates['speedchat'][1] - 8, coordinates['speedchat'][0] + 115, coordinates['speedchat'][1] + 135)))

    relative_center = ocr(screen)['pets']

    coordinates['pets'] = [coordinates['speedchat'][0] + relative_center[0]  + 20, coordinates['speedchat'][1] + relative_center[1] - 8]
    pyautogui.moveTo(coordinates['pets'])

    coordinates['tricks'] = [coordinates['pets'][0] + 120, coordinates['pets'][1]]
    pyautogui.moveTo(coordinates['tricks'])

    coordinates['here_boy'] = [coordinates['tricks'][0], coordinates['tricks'][1] + 15]

    pyautogui.moveTo(current_mouse_pos)
    screen = np.array(ImageGrab.grab(bbox=(coordinates['tricks'][0] + 20, coordinates['tricks'][1] - 10, coordinates['tricks'][0] + 120, coordinates['tricks'][1] + 122)))

    tricks = ocr(screen)
    for key in tricks.keys():
        coordinates[key] = [coordinates['tricks'][0] + tricks[key][0] + 20, coordinates['tricks'][1] + tricks[key][1] - 10]

    pyautogui.click(coordinates['speedchat'])
    pyautogui.click(current_mouse_pos)

    print(coordinates)

    if len(coordinates) >= 5:
        displayMessage('Calibration Successful')
        return coordinates, list(tricks.keys())
    else:
        displayMessage('Calibration Failed')
        return None, None


def performTrick(coordinates, selected_tricks):
    """Navigates the mouse to the specified trick via dropdowns and predetermined coordinates"""
    trick = random.randint(0, len(selected_tricks) - 1)
    pyautogui.click(coordinates['speedchat'])
    pyautogui.moveTo(coordinates['pets'])
    pyautogui.moveTo(coordinates['tricks'])
    pyautogui.click(coordinates[selected_tricks[trick]])


def hereBoy(coordinates):
    """Navigates the mouse to call the doodle back to us if it runs too far away"""
    pyautogui.click(coordinates['speedchat'])
    pyautogui.moveTo(coordinates['pets'])
    pyautogui.click(coordinates['here_boy'])


def takeUserInput():
    """Navigates the mouse to call the doodle back to us if it runs too far away"""
    displayMessage('Select the tricks you want to train with commas separating the numbers:')
    trick_message = ""
    for i in range(len(tricks)):
        trick_message += f'{i + 1}: {tricks[i]}'
        if i < len(tricks) - 1:
            trick_message += '\n'
    print('0: All')
    displayMessage(trick_message)
    print(end='>')
    selected = input()
    printBreak()
    displayMessage('How many hours (4-8 is recommended) would you like to run the trainer:')
    print(end='>')
    hours = float(input())
    printBreak()

    selected_tricks = []
    if selected == '0':
        selected_tricks = tricks
    else:
        selected = list(map(int, input().split(',')))
        for i in range(len(selected)):
            selected[i] -= 1
        selected_tricks = [tricks[num] for num in selected]

    return hours, selected_tricks


def printBreak():
    """Break Line for after inputs"""
    print('=========================================================================')


def displayMessage(message):
    """Input a string and have it wrapped nicely"""
    print(message)
    printBreak()


def on_escape():
    global stop
    if not stop:
        displayMessage(f'Stopping Trainer...')
        stop = True

keyboard.add_hotkey('ESC', on_escape)

if __name__ == "__main__":
    print('=========================================================================')
    mode = initWindow()
    if mode is not None:
        displayMessage(f'{mode.title} mode')
        coordinates, tricks = calibrate()

        if coordinates is not None:
            start_time = time.time()
            hours, selected_tricks = takeUserInput()
            tricks_performed = 0
            displayMessage('Starting training, press esc to exit')
            while hours > (time.time() - start_time) / 3600 and not stop:
                rand_variation = random.randint(0, 100)
                if rand_variation > 88:
                    hereBoy(coordinates)
                    time.sleep(1 + (rand_variation * 2) / 100)

                hours_message = f'Hours elapsed: {round((time.time() - start_time) / 3600, 2)}/{hours}'
                tricks_message = f'Tricks attempted: {tricks_performed}'
                displayMessage(hours_message + "\n" + tricks_message)

                performTrick(coordinates, selected_tricks)
                tricks_performed += 1
                time.sleep(4.5 + random.randrange(0, 4))
            displayMessage('Training Completed')
    else:
        displayMessage('No Window Found, Aborting')
