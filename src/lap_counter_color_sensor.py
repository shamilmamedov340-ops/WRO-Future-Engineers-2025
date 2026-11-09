import RPi.GPIO as GPIO
import time

# --- PIN DEFINITIONS ---
# 0.014 - reaction / 30 - pwm
S0_PIN = 22
S1_PIN = 10
S2_PIN = 9
S3_PIN = 11
OUT_PIN = 8

# Motor driver pins (TB6612)
MOTOR_IN1 = 24
MOTOR_IN2 = 25
MOTOR_PWM = 13

# --- CALIBRATION VALUES ---
# NOTE: You MUST recalibrate the sensor after this change.
# The raw values will be much lower.
RED_CALIBRATION = 145
GREEN_CALIBRATION = 200
BLUE_CALIBRATION = 200

# --- SETUP GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup color sensor pins
GPIO.setup(S0_PIN, GPIO.OUT)
GPIO.setup(S1_PIN, GPIO.OUT)
GPIO.setup(S2_PIN, GPIO.OUT)
GPIO.setup(S3_PIN, GPIO.OUT)
GPIO.setup(OUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Set frequency scaling to 100%
GPIO.output(S0_PIN, GPIO.HIGH)
GPIO.output(S1_PIN, GPIO.HIGH)
print("Sensor frequency scaling set to 100%.")

# Setup motor driver pins
GPIO.setup(MOTOR_IN1, GPIO.OUT)
GPIO.setup(MOTOR_IN2, GPIO.OUT)
GPIO.setup(MOTOR_PWM, GPIO.OUT)

# --- MOTOR DRIVER CLASS ---
class TB6612MotorDriver:
    def __init__(self, in1_pin, in2_pin, pwm_pin, pwm_freq=1000):
        self.in1_pin = in1_pin
        self.in2_pin = in2_pin
        self.pwm_pin = pwm_pin
        self.pwm = GPIO.PWM(self.pwm_pin, pwm_freq)
        self.pwm.start(0)
    
    def forward(self, speed):
        speed = max(0, min(100, speed))
        GPIO.output(self.in1_pin, GPIO.HIGH)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(speed)
        
    def stop(self):
        GPIO.output(self.in1_pin, GPIO.LOW)
        GPIO.output(self.in2_pin, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
    
    def cleanup(self):
        self.pwm.stop()

# --- SENSOR FUNCTIONS ---
def get_frequency(s2_state, s3_state):
    GPIO.output(S2_PIN, s2_state)
    GPIO.output(S3_PIN, s3_state)
    
    start_time = time.time()
    
    pulse_count = 0
    # Measure pulses for a much shorter duration
    while time.time() - start_time < 0.01: # CHANGED from 0.1 to 0.01
        if GPIO.input(OUT_PIN) == 0:
            pulse_count += 1
            while GPIO.input(OUT_PIN) == 0:
                pass
    return pulse_count

try:
    print("Robot and color sensor initialized.")
    motor = TB6612MotorDriver(MOTOR_IN1, MOTOR_IN2, MOTOR_PWM)
    
    blue_count = 0

    # Start the motor moving forward at the desired speed
    motor.forward(20)
    print("Robot is now moving forward constantly at 20% speed.")

    while True:
        red_frequency = get_frequency(GPIO.LOW, GPIO.LOW)
        green_frequency = get_frequency(GPIO.HIGH, GPIO.HIGH)
        blue_frequency = get_frequency(GPIO.LOW, GPIO.HIGH)

        normalized_red = (red_frequency / RED_CALIBRATION) * 255
        normalized_green = (green_frequency / GREEN_CALIBRATION) * 255
        normalized_blue = (blue_frequency / BLUE_CALIBRATION) * 255
        
        print("-" * 30)
        print(f"Raw: R={red_frequency} G={green_frequency} B={blue_frequency}")
        print(f"Normalized: R={normalized_red:.2f} G={normalized_green:.2f} B={normalized_blue:.2f}")
        
        if normalized_blue > normalized_red and normalized_blue > normalized_green and normalized_blue > 150:
            blue_count += 1
            print(f"Detected Color: BLUE! Count: {blue_count}")
        else:
            print("Detected Color: UNKNOWN")
        
        # No time.sleep() here to allow the loop to run as fast as possible

except KeyboardInterrupt:
    print("\nProgram terminated.")
finally:
    motor.stop()
    motor.cleanup()
    GPIO.cleanup()
    print("All components cleaned up.")