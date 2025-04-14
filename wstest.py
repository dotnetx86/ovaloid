import websocket
import threading

def on_message(ws, message):
    print(f"Получено: {message}")

def on_open(ws):
    def run():
        while True:
            msg = input("WH: ")
            ws.send(msg)
    threading.Thread(target=run, daemon=True).start()

def on_close(ws, close_status_code, close_msg):
    print("Соединение закрыто")

ws = websocket.WebSocketApp("ws://localhost:8080",
                            on_open=on_open,
                            on_message=on_message,
                            on_close=on_close)

ws.run_forever()
