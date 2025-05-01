import tkinter as tk
import websocket
from time import time, sleep
from threading import Thread
from math import hypot
from json import loads, dumps

WIDTH, HEIGHT = 1024, 768
CLASSES = {
    "Areaer": {
        "Description": "The deafult free class. Attacks by creating an area wave damaging anyone it hits or by shooting a projectile",
        "AbilityDamage": 50,
        "AbilityCooldown": 2,
        "ProjectileSpeed": 15,
        "ProjectileDamage": 20,
        "ProjectileCooldown": 0.1
    },
    "Dasher": {
        "Description": "A faster and harder class for experienced players. Attacks by dashing in the enemy or by shooting a projectile",
        "AbilityDamage": 50,
        "AbilityCooldown": 5,
        "ProjectileSpeed": 30,
        "ProjectileDamage": 50,
        "ProjectileCooldown": 5
    }
}

class Projectile:
    def __init__(self, canvas: tk.Canvas, coords: tuple, direction: tuple, shooterId, multiplayer=None):
        self.canvas = canvas
        self.dx, self.dy = direction
        self.shooterId = shooterId
        self.multiplayer = multiplayer
        self.playerId = self.multiplayer and self.multiplayer.playerId
        self.info = (self.multiplayer and CLASSES[self.multiplayer.players[self.shooterId]["class"]]) or shooterId.plrClass
        self.shape = self.canvas.create_oval(*coords, fill="blue")
        self.move()
        
    def __del__(self):
        self.canvas.delete(self.shape)

    def move(self):
        self.canvas.move(self.shape, self.dx * self.info["ProjectileSpeed"], self.dy * self.info["ProjectileSpeed"])
        x1, y1, x2, y2 = self.canvas.coords(self.shape)
        if self.multiplayer:
            overlapping = self.canvas.find_overlapping(x1, y1, x2, y2)
            print(overlapping)
            plr:Player = self.multiplayer and self.multiplayer.players[self.playerId]["shape"]
            if plr.shape in overlapping:
                print("aoaoao")
                plr.update_health(plr.health - self.info["ProjectileDamage"], shooter=self.shooterId)
                del self
                return
                # self.multiplayer.send({ "type": "damage", "data": { "id": self.multiplayer.playerId, "shooter": self.shooterId } })
        if x2 < 0 or x1 > WIDTH or y2 < 0 or y1 > HEIGHT:
            del self
        else:
            self.canvas.after(30, self.move)

