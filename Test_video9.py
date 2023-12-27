import cv2
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import csv
from datetime import datetime

class VideoPlayerApp:
    def __init__(self, root, video_source):
        self.root = root
        self.root.title("Dark Spot Detector")

        self.video_source = video_source
        self.vid = cv2.VideoCapture(self.video_source)
     

        self.canvas = tk.Canvas(root)
        self.canvas.pack()

        self.btn_open = tk.Button(root, text="Open Video", command=self.open_video)
        self.btn_open.pack(pady=10)

        self.detect_dark_spot_var = tk.IntVar()
        self.chk_detect_dark_spot = tk.Checkbutton(root, text="Detect Dark Spots", variable=self.detect_dark_spot_var)
        self.chk_detect_dark_spot.pack()

        self.label_area = tk.Label(root, text="Dark Spot Area: ")
        self.label_area.pack()

        # Trackbars for adjusting HSV values
        self.hue_min = tk.IntVar(value=0)
        self.hue_max = tk.IntVar(value=205)
        self.saturation_min = tk.IntVar(value=0)
        self.saturation_max = tk.IntVar(value=100)
        self.value_min = tk.IntVar(value=0)
        self.value_max = tk.IntVar(value=134)

        # Create trackbars
        self.create_trackbar("Hue Min", self.hue_min, 0, 180)
        self.create_trackbar("Hue Max", self.hue_max, 0, 255)
        self.create_trackbar("Saturation Min", self.saturation_min, 0, 255)
        self.create_trackbar("Saturation Max", self.saturation_max, 0, 255)
        self.create_trackbar("Value Min", self.value_min, 0, 255)
        self.create_trackbar("Value Max", self.value_max, 0, 255)

        self.dark_spots_data = []

        # Label to display video playback time
        self.label_time = tk.Label(root, text="", anchor=tk.E)
        self.label_time.pack(side=tk.RIGHT, padx=10, pady=10)

        # Play/Pause buttons
        self.btn_play_pause = tk.Button(root, text="Play", command=self.play_pause)
        self.btn_play_pause.pack(side=tk.RIGHT, padx=10)
        self.is_playing = True

        self.update()
        self.root.mainloop()

    def create_trackbar(self, label, variable, min_val, max_val):
        trackbar_frame = tk.Frame(self.root)
        trackbar_frame.pack()
        label_widget = tk.Label(trackbar_frame, text=label)
        label_widget.pack(side=tk.LEFT)
        trackbar = tk.Scale(trackbar_frame, orient=tk.HORIZONTAL, variable=variable, from_=min_val, to=max_val)
        trackbar.pack(side=tk.LEFT)
        return trackbar

    def open_video(self):
        file_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video files", "*.mp4;*.avi")])
        if file_path:
            self.video_source = file_path
            self.vid = cv2.VideoCapture(self.video_source)
            # Adjust canvas size based on the new video frame size
            self.canvas.config(width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def play_pause(self):
        if self.is_playing:
            self.is_playing = False
            self.btn_play_pause.config(text="Resume")
        else:
            self.is_playing = True
            self.btn_play_pause.config(text="Pause")

    def detect_dark_spots(self, frame, timestamp):
        # Convert the frame to HSV color space
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define lower and upper bounds for dark spots in HSV
        lower_bound = (self.hue_min.get(), self.saturation_min.get(), self.value_min.get())
        upper_bound = (self.hue_max.get(), self.saturation_max.get(), self.value_max.get())

        # Create a mask to extract dark spots
        mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Get bounding box coordinates
            x, y, w, h = cv2.boundingRect(contour)

            # Check if the area is greater than 1000 pixels
            if cv2.contourArea(contour) > 300 and cv2.contourArea(contour)<10000:
                # Draw a red rectangle around the dark spot
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                # Display the area of the dark spot
                area = cv2.contourArea(contour)
                self.label_area.config(text=f"Dark Spot Area: {area} pixels")

                # Save data to list
                current_time = int(self.vid.get(cv2.CAP_PROP_POS_MSEC))
                dark_spot_data = {
                    "Timestamp": timestamp,
                    "Time (ms)": current_time,
                    "X": x,
                    "Y": y,
                    "Width": w,
                    "Height": h,
                    "Area": area
                }
                self.dark_spots_data.append(dark_spot_data)

    def update(self):
        if self.is_playing:
            ret, frame = self.vid.read()

            if self.detect_dark_spot_var.get() == 1 and ret:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.detect_dark_spots(frame, timestamp)

            if ret:
                self.photo = self.convert_frame_to_photo(frame)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

                # Update video playback time
                current_time = int(self.vid.get(cv2.CAP_PROP_POS_MSEC))
                self.label_time.config(text=f"Time: {current_time} ms")

        self.root.after(10, self.update)

    def convert_frame_to_photo(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=img)
        return photo

    def save_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, mode='w', newline='') as csvfile:
                fieldnames = ["Timestamp", "Time (ms)", "X", "Y", "Width", "Height", "Area"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for data in self.dark_spots_data:
                    writer.writerow(data)

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

# Create the Tkinter root window
root = tk.Tk()
root.geometry("1124x968")

# Specify the path to the video file
video_source = "3.mp4"

# Create the VideoPlayerApp instance
app = VideoPlayerApp(root, video_source)
app.save_to_csv()  # Call this method when you want to save the data to CSV
