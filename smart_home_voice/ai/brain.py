# ai/brain.py

import os
import numpy as np
import pandas as pd

from sklearn.neighbors import KNeighborsClassifier


# ==================================================
# SMART AI BRAIN
# ==================================================

class SmartBrain:

    def __init__(self,file_path='habit_data.csv',default_level=0):
        self.file_path = file_path
        self.default_level = default_level
        self.model = KNeighborsClassifier(n_neighbors=5)
        self.X_train = []
        self.y_train = []
        self.load_data()


    # ==================================================
    # LOAD DATA
    # ==================================================

    def load_data(self):
        if os.path.exists(self.file_path):
            try:
                df = pd.read_csv(self.file_path)
                self.X_train = df[
                    ['hour', 'temp', 'humi']
                ].values.tolist()
                self.y_train = df[
                    'level'
                ].values.tolist()
                print(
                    f"🧠 AI: Loaded "
                    f"{len(self.X_train)} samples."
                )
            except Exception as e:
                print("❌ CSV load lỗi:", e)
                self._load_default_data()
        else:

            self._load_default_data()
        self.update_model()


    # ==================================================
    # DEFAULT DATA
    # ==================================================
    def _load_default_data(self):
        print("🧠 AI: Using default data.")
        self.X_train = [
            [22, 25, 60],
            [23, 24, 65],
            [0, 24, 70],
            [19, 28, 55],
            [12, 32, 40]]
        self.y_train = [1,1,0, 3,0]
    # ==================================================
    # TRAIN MODEL
    # ==================================================
    def update_model(self):
        try:
            if len(self.X_train) < 1:
                return
            self.model.n_neighbors = min(5,len(self.X_train))
            self.model.fit(self.X_train,self.y_train )
        except Exception as e:

            print("❌ Train lỗi:", e)


    # ==================================================
    # LEARN
    # ==================================================

    def learn(self,hour,temp,humi,level):

        self.X_train.append([hour, temp, humi] )
        self.y_train.append(level)
        self.update_model()
        try:
            df = pd.DataFrame(
                self.X_train,
                columns=['hour','temp','humi'] )
            df['level'] = self.y_train
            df.to_csv(self.file_path,index=False)
            print(
                f"🧠 AI learned "
                f"{hour}h | "
                f"{temp}°C | "
                f"level={level}"
            )

        except Exception as e:
            print("❌ Save CSV lỗi:", e)


    # ==================================================
    # PREDICT
    # ==================================================

    def predict(self,hour,temp,humi):
        try:
            prediction = self.model.predict([[hour, temp, humi]])
            return int(prediction[0])
        except Exception as e:
            print("❌ Predict lỗi:", e)
            return 0


    # ==================================================
    # GET PROBABILITY
    # ==================================================

    def get_probability(self,hour,temp,humi):
        try:
            classes = self.model.classes_
            probs = self.model.predict_proba([[hour, temp, humi]])[0]
            max_prob_index = np.argmax(probs)
            best_class = classes[max_prob_index]
            prob_percent = int(probs[max_prob_index] * 100)
            if best_class == 0:
                return 100 - prob_percent
            return prob_percent
        except Exception as e:
            print("❌ Probability lỗi:", e)
            return 50


# ==================================================
# GLOBAL BRAIN
# ==================================================
# ==================================================
# MULTI AI MODELS
# ==================================================

brain_light_khach = None

brain_fan_khach = None

brain_light_ngu = None

brain_fan_ngu = None


# ==================================================
# INIT ALL BRAINS
# ==================================================

def init_brain():

    global brain_light_khach
    global brain_fan_khach
    global brain_light_ngu
    global brain_fan_ngu

    try:

        # ==========================================
        # LIGHT KHACH
        # ==========================================

        brain_light_khach = SmartBrain(
            'light_khach.csv'
        )

        # ==========================================
        # FAN KHACH
        # ==========================================

        brain_fan_khach = SmartBrain(
            'fan_khach.csv'
        )

        # ==========================================
        # LIGHT NGU
        # ==========================================

        brain_light_ngu = SmartBrain(
            'light_ngu.csv'
        )

        # ==========================================
        # FAN NGU
        # ==========================================

        brain_fan_ngu = SmartBrain(
            'fan_ngu.csv'
        )

        print("🧠 ALL AI BRAINS READY")

        return {

            "brain_light_khach":
                brain_light_khach,

            "brain_fan_khach":
                brain_fan_khach,

            "brain_light_ngu":
                brain_light_ngu,

            "brain_fan_ngu":
                brain_fan_ngu
        }

    except Exception as e:

        print("❌ AI Brain lỗi:", e)

        return None