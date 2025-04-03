import random
import socket
import time
import pygame
import psycopg2
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from russian_names import RussianNames
import math
from logtail import LogtailHandler
from loguru import logger

logtail_handler = LogtailHandler(source_token="PS1hA1zRVrK55eXdHBtwzQ6p")

logger.add(logtail_handler, level="DEBUG")

main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.bind(("localhost", 10000))
main_socket.setblocking(False)
main_socket.listen(5)
print("сервер запущен")

engine = create_engine("postgresql+psycopg2://postgres:grem121grem@localhost/agario")
Session = sessionmaker(bind=engine)
Base = declarative_base()
s = Session()

width = 300
height = 300
width2 = 4000
height2 = 4000
center_x = width2 // 2
center_y = height2 // 2
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("admin")
clock = pygame.time.Clock()
FPS = 100


def filter(vector: str):
    first = None
    for num, simv in enumerate(vector):
        if simv == "<":
            first = num
        if simv == ">" and first is not None:
            second = num
            result = vector[first + 1: second].split(",")
            result = list(map(float, result))
            return result
    return ""


def filter_color(info):
    first = None
    for num, simv in enumerate(info):
        if simv == "<":
            first = num
        if simv == ">" and first is not None:
            second = num
            result = info[first + 1: second].split(",")
            return result
    return ""


class Player(Base):
    __tablename__ = "Players"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    address = Column(String)
    x = Column(Integer, default=500)
    y = Column(Integer, default=500)
    size = Column(Integer, default=50)
    errors = Column(Integer, default=0)
    abs_speed = Column(Integer, default=1)
    speed_x = Column(Integer, default=0)
    speed_y = Column(Integer, default=0)
    color = Column(String, default="red")
    w_vision = Column(Integer, default=800)
    h_vision = Column(Integer, default=600)

    def __init__(self, name, address):
        self.name = name
        self.address = address


Base.metadata.create_all(engine)


class Local_player:
    def __init__(self, id, name, sock, address):
        self.id = id
        self.name = name
        self.address = address
        self.sock = sock
        self.db: Player = s.get(Player, self.id)
        self.x = 500
        self.y = 500
        self.L = 1
        self.size = 50
        self.errors = 0
        self.abs_speed = 1
        self.speed_x = 0
        self.speed_y = 0
        self.color = "red"
        self.w_window = 800
        self.h_window = 600
        self.w_vision = 800
        self.h_vision = 600

    def load(self):
        self.x = self.db.x
        self.y = self.db.y
        self.size = self.db.size
        self.errors = self.db.errors
        self.abs_speed = self.db.abs_speed
        self.speed_x = self.db.speed_x
        self.speed_y = self.db.speed_y
        self.color = self.db.color
        self.w_vision = self.db.w_vision
        self.h_vision = self.db.h_vision
        return self

    def sync(self):
        self.db.x = self.x
        self.db.x = self.y
        self.db.size = self.size
        self.db.errors = self.errors
        self.db.abs_speed = self.abs_speed
        self.db.speed_x = self.speed_x
        self.db.speed_y = self.speed_y
        self.db.color = self.color
        self.db.w_vision = self.w_vision
        self.db.h_vision = self.h_vision
        s.merge(self.db)
        s.commit()

    def update(self):
        if self.x - self.size <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        elif self.x + self.size >= width2:
            if self.speed_x <= 0:
                self.x += self.speed_x
        else:
            self.x += self.speed_x

        if self.y - self.size <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        elif self.y + self.size >= height2:
            if self.speed_y <= 0:
                self.y += self.speed_y
        else:
            self.y += self.speed_y

        if self.size >= self.w_vision/4 or self.size >= self.h_vision/4:
            if self.w_vision <= width2 or self.h_vision <= height2:
                self.L *= 2
                self.w_vision = self.w_window * self.L
                self.h_vision = self.h_window * self.L


    def change_speed(self, vector):
        vector = filter(vector)
        if vector[0] == 0 and vector[1] == 0:
            self.speed_x = self.speed_y = 0
        else:
            vector = vector[0] * self.abs_speed, vector[1] * self.abs_speed
            self.speed_x = vector[0]
            self.speed_y = vector[1]

    def new_speed(self):
        self.abs_speed = 10 / self.size ** 0.5


