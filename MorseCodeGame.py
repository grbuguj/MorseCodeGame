"""
모스부호 학습 게임 

- 동작 방식
  1. 무작위 알파벳을 선택하고 해당 모스부호를 부저로 출력
  2. 사용자가 버튼(A1)을 짧게/길게 눌러 모스부호 입력
  3. 정답 여부 판정
     - 정답: LED 순차 점등
     - 오답: LED 하나씩 점등 (실패 누적)
     - 4회 실패: LED 전체 깜빡이며 리셋
"""

import time
import random
import pyfirmata2

# ------------------------------
# 보드 연결
# ------------------------------
PORT = pyfirmata2.Arduino.AUTODETECT  # 아두이노 포트 자동 감지
board = pyfirmata2.Arduino(PORT)
print(f"연결 성공: {PORT}")

# ------------------------------
# 핀 설정
# ------------------------------
buzzer = board.digital[3]   # 부저
led_pins = [board.digital[10], board.digital[11], board.digital[12], board.digital[13]]  # LED 4개
button = board.get_pin('a:1:u')   # 버튼 (A1, update 모드)

# ------------------------------
# 모스부호 테이블
# ------------------------------
MORSE_TABLE = {
    'A': ".-", 'B': "-...", 'C': "-.-.", 'D': "-..",  'E': ".",
    'F': "..-.", 'G': "--.",  'H': "....", 'I': "..",   'J': ".---",
    'K': "-.-",  'L': ".-..", 'M': "--",   'N': "-.",   'O': "---",
    'P': ".--.", 'Q': "--.-", 'R': ".-.",  'S': "...",  'T': "-",
    'U': "..-",  'V': "...-", 'W': ".--",  'X': "-..-", 'Y': "-.--",
    'Z': "--.."
}
LETTERS = list(MORSE_TABLE.keys())

# ------------------------------
# 시간 설정
# ------------------------------
DOT = 0.2   # dot 길이
DASH = 0.6  # dash 길이

# ------------------------------
# 게임 변수
# ------------------------------
target_char = ''
target_morse = ''
user_input = ''
wrong_count = 0
press_start = None

# ------------------------------
# LED 유틸
# ------------------------------
def all_leds_off():
    for led in led_pins:
        led.write(0)

def blink_all(times=5, delay=0.2):
    for _ in range(times):
        for led in led_pins: led.write(1)
        time.sleep(delay)
        for led in led_pins: led.write(0)
        time.sleep(delay)

def led_sequence(delay=0.2):
    for led in led_pins:
        led.write(1)
        time.sleep(delay)
    for led in reversed(led_pins):
        led.write(0)
        time.sleep(delay)

# ------------------------------
# 모스부호 재생 (부저)
# ------------------------------
def play_morse(morse):
    print(f"출제 모스부호: {morse}")
    for symbol in morse:
        buzzer.write(0)                 # 소리 ON (회로 따라 반대일 수 있음)
        time.sleep(DOT if symbol == '.' else DASH)
        buzzer.write(1)                 # 소리 OFF
        time.sleep(DOT)
    time.sleep(DOT * 2)                 # 문자 간격

# ------------------------------
# 새로운 문제 출제
# ------------------------------
def new_question():
    global target_char, target_morse, user_input
    user_input = ''
    target_char = random.choice(LETTERS)
    target_morse = MORSE_TABLE[target_char]
    print("\n==============================")
    print(f"출제 문자: {target_char}")
    play_morse(target_morse)

# ------------------------------
# 정답 판정
# ------------------------------
def check_answer():
    global user_input, wrong_count
    print(f"\n사용자 입력: {user_input}")

    if user_input == target_morse:   # 정답
        print("정답! 🎉")
        led_sequence()
        wrong_count = 0
        new_question()
    else:   # 오답
        print("오답! ❌")
        if wrong_count < 3:
            led_pins[wrong_count].write(1)
            wrong_count += 1
            print(f"틀린 횟수: {wrong_count}")
            play_morse(target_morse)    # 같은 문제 반복
        else:
            print("4회 실패 → 리셋")
            blink_all()
            all_leds_off()
            wrong_count = 0
            new_question()
        
    user_input = ''

# ------------------------------
# 버튼 콜백
# ------------------------------
def button_event(value):
    global press_start, user_input, target_morse
    if value is None: return

    if value < 0.5 and press_start is None:  # 버튼 누름
        press_start = time.time()
    elif value > 0.5 and press_start is not None:  # 버튼 뗌
        press_time = (time.time() - press_start) * 1000
        press_start = None

        if press_time < 400:   # dot
            user_input += "."
            print(".", end="", flush=True)
        else:                  # dash
            user_input += "-"
            print("-", end="", flush=True)

        if len(user_input) == len(target_morse):  # 입력 끝 → 판정
            check_answer()

# ------------------------------
# 메인 실행
# ------------------------------
all_leds_off()
button.register_callback(button_event)
button.enable_reporting()
board.samplingOn(100)

try:
    new_question()
    input("엔터를 누르면 게임 종료...\n")
finally:
    board.exit()
    print("게임 종료")
