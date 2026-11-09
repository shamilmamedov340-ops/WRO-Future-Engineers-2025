import cv2
import numpy as np
import subprocess
import RPi.GPIO as GPIO
import time

SERVO_PIN = 18
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

MOTOR_PWM_PIN = 13
MOTOR_IN1_PIN = 24
MOTOR_IN2_PIN = 25

GPIO.setup(MOTOR_PWM_PIN, GPIO.OUT)
GPIO.setup(MOTOR_IN1_PIN, GPIO.OUT)
GPIO.setup(MOTOR_IN2_PIN, GPIO.OUT)

pwm_motor = GPIO.PWM(MOTOR_PWM_PIN, 100)
pwm_motor.start(0)

RIGHT_TRIG = 21
RIGHT_ECHO = 20
FORWARD_TRIG = 27
FORWARD_ECHO = 17
LEFT_TRIG = 4
LEFT_ECHO = 23

GPIO.setup(RIGHT_TRIG, GPIO.OUT)
GPIO.setup(RIGHT_ECHO, GPIO.IN)
GPIO.setup(FORWARD_TRIG, GPIO.OUT)
GPIO.setup(FORWARD_ECHO, GPIO.IN)
GPIO.setup(LEFT_TRIG, GPIO.OUT)
GPIO.setup(LEFT_ECHO, GPIO.IN)

MAX_TIMEOUT = 0.05

def set_angle(angle):
    duty_cycle = (angle + 90) / 18.0 + 2
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(0.2)

def go_forward(speed):
    GPIO.output(MOTOR_IN1_PIN, GPIO.HIGH)
    GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
    pwm_motor.ChangeDutyCycle(speed)

def go_backward(speed):
    GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
    GPIO.output(MOTOR_IN2_PIN, GPIO.HIGH)
    pwm_motor.ChangeDutyCycle(speed)
    
def stop_motor():
    GPIO.output(MOTOR_IN1_PIN, GPIO.LOW)
    GPIO.output(MOTOR_IN2_PIN, GPIO.LOW)
    pwm_motor.ChangeDutyCycle(0)

def get_distance(TRIG, ECHO):
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    timeout_start = time.time()
    
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if time.time() - timeout_start > MAX_TIMEOUT:
            return -1

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if time.time() - pulse_start > MAX_TIMEOUT:
            return -1
        
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    return round(distance, 2)

def turn_wheels(direction, duration):
    if direction == "opposite":
        go_backward(50)
        time.sleep(duration)
        stop_motor()
    else:
        stop_motor()

cmd = [
    "rpicam-vid",
    "--width", "160",
    "--height", "120",
    "--codec", "mjpeg",
    "--timeout", "0",
    "--framerate", "40",
    "-o", "-"
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=4096)
bytes_buffer = b""

try:
    while True:
        bytes_buffer += proc.stdout.read(16384)

        a = bytes_buffer.rfind(b'\xff\xd8')
        b = bytes_buffer.rfind(b'\xff\xd9')

        if a != -1 and b != -1 and b > a:
            jpg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:]

            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

            h, w = frame.shape[:2]
            roi = frame[h//3:2*h//3, w//3:2*w//3]

            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            lower_green = np.array([35, 80, 80])
            upper_green = np.array([85, 255, 255])

            lower_red1 = np.array([0, 120, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 120, 100])
            upper_red2 = np.array([180, 255, 255])

            mask_green = cv2.inRange(hsv, lower_green, upper_green)
            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)

            kernel = np.ones((5, 5), np.uint8)
            mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
            mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)

            green_pixels = cv2.countNonZero(mask_green)
            red_pixels = cv2.countNonZero(mask_red)

            if green_pixels > 800 and green_pixels > red_pixels:
                direction = "Turn Left (Green)"
                set_angle(-15)
                go_forward(50)
            elif red_pixels > 800:
                direction = "Turn Right (Red)"
                set_angle(15)
                go_forward(50)
            else:
                direction = "No Target Color"
                set_angle(0)
                go_forward(50)

            right_distance = get_distance(RIGHT_TRIG, RIGHT_ECHO)
            forward_distance = get_distance(FORWARD_TRIG, FORWARD_ECHO)
            left_distance = get_distance(LEFT_TRIG, LEFT_ECHO)

            print(f"Right Distance: {right_distance} cm")
            print(f"Forward Distance: {forward_distance} cm")
            print(f"Left Distance: {left_distance} cm")
            
            if forward_distance < 5 and forward_distance != -1:
                turn_wheels("opposite", 3)
                set_angle(0)

            if left_distance < 5 and left_distance != -1:
                set_angle(15)
                go_forward(50)
                time.sleep(1)
            
            if right_distance > 100 and right_distance != -1:
                set_angle(15)
                go_forward(50)
            elif right_distance < 15 and right_distance != -1:
                set_angle(-15)
                go_forward(50)


            cv2.putText(frame, direction, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
            cv2.rectangle(frame, (w//3, h//3), (2*w//3, 2*h//3), (255, 255, 0), 2)
            cv2.imshow("Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except KeyboardInterrupt:
    print("Program stopped by User")
finally:
    proc.terminate()
    cv2.destroyAllWindows()
    pwm.stop()
    pwm_motor.stop()
    GPIO.cleanup()

