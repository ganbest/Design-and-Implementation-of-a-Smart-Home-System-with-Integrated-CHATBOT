# services/pn532_service.py

import time
import smbus2
from adafruit_pn532.i2c import PN532_I2C


class I2CDriverWrapper:

    def __init__(self, bus_num):
        self.bus = smbus2.SMBus(bus_num)

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def writeto(self, address, buffer, *, start=0, end=None):
        out_data = list(buffer[start:end if end else len(buffer)])

        msg = smbus2.i2c_msg.write(address, out_data)

        self.bus.i2c_rdwr(msg)

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        read_len = (end if end else len(buffer)) - start

        msg = smbus2.i2c_msg.read(address, read_len)

        self.bus.i2c_rdwr(msg)

        buffer[start:start + len(msg)] = list(msg)

    def write_then_readinto(
        self,
        out_buf,
        in_buf,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None
    ):

        address = 0x24

        out_data = list(
            out_buf[out_start:out_end if out_end else len(out_buf)]
        )

        msg_w = smbus2.i2c_msg.write(address, out_data)

        read_len = (
            (in_end if in_end else len(in_buf)) - in_start
        )

        msg_r = smbus2.i2c_msg.read(address, read_len)

        self.bus.i2c_rdwr(msg_w, msg_r)

        in_buf[in_start:in_start + len(msg_r)] = list(msg_r)


def init_pn532(bus_num=3):

    pn532 = None

    try:
        i2c_wrapper = I2CDriverWrapper(bus_num)

        retries = 5

        while retries > 0:

            try:
                pn532 = PN532_I2C(
                i2c_wrapper,
                debug=False
                )
                time.sleep(1)
                pn532.SAM_configuration()

                print("✅ PN532 OK")

                return pn532

            except Exception as e:

                retries -= 1

                print(f"⌛ Retry PN532... ({retries})")

                time.sleep(1)

    except Exception as e:
        print("❌ PN532 ERROR:", e)

    print("❌ PN532 FAIL")

    return None