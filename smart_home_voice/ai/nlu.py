from ai.ngucanh import IntentClassifier

nlu = None

def init_nlu():

    global nlu

    try:

        nlu = IntentClassifier()

        print("🧠 NLU OK")

        return nlu

    except Exception as e:

        print("❌ NLU lỗi:", e)

        return None