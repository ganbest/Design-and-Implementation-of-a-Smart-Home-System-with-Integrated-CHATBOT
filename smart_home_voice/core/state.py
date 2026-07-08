# core/state.py


class SystemState:

    def __init__(self):

        # ===== VOICE =====
        self.is_bot_speaking = False

        # ===== AI =====
        self.ai_mode = False
        self.pending_action = None
        self.waiting_window_room = False
        self.waiting_fan_room = False
        self.waiting_light_room = False
        self.waiting_reduce_fan_room = False
        self.waiting_reduce_light_room = False
        self.chat_history = []
        self.last_room = None
        self.last_device = None
        self.demo_mode = False
        self.demo_step = 0
        self.waiting_demo_confirm = False

        # ===== SECURITY =====
        self.security_mode = False

        # ===== SYSTEM =====
        self.system_ready = False
        self.manual_override = {}