class BasePlayer:
    def __init__(self, canvas: tk.Canvas, coords: tuple):
        self.canvas = canvas
        self.step = 10
        self.shape = canvas.create_oval(*self.from_center((0, 0, 50), coords), fill="red", width=2)
        self.health = 100
        self.alive = True
        self.healthBar = canvas.create_oval(0, 0, 0, 0, fill="black")
        self.group = [self.shape, self.healthBar]
        
    def __del__(self):
        print("dele")
        self.canvas.delete(*(i for i in self.group))
            
    def die(self):
        print("die")
        self.alive = False
        self.canvas.delete(*(i for i in self.group))
    
    def respawn(self, coords: tuple):
        self.shape = canvas.create_oval(*self.from_center((0, 0, 50), coords), fill="red", width=2)
        self.health = 100
        self.healthBar = canvas.create_oval(0, 0, 0, 0, fill="black")
        self.group = [self.shape, self.healthBar]
        self.alive = True
        
    
    def update_health(self, health):
        self.health = health
        shapePos = self.canvas.coords(self.shape)
        size = [(shapePos[2] - shapePos[0]) / 2, (shapePos[3] - shapePos[1]) / 2]
        center = [shapePos[0] + size[0], shapePos[1] + size[1]]
        # cx, cy = ((item * (1 / 100)) / 2 for item in center)
        rad = [size[0] * ((100 - self.health) / 100), size[1] * ((100 - self.health) / 100)]
        
        self.canvas.coords(self.healthBar, center[0] - rad[0], center[1] - rad[1], center[0] + rad[0], center[1] + rad[1])

    def move(self, x, y):
        for member in self.group:
            pos = self.canvas.coords(member)
            self.canvas.coords(member, *self.from_center(pos, (x, y)))

    def get_center(self, coords=None):
        pos = coords or self.canvas.coords(self.shape)
        return (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2
    
    def from_center(self, pos, center):
        r = (pos[2] - pos[0]) / 2
        
        return center[0] - r, center[1] - r, center[0] + r, center[1] + r
    

    def area_attack(self, check=None):
        coords = self.canvas.coords(self.shape)
        attack = self.canvas.create_oval(coords, outline="red", fill="", width=3)
        self.group.append(attack)

        def expand(i):
            coords = self.canvas.coords(self.shape)
            coords = (coords[0] - i, coords[1] - i, coords[2] + i, coords[3] + i)
            self.canvas.coords(attack, *coords)
            if (check): check(coords)
            if i >= 50:
                self.group.remove(attack)
                self.canvas.delete(attack)
                return 
            self.canvas.after(10 if i < 45 else 100, expand, i + 5)

        expand(1)
        return attack

class Player(BasePlayer):
    def __init__(self, canvas, plrClass, multiplayer, coords: tuple):
        super().__init__(canvas, coords)
        multiplayer.players[multiplayer.playerId] = { "shape": self }
        self.plrClass = CLASSES[plrClass]
        self.multiplayer = multiplayer
        self.area_last = 0
        self.dash_last = 0
        self.shoot_last = 0
        
        
        self.canvas.bind("<Button-1>", self.shoot)
    
    def update_health(self, health, **data):
        print(f"from {self.health} to {health}")
        self.multiplayer.send({ "type": "health", "data": { "health": health } | data })
        super().update_health(health)
    
    def move(self, dx, dy):
        if not self.alive: return
        
        coords = self.canvas.coords(self.shape)
        new_x, x2 = (item + dx * self.step for item in coords[::2])
        new_y, y2 = (item + dy * self.step for item in coords[1::2])

        if 0 <= new_x and x2 <= WIDTH and 0 <= new_y and y2 <= HEIGHT:
            center = self.get_center((new_x, new_y, x2, y2))
            
            self.multiplayer.send({ "type": "move", "data": { "coords": list(center) } })
            super().move(*center)
    
    def area_attack(self):
        now = time()
        if now - self.area_last < self.plrClass["AbilityCooldown"]: return
        
        self.area_last = now
        super().area_attack()
        #check enemies inside
        
        
    
    def dash(self, on=True):
        now = time()
        if not on or now - self.dash_last < self.plrClass["AbilityCooldown"]:
            self.step = 10
            return
        
        self.dash_last = now
        self.step = 30
        self.canvas.after(5000, self.dash, False)
    
    def shoot(self, event):
        if not self.alive: return
        
        now = time()
        if now - self.shoot_last < self.plrClass["ProjectileCooldown"]: return
        
        self.shoot_last = now
        
        # self.update_health(self.health - 10)
        
        px, py = self.get_center()
        dx = event.x - px
        dy = event.y - py
        distance = hypot(dx, dy)

        if distance == 0:
            return

        dx /= distance
        dy /= distance
        
        self.multiplayer.send({ "type": "projectile", "data": { "coords": [px - 5, py - 5, px + 5, py + 5], "direction": [dx, dy], "speed": self.plrClass["ProjectileSpeed"] } })
        Projectile(self.canvas, (px - 5, py - 5, px + 5, py + 5), (dx, dy), self)
        
class Enemy(BasePlayer):
    def __init__(self, canvas, coords: tuple):
        print("crea")
        super().__init__(canvas, coords)
        
class Multiplayer:
    def __init__(self, canvas, plrClass):
        self.canvas = canvas
        self.plrClass = plrClass
        self.players = {}
        
        # self.ws
            
        self.ws = websocket.WebSocketApp("ws://localhost:8080",
                            on_open=self.on_open,
                            on_message=self.on_message,
                            on_close=self.on_close)
        try:
            Thread(target=self.ws.run_forever, daemon=True).start()
        except Exception as err:
            print("websocket error:")
            print(err)
        
    def send(self, msg:dict):
        msg["data"]["id"] = self.playerId
        self.ws.send(dumps(msg))
        
    
    def on_message(self, ws, msg: str):
        msg: dict = loads(msg)
        data = msg["data"]
        playerId = data["id"]
        
        match msg["type"]:
            case "login":
                print(msg)
                self.playerId = playerId
                for plrId, plrData in data["players"].items():
                    if plrId == playerId:
                        continue
                    
                    plr = Enemy(self.canvas, tuple(plrData["coords"]))
                    self.players[plrId] = { "shape": plr, "alive": True, "class": plrData["class"] }
            case "new":
                plr = Enemy(self.canvas, data["coords"])
                self.players[playerId] = { "shape": plr, "alive": True, "class": data["class"] }
            case "respawn":
                print("resp")
                plr: BasePlayer = self.players[playerId]["shape"]
                plr.respawn(tuple(data["coords"]))
            case "move":
                plr: Enemy = self.players[playerId]["shape"]
                plr.move(*data["coords"])
            case "projectile":
                proj = Projectile(self.canvas, tuple(data["coords"]), tuple(data["direction"]), playerId, self)
            case "health":
                plr: Enemy = self.players[playerId]["shape"]
                plr.update_health(data["health"])
            case "death":
                print("death")
                print(self.players)
                self.players[playerId]["alive"] = False
                self.players[playerId]["shape"].die()
            case "leave":
                del self.players[playerId]["shape"]
                self.players.pop(playerId)

    def on_open(self, ws):
        self.ws.send(dumps({ "type": "login", "class": self.plrClass }))
        print(f"Connected to the server")

    def on_close(self, ws, close_status_code, close_msg):
        print("Disconnected")

class Game:
    def __init__(self, root, canvas, plrClass, multiplayer):
        self.root = root
        self.canvas = canvas
        self.canvas.pack()
                
        self.multiplayer = multiplayer
        self.player = Player(self.canvas, plrClass, self.multiplayer, (WIDTH / 2, HEIGHT / 2))
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
                
        i = 100
        for name, data in CLASSES.items():
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
        
        CLASSES[name]["rect"] = rect
        select = tk.Button(self.canvas, text="Select", font=("Arial", 16), command= lambda: self.select(name))
        # select.place(x=x + 85, y=y + 250)
        self.canvas.create_window(x + 125, y + 250, window=select)
    
    def select(self, name):
        self.selected = name
        for char, data in CLASSES.items():
            if char == name:
                self.canvas.itemconfig(data["rect"], outline="blue")
            else:
                self.canvas.itemconfig(data["rect"], outline="black")
    
    def play(self):
        if not hasattr(self, "selected"):
            self.notify("Select a class!")
            return
        
        self.canvas.delete("all")
        multiplayer = Multiplayer(self.canvas, self.selected)
        while not hasattr(multiplayer, "playerId"):
            sleep(1)
        Game(self.root, self.canvas, self.selected, multiplayer)
    
    def notify(self, msg):
        self.canvas.itemconfig(self.notif, text=msg)
        self.canvas.after(5000, lambda: self.canvas.itemconfig(self.notif, text=""))
        


if __name__ == "__main__":
    root = tk.Tk()
    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH, bg="white")
    menu = Menu(root, canvas)
    
    # game = Game(root)
    root.mainloop()