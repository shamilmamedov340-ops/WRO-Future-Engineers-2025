# Source code

| File | Description |
|------|-------------|
| `main.py` | Main program: camera-based red/green pillar detection (OpenCV, HSV), wall following with 3 ultrasonic sensors, servo steering and TB6612 motor control. |
| `lap_counter_color_sensor.py` | TCS3200 colour sensor driver: detects the blue lines on the mat and counts them to track laps. |

Run on the Raspberry Pi with `python3 main.py`. See the main [README](../README.md) for wiring and calibration.
