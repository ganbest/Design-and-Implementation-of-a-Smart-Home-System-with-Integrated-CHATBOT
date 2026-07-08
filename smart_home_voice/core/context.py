# core/context.py

class AppContext:

    def __init__(

        self,

        # =========================
        # SERVICES
        # =========================

        db=None,
        ser=None,
        kit=None,

        # =========================
        # VOICE
        # =========================

        speak=None,
        is_bot_speaking=None,

        # =========================
        # AI
        # =========================

        brain=None,
        nlu=None,

        brain_light_khach=None,
        brain_fan_khach=None,
        brain_light_ngu=None,
        brain_fan_ngu=None,

        # =========================
        # HARDWARE
        # =========================

        pn532=None,
        rain_sensor=None,
        pn532_lock=None,

        # =========================
        # SYSTEM
        # =========================

        state=None

    ):

        # =========================
        # SERVICES
        # =========================

        self.db = db
        self.ser = ser
        self.kit = kit

        # =========================
        # VOICE
        # =========================

        self.speak = speak
        self.is_bot_speaking = is_bot_speaking

        # =========================
        # AI
        # =========================

        self.brain = brain
        self.nlu = nlu

        self.brain_light_khach = brain_light_khach
        self.brain_fan_khach = brain_fan_khach

        self.brain_light_ngu = brain_light_ngu
        self.brain_fan_ngu = brain_fan_ngu

        # =========================
        # HARDWARE
        # =========================

        self.pn532 = pn532
        self.rain_sensor = rain_sensor
        self.pn532_lock = pn532_lock

        # =========================
        # SYSTEM
        # =========================

        self.state = state