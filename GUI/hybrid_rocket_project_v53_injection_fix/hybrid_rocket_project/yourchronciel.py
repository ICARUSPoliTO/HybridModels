import pyautogui
import keyboard
import time
from PIL import ImageGrab

# Coordinates (from your Paint screenshot)
PIXEL_CHECK_X = 750
PIXEL_CHECK_Y = 400
CLICK_X = 1380
CLICK_Y = 320


# Red color threshold - adjust if needed
def is_red(rgb):
    r, g, b = rgb
    # Check if red channel is high and green/blue are low
    return r > 150 and g < 100 and b < 100


def main():
    print("Starting in 3 seconds... Switch to your target window!")
    print("Press 'L' at any time to stop the script.")
    time.sleep(3)

    print("Script running...")

    while True:
        # Check if 'l' is pressed to exit
        if keyboard.is_pressed('l'):
            print("'L' pressed - Stopping script.")
            break

        # Take a screenshot and get the pixel color
        screenshot = ImageGrab.grab()
        pixel_color = screenshot.getpixel((PIXEL_CHECK_X, PIXEL_CHECK_Y))

        if is_red(pixel_color):
            print(f"Red detected! RGB: {pixel_color}")
            # Press 'd'
            pyautogui.press('d')
            # Small delay before clicking
            time.sleep(0.1)
            # Click at the specified coordinates
            pyautogui.click(CLICK_X, CLICK_Y)

        # Small delay to prevent excessive CPU usage
        time.sleep(0.1)


if __name__ == "__main__":
    main()