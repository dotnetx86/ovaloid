import tkinter as tk
import websocket
from threading import Thread
from math import hypot
from json import load, loads, dumps

WIDTH, HEIGHT = 1024, 768

class Projectile:
    def __init__(self, canvas, x, y, dx, dy, speed=15):
        self.canvas = canvas
        self.speed = speed
        self.dx = dx
        self.dy = dy
        self.shape = canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="blue")
        self.move()

    def move(self):
        self.canvas.move(self.shape, self.dx * self.speed, self.dy * self.speed)
        x1, y1, x2, y2 = self.canvas.coords(self.shape)
        if x2 < 0 or x1 > WIDTH or y2 < 0 or y1 > HEIGHT:
            self.canvas.delete(self.shape)
        else:
            self.canvas.after(30, self.move)

class BasePlayer:
    def __init__(self, canvas: tk.Canvas, x, y):
        self.canvas = canvas
        self.step = 10
        self.shape = canvas.create_oval(x, y, x + 50, y + 50, fill="red")
        self.group = [self.shape]


    def get_center(self):
        x1, y1, x2, y2 = self.canvas.coords(self.shape)
        return (x1 + x2) / 2, (y1 + y2) / 2


    def area_attack(self):
        coords = self.canvas.coords(self.shape)
        attack = self.canvas.create_oval(coords, outline="red", fill="")
        self.group.append(attack)

        def expand(i):
            coords = self.canvas.coords(self.shape)
            self.canvas.coords(attack, coords[0] + i, coords[1] + i, coords[2] - i, coords[3] - i)
            if i >= 100:
                self.canvas.delete(attack)
                return 
            self.canvas.after(50, expand, i + 10)

        expand(1)
        return attack
        
    def shoot(self, event):
        px, py = self.get_center()
        dx = event.x - px
        dy = event.y - py
        distance = hypot(dx, dy)

        if distance == 0:
            return

        dx /= distance
        dy /= distance

        Projectile(self.canvas, px, py, dx, dy)

class Player(BasePlayer):
    def __init__(self, canvas, multiplayer, x, y):
        super().__init__(canvas, x, y)
        self.multiplayer = multiplayer
        
        self.canvas.bind("<Button-1>", self.shoot)
    
    def move(self, dx, dy):
        coords = self.canvas.coords(self.shape)
        new_x, x2 = (item + dx * self.step for item in coords[::2])
        new_y, y2 = (item + dy * self.step for item in coords[1::2])

        if 0 <= new_x <= WIDTH - 50 and 0 <= new_y <= HEIGHT - 50:
            self.multiplayer.send({ "type": "move", "data": { "coords": [new_x, new_y, x2, y2] } })
            for member in self.group:
                self.canvas.coords(member, new_x, new_y, x2, y2)
    
    def area_attack(self):
        super().area_attack()
        #check enemies inside
        
        
    
    def dash(self, on=True):
        if not on:
            self.step = 10
            return
        
        self.step = 30
        self.canvas.after(5000, self.dash, False)
        
class Enemy(BasePlayer):
    def __init__(self, canvas, x, y):
        super().__init__(canvas, x, y)
        
class Multiplayer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.players = {}
        
        # self.ws
            
        self.ws = websocket.WebSocketApp("ws://localhost:8080",
                            on_open=self.on_open,
                            on_message=self.on_message,
                            on_close=self.on_close)
        Thread(target=self.ws.run_forever, daemon=True).start()
    
    def send(self, msg:dict):
        msg["data"]["id"] = self.playerId
        self.ws.send(dumps(msg))
    
    def on_message(self, ws, msg: bytes):
        print(msg)
        msg = loads(msg)
        playerId = msg["data"]["id"]
        
        match msg["type"]:
            case "login":
                self.playerId = playerId
            case "new" | "respawn":
                plr = Enemy(self.canvas, WIDTH / 2, HEIGHT / 2)
                self.players[playerId] = plr
            case "move":
                plr = self.players[playerId]
                canvas.coords(plr.shape, *msg["data"]["coords"])

    def on_open(self, ws):
        self.ws.send(dumps({ "type": "login" }))
        print(f"Connected to the server")

    def on_close(self, ws, close_status_code, close_msg):
        print("Disconnected")

class Game:
    def __init__(self, root, canvas):
        self.root = root
        self.canvas = canvas
        self.canvas.pack()

        self.multiplayer = Multiplayer(canvas)
        self.player = Player(self.canvas, self.multiplayer, WIDTH / 2, HEIGHT / 2)
        self.holding_keys = set()

        self.root.bind("<KeyPress>", self.keypress)
        self.root.bind("<KeyRelease>", self.keyrelease)
        
        # Enemy(canvas, WIDTH / 2, 150)

        self.move_loop()

    def move_loop(self):
        for key in self.holding_keys:
            match key:
                case "w":
                    self.player.move(0, -1)
                case "a":
                    self.player.move(-1, 0)
                case "s":
                    self.player.move(0, 1)
                case "d":
                    self.player.move(1, 0)
        self.canvas.after(25, self.move_loop)

    def keypress(self, event):
        self.holding_keys.add(event.keysym)
        match event.keysym:
            case "q":
                self.player.dash()
            case "f":
                self.player.area_attack()

    def keyrelease(self, event):
        self.holding_keys.discard(event.keysym)
        
class Menu:
    def __init__(self, root, canvas: tk.Canvas):
        self.root = root
        self.canvas = canvas
        self.canvas.create_text(WIDTH / 2, 20, text='Classes', font=('Arial', 15))
                
        with open("classes.json", "r") as f:
            self.classes = load(f)
        
        i = 100
        for name, data in self.classes.items():
            print(name, data)
            self.draw_class(name, data, i, 300)
            i += 300
            
        play = tk.Button(self.canvas, text="Play", font=("Arial", 16), command=self.play)
        # play.place(x=WIDTH / 2 - 16 * 2, y=HEIGHT - 50)
        self.canvas.create_window(WIDTH / 2, HEIGHT - 50, window=play)
        
        self.notif = canvas.create_text(WIDTH / 2, HEIGHT - 100, font=("Arial", 16))
        
        self.canvas.pack()
        
    def draw_class(self, name, data, x, y):
        rect = self.canvas.create_rectangle(x, y, x + 250, y + 300, fill="")
        self.canvas.create_text(x + 125, y + 10, text=name, font=('Arial', 15))
        self.canvas.create_text(x + 125, y + 150, text=data["Description"], font=('Arial', 15), width=200)
        
        self.classes[name]["rect"] = rect
        select = tk.Button(self.canvas, text="Select", font=("Arial", 16), command= lambda: self.select(name))
        # select.place(x=x + 85, y=y + 250)
        self.canvas.create_window(x + 125, y + 250, window=select)
    
    def select(self, name):
        self.selected = name
        for char, data in self.classes.items():
            if char == name:
                self.canvas.itemconfig(data["rect"], outline="blue")
            else:
                self.canvas.itemconfig(data["rect"], outline="black")
    
    def play(self):
        if not hasattr(self, "selected"):
            self.notify("Select a class!")
            return
        
        self.canvas.delete("all")
        Game(self.root, self.canvas)
    
    def notify(self, msg):
        self.canvas.itemconfig(self.notif, text=msg)
        self.canvas.after(5000, lambda: self.canvas.itemconfig(self.notif, text=""))
        


if __name__ == "__main__":
    root = tk.Tk()
    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH, bg="white")
    menu = Menu(root, canvas)
    
    # game = Game(root)
    root.mainloop()
