def reset_all_devices(ctx):

    db = ctx.db
    ser = ctx.ser
    kit = ctx.kit

    # ==========================
    # FIREBASE
    # ==========================

    db.reference('Light/Khach').set(0)
    db.reference('Light/Ngu').set(0)

    db.reference('Devices/Fan_Khach').set(0)
    db.reference('Devices/Fan_Ngu').set(0)

    db.reference('Devices/Window_Bed').set("CLOSE")
    db.reference('Devices/Window_Living').set("CLOSE")

    db.reference('Devices/Main_Door').set("CLOSE")


    # ==========================
    # UART
    # ==========================

    if ser and ser.is_open:

        ser.write(b"Khach:0\n")
        ser.write(b"Ngu:0\n")

        ser.write(b"Fan_Khach:0\n")
        ser.write(b"Fan_Ngu:0\n")

        ser.write(b"SET_WIN_BED:CLOSE\n")
        ser.write(b"SET_WIN_LIVING:CLOSE\n")

        ser.write(b"SET_DOOR:CLOSE\n")
        ser.write(b"SET_LAUNDRY:CLOSE\n")

    # ==========================
    # SERVO
    # ==========================

    if kit:

        try:

            kit.servo[0].angle = 0
            kit.servo[1].angle = 90
            kit.servo[3].angle = 90
            kit.servo[2].angle = 0

        except Exception as e:

            print("❌ Servo reset lỗi:", e)

    print("✅ RESET ALL DEVICES")