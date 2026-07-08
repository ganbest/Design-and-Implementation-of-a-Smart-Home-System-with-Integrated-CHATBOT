import serial

from utils.constants import SERIAL_PORT, UART_BAUDRATE

ser = None

def init_uart():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, UART_BAUDRATE)
        print("✅ UART OK")
        return ser
    except Exception as e:
        print("❌ UART lỗi:", e)
        return None