class Food:
    def __init__(self, x, y, size, color, id):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.id = id


players = {

}

foods = []

mob_count = 70

mob_color = [
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown", "grey", "black", "white", "cyan", "magenta",
    "lime", "teal", "indigo", "violet", "gold", "silver", "maroon", "olive", "navy", "turquoise", "coral", "salmon",
    "wheat", "lavender", "beige", "khaki", "plum", "orchid", "crimson", "chocolate", "skyblue", "darkblue",
    "darkgreen", "darkred", "darkgrey", "lightblue", "lightgreen", "lightgrey", "lightpink", "lightsalmon",
    "lightseagreen", "lightskyblue", "lightsteelblue", "palegreen", "palevioletred", "powderblue", "seagreen",
    "springgreen", "steelblue", "tan", "thistle", "tomato", "violetred", "yellowgreen"
]
mob_names = RussianNames(count=40, patronymic=False, surname=False, rare=True)
mob_names = list(set(mob_names))

for mob2 in range(mob_count):
    mob = Player(random.choice(mob_names), None)
    mob.x, mob.y = random.randint(0, width2), random.randint(0, height2)
    mob.speed_x, mob.speed_y = random.randint(-1, 1), random.randint(-1, 1)
    mob.color = random.choice(mob_color)
    mob.size = 35
    s.add(mob)
    s.commit()

    local_mob = Local_player(mob.id, mob.name, None, None).load()
    players[mob.id] = local_mob

food_count = 700

for food2 in range(food_count):
    x, y = random.randint(0, width2), random.randint(0, height2)
    color = random.choice(mob_color)
    size = 10

    food = Food(x, y, size, color, id)
    foods.append(food)

tick = -1

run = True
while run:
    clock.tick(FPS)
    tick += 1
    if tick % 200 == 0:
        try:
            new_socket, address = main_socket.accept()
            print(f"подключился {address}")
            new_socket.setblocking(False)
            get_data = new_socket.recv(1024).decode()
            player = Player("name", address)
            if get_data.startswith("color"):
                get_data = filter_color(get_data[6:])
                player.name, player.color = get_data

            s.merge(player)
            s.commit()

            addr = f"({address[0]},{address[1]})"
            data = s.query(Player).filter(Player.address == addr)
            for p in data:
                user = Local_player(p.id, "name", new_socket, addr).load()
                players[p.id] = user
        except BlockingIOError:
            pass

    if tick % 10000 == 0:
        need = mob_count - len(players)
        if need > 35:
            for i in range(1):
                mob = Player(random.choice(mob_names), None)
                spawn = random.choice(foods)
                foods.remove(spawn)
                mob.x, mob.y = spawn.x, spawn.y
                mob.speed_x, mob.speed_y = random.randint(-1, 1), random.randint(-1, 1)
                mob.color = random.choice(mob_color)
                mob.size = 35

                s.add(mob)
                s.commit()

                local_mob = Local_player(mob.id, mob.name, None, None).load()
                players[mob.id] = local_mob
                local_mob.new_speed()
            logger.info(f"Появилось {need} мобов")
            need = 0

    if tick % 3400 == 0:
        need_food = food_count - len(foods)
        for i in range(need_food//2):
            x, y = random.randint(0, width2), random.randint(0, height2)
            color = random.choice(mob_color)
            size = 10

            food = Food(x, y, size, color, id)
            foods.append(food)
        logger.info(f"Появилось {need_food} еды")

    for id in list(players):
        if players[id].sock is not None:
            try:
                data = players[id].sock.recv(1024).decode()
                players[id].change_speed(data)
            except:
                pass
        else:
            if tick % 250 == 0:
                vector = f"<{random.randint(-1, 1)},{random.randint(-1, 1)}>"
                players[id].change_speed(vector)

    bacteries = {}
    for id in list(players):
        bacteries[id] = []

    pairs = list(players.items())

    for p1 in range(0, len(pairs)):
        for food in foods:
            hero: Player = pairs[p1][1]
            dist_x = food.x - hero.x
            dist_y = food.y - hero.y

            if abs(dist_x) <= hero.w_vision // 2 + food.size and abs(dist_y) <= hero.h_vision // 2 + food.size:
                dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
                if dist < hero.size:
                    hero.size = (hero.size ** 2 + food.size ** 2) ** 0.5
                    hero.new_speed()
                    food.size = 0
                    foods.remove(food)

                if hero.sock is not None and food.size != 0:
                    x_ = str(round(dist_x / hero.L))
                    y_ = str(round(dist_y / hero.L))
                    size_ = str(round(food.size / hero.L))
                    color_ = food.color
                    data_t = x_ + " " + y_ + " " + size_ + " " + color_
                    bacteries[hero.id].append(data_t)

        for p2 in range(p1 + 1, len(pairs)):
            hero_1: Player = pairs[p1][1]
            hero_2: Player = pairs[p2][1]

            dist_x = hero_2.x - hero_1.x
            dist_y = hero_2.y - hero_1.y

            if abs(dist_x) <= hero_1.w_vision // 2 + hero_2.size and abs(dist_y) <= hero_1.h_vision // 2 + hero_2.size:
                dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
                if dist < hero_1.size and hero_1.size > hero_2.size * 1.3:
                    hero_1.size = (hero_1.size ** 2 + hero_2.size ** 2) ** 0.5
                    hero_2.size, hero_2.speed_x, hero_2.speed_y = 0, 0, 0
                    hero_1.new_speed()
                if hero_1.sock is not None:
                    x_ = str(round(dist_x / hero_1.L))
                    y_ = str(round(dist_y / hero_1.L))
                    size_ = str(round(hero_2.size / hero_1.L))
                    color_ = hero_2.color
                    name_ = hero_2.name
                    data_t = x_ + " " + y_ + " " + size_ + " " + color_ + " " + name_
                    bacteries[hero_1.id].append(data_t)

            if abs(dist_x) <= hero_2.w_vision // 2 + hero_1.size and abs(dist_y) <= hero_2.h_vision // 2 + hero_1.size:
                dist = (dist_x ** 2 + dist_y ** 2) ** 0.5
                if dist < hero_2.size and hero_2.size > hero_1.size * 1.3:
                    hero_2.size = (hero_2.size ** 2 + hero_1.size ** 2) ** 0.5
                    hero_1.size, hero_1.speed_x, hero_1.speed_y = 0, 0, 0
                    hero_2.new_speed()
                if hero_2.sock is not None:
                    x_ = str(round(-dist_x / hero_2.L))
                    y_ = str(round(-dist_y / hero_2.L))
                    size_ = str(round(hero_1.size / hero_2.L))
                    color_ = hero_1.color
                    name_ = hero_1.name
                    data_t = x_ + " " + y_ + " " + size_ + " " + color_ + " " + name_
                    bacteries[hero_2.id].append(data_t)

    for id in list(players):
        r_ = str(round(players[id].size / players[id].L))
        x_ = str(round(players[id].x / players[id].L))
        y_ = str(round(players[id].y / players[id].L))
        L_ = str(round(players[id].L))
        bacteries[id] = [r_ + " " + x_ + " " + y_ + " " + L_] + bacteries[id]
        bacteries[id] = "<" + ",".join(bacteries[id]) + ">"

    for id in list(players):
        if players[id].sock is not None:
            try:
                players[id].sock.send(bacteries[id].encode())
            except:
                players[id].errors += 1

    for id in list(players):
        if players[id].size == 0 or players[id].errors >= 700:
            if players[id].sock is not None:
                players[id].sock.close()
            del players[id]
            s.query(Player).filter(Player.id == id).delete()
            s.commit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    screen.fill("black")
    for id in list(players):
        player = players[id]
        x = player.x * width // width2
        y = player.y * height // height2
        size = player.size * width // width2
        pygame.draw.circle(screen, player.color, (x, y), size)

    for id in list(players):
        player = players[id]
        player.update()

    pygame.display.update()

pygame.quit()
main_socket.close()
s.query(Player).delete()
s.commit()