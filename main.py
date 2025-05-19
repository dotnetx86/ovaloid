import tkinter as tk
import websocket
import maps
from time import time, sleep
from threading import Thread
from math import hypot
from json import loads, dumps
from copy import deepcopy

WIDTH, HEIGHT = 1024, 768
CLASSES = {
    "Areaer": {
        "Description": "The deafult free class. Attacks by creating an area wave damaging anyone it hits or by shooting a projectile",
        "AbilityDamage": 50,
        "AbilityCooldown": 2,
        "ProjectileSpeed": 15,
        "ProjectileDamage": 20,
        "ProjectileCooldown": 1
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
HOST = "ws://193.135.137.2:8080" or "ws://localhost:8080"

class Projectile:
    def __init__(self, game, coords: tuple, direction: tuple, shooter, multiplayer=None):
        self.game = game
        self.canvas = self.game.canvas
        self.dx, self.dy = direction
        self.shooter = shooter
        self.multiplayer = multiplayer
        self.playerId = self.multiplayer and self.multiplayer.playerId
        self.info = shooter.plrClass
        self.shape = self.canvas.create_oval(*coords, fill="blue")
        self.move()
        
    def __del__(self):
        self.canvas.delete(self.shape)

    def move(self):
        self.canvas.move(self.shape, self.dx * self.info["ProjectileSpeed"], self.dy * self.info["ProjectileSpeed"])
        x1, y1, x2, y2 = self.canvas.coords(self.shape)
        overlapping = set(self.canvas.find_overlapping(x1, y1, x2, y2))
        if self.multiplayer:
            print(overlapping)
            plr:Player = self.multiplayer and self.multiplayer.players[self.playerId]["shape"]
            if plr.shape in overlapping:
                print("aoaoao")
                plr.update_health(plr.health - self.info["ProjectileDamage"])
                del self
                return
                # self.multiplayer.send({ "type": "damage", "data": { "id": self.multiplayer.playerId, "shooter": self.shooterId } })
        if x2 < 0 or x1 > WIDTH or y2 < 0 or y1 > HEIGHT or self.game.objects[0].intersection(overlapping):
            del self
        else:
            self.canvas.after(30, self.move)

class BasePlayer:
    def __init__(self, game, coords: tuple, plrClass):
        self.game = game
        self.canvas = game.canvas
        self.plrClass = CLASSES[plrClass]
        self.step = 10
        self.shape = self.canvas.create_oval(*self.game.from_center((0, 0, 50), coords), fill="red", width=2)
        self.health = 100
        self.alive = True
        self.healthBar = self.canvas.create_oval(0, 0, 0, 0, fill="black")
        self.group = [self.shape, self.healthBar]
        
    def __del__(self):
        print("dele")
        self.canvas.delete(*(i for i in self.group))
            
    def die(self):
        print("die")
        self.alive = False
        self.canvas.delete(*(i for i in self.group))
    
    def respawn(self, coords: tuple):
        self.shape = self.canvas.create_oval(*self.game.from_center((0, 0, 50), coords), fill="red", width=2)
        self.health = 100
        self.healthBar = self.canvas.create_oval(0, 0, 0, 0, fill="black")
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
            self.canvas.coords(member, *self.game.from_center(pos, (x, y)))

    def get_center(self, coords=None):
        pos = coords or self.canvas.coords(self.shape)
        return (pos[0] + pos[2]) / 2, (pos[1] + pos[3]) / 2
    

    def area_attack(self, check=None):
        coords = self.canvas.coords(self.shape)
        attack = self.canvas.create_oval(coords, outline="red", fill="", width=3)
        self.group.append(attack)
        print(check)

        def expand(i):            
            coords = self.canvas.coords(self.shape)
            coords = (coords[0] - i, coords[1] - i, coords[2] + i, coords[3] + i)
            self.canvas.coords(attack, *coords)
            if check != None: check(coords)
            if i >= 50:
                self.group.remove(attack)
                self.canvas.delete(attack)
                return 
            self.canvas.after(10 if i < 45 else 100, expand, i + 5)

        expand(1)
        return attack

class Player(BasePlayer):
    def __init__(self, game, coords: tuple, plrClass):
        super().__init__(game, coords, plrClass)
        
        self.game.multiplayer.players[self.game.multiplayer.playerId] = { "shape": self }
        self.multiplayer = self.game.multiplayer
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
        overlap = set(self.canvas.find_overlapping(new_x, new_y, x2, y2))
        
        if 0 <= new_x and x2 <= WIDTH and 0 <= new_y and y2 <= HEIGHT and len(self.game.objects[0].intersection(overlap)) == 0:
            center = self.get_center((new_x, new_y, x2, y2))
            
            self.multiplayer.send({ "type": "move", "data": { "coords": list(center) } })
            super().move(*center)
    
    def area_attack(self):
        now = time()
        if now - self.area_last < self.plrClass["AbilityCooldown"]: return
        
        self.area_last = now
        
        self.multiplayer.send({ "type": "ability", "data": { "ability": "area" } })
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
        Projectile(self.game, (px - 5, py - 5, px + 5, py + 5), (dx, dy), self)
        
class Enemy(BasePlayer):
    def __init__(self, game, coords: tuple, plrClass):
        print("crea")
        super().__init__(game, coords, plrClass)
        
    def area_attack(self):
        self.tagged = False
        def check(coords):
            if self.tagged: return
            plr: Player = self.game.player
            overlapping = self.canvas.find_overlapping(*coords)
            if plr.shape in overlapping:
                plr.update_health(plr.health - self.plrClass["AbilityDamage"])
                self.tagged = True
                print("yay")
        
        super().area_attack(check)
        
class Multiplayer:
    def __init__(self, game):
        self.game = game
        self.canvas = self.game.canvas
        self.plrClass = game.plrClass
        self.players = {}
                    
        self.ws = websocket.WebSocketApp(HOST,
                            on_open=self.on_open,
                            on_message=self.on_message,
                            on_close=self.on_close)
        try:
            Thread(target=self.ws.run_forever, daemon=True).start()
        except Exception as err:
            print("websocket error:")
            print(err)
            
    def close(self):
        self.ws.close()        

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
                self.game.load_map(maps.maps[data["round"]["map"]])
                for plrId, plrData in data["players"].items():
                    if plrId == playerId:
                        continue
                    
                    plr = Enemy(self.game, tuple(plrData["coords"]), plrData["class"])
                    self.players[plrId] = { "shape": plr }
            case "new":
                plr = Enemy(self.game, tuple(data["coords"]), data["class"])
                self.players[playerId] = { "shape": plr }
            case "respawn":
                print("resp")
                plr: BasePlayer = self.players[playerId]["shape"]
                plr.respawn(tuple(data["coords"]))
            case "move":
                plr: Enemy = self.players[playerId]["shape"]
                plr.move(*data["coords"])
            case "projectile":
                proj = Projectile(self.game, tuple(data["coords"]), tuple(data["direction"]), self.players[playerId]["shape"], self)
            case "ability":
                print(msg)
                plr: Enemy = self.players[playerId]["shape"]
                match data["ability"]:
                    case "area":
                        print("L()")
                        plr.area_attack()
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
    def __init__(self, root, canvas: tk.Canvas, plrClass):
        self.root = root
        self.canvas = canvas
        self.canvas.pack()
                
        self.objects = [set(), set()]
        self.plrClass = plrClass
        
        self.multiplayer = Multiplayer(self)
        while not hasattr(self.multiplayer, "playerId"):
            sleep(1)
        
        self.player = Player(self, (WIDTH / 2, HEIGHT / 2), self.plrClass)
        self.holding_keys = set()
        
        
        self.root.bind("<KeyPress>", self.keypress)
        self.root.bind("<KeyRelease>", self.keyrelease)
        
        # Enemy(canvas, WIDTH / 2, 150)

        self.move_loop()
    
    def leave(self):
        print("va")
        self.multiplayer.close()
        self.player.die()
        
        self.canvas.delete("all")
        self.objects = None
        
        self.root.unbind("<KeyPress>")
        self.root.unbind("<KeyRelease>")
        
        Menu(self.root, self.canvas)
        
    def load_map(self, layout):
        for obj in layout:
            print(obj)
            self.create_object(obj)
            print(obj)
            if obj.get("mirrored"):
                mask = [WIDTH, HEIGHT, WIDTH, HEIGHT][:len(obj["coords"])]
                obj["coords"] = list(map(lambda x, y: abs(y - x), obj["coords"], [item if item in obj["mirrored"] else 0 for item in mask]))
                self.create_object(obj)
            
    
    def create_object(self, obj):
        obj = deepcopy(obj)
        args = [*obj["coords"]]
        kwargs = { "fill": obj["fill"] }
        shape = None
        match obj["shape"]:
            case "rect":
                shape = self.canvas.create_rectangle(*args, **kwargs)
            
            case "circle":
                args = [self.from_center(obj["radius"], obj["coords"])]
                kwargs["outline"] = ""
                shape = self.canvas.create_oval(*args, **kwargs)
        
        if obj.get("tags") and "NoCollision" in obj["tags"]:
            self.objects[1].add(shape)
        else:
            self.objects[0].add(shape)
        
    
    def from_center(self, pos, center):
        if type(pos) in [int, float]:
            r = pos
        else:
            r = (pos[2] - pos[0]) / 2
        
        return center[0] - r, center[1] - r, center[0] + r, center[1] + r
    
    def move_loop(self):
        if self.objects == None:
            return
        
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
        self.canvas.after(20, self.move_loop)

    def keypress(self, event):
        print(event)
        self.holding_keys.add(event.keysym.lower())
        match event.keysym.lower():
            case "q":
                if self.plrClass == "Dasher":
                    self.player.dash()
            case "f":
                if self.plrClass == "Areaer":
                    self.player.area_attack()
            case "escape":
                self.leave()
                

    def keyrelease(self, event):
        self.holding_keys.discard(event.keysym.lower())
        
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
        
        self.notif = self.canvas.create_text(WIDTH / 2, HEIGHT - 100, font=("Arial", 16))
        
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
        # multiplayer = Multiplayer(self.canvas, self.selected)
        # while not hasattr(multiplayer, "playerId"):
        #     sleep(1)
        Game(self.root, self.canvas, self.selected)
    
    def notify(self, msg):
        self.canvas.itemconfig(self.notif, text=msg)
        self.canvas.after(5000, lambda: self.canvas.itemconfig(self.notif, text=""))
        


if __name__ == "__main__":
    root = tk.Tk()
    canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH, bg="white")
    menu = Menu(root, canvas)
    
    # game = Game(root)
    root.mainloop()