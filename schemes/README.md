# Wiring diagrams

<!-- TODO (Shamil): add the wiring diagram here (Fritzing, KiCad, EasyEDA or even a clear hand drawing photo), e.g. schemes/wiring.png -->

| Function | Signal | GPIO (BCM) |
|----------|--------|-----------|
| Steering servo | PWM | 18 |
| TB6612 motor driver | PWMA / AIN1 / AIN2 | 13 / 24 / 25 |
| Ultrasonic right | TRIG / ECHO | 21 / 20 |
| Ultrasonic front | TRIG / ECHO | 27 / 17 |
| Ultrasonic left | TRIG / ECHO | 4 / 23 |
| TCS3200 colour sensor | S0 / S1 / S2 / S3 / OUT | 22 / 10 / 9 / 11 / 8 |
