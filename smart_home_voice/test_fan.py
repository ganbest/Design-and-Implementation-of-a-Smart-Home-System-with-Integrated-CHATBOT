from services.pn532_service import init_pn532

import time

pn532 = init_pn532(3)

if not pn532:

    print("PN532 fail")
    exit()

print("Đưa thẻ vào 😄")

while True:

    try:

        uid = pn532.read_passive_target(
            timeout=1.0
        )

        if uid:

            print(
                "UID:",
                [hex(i) for i in uid]
            )

    except Exception as e:

        print("RFID busy...")

    time.sleep(1)