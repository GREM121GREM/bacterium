import socket
import time
import pygame
import math
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox


from loguru import logger

name = ""
color = ""
buffer = 1024
window = tk.Tk()
window.title("Меню")
window.geometry("600x300")


def get_color(event):
    global color
    color = color_combo.get()
    window.configure(bg=color)
    title_label.configure(bg=color)
    input_frame.configure(bg=color)
    name_label.configure(bg=color)
    color_label.configure(bg=color)


def start():
    global name
    name = name_entry.get()
    if name and color:
        window.destroy()
        window.quit()
        logger.info(f"Пользователь ввел имя: {name}")
        logger.info(f"Пользователь выбрал цвет: {color}")
    else:
        logger.warning("Пользователь не выбрал цвет или не написал имя")
        tk.messagebox.showerror("Ошибка", "Вы не ввели имя или не выбрали цвет")



def find(info):
    global buffer
    first = None
    for num, simv in enumerate(info):
        if simv == "<":
            first = num
        if simv == ">" and first is not None:
            second = num
            result = info[first + 1: second]
            return result
    buffer = int(buffer * 2)
    return ""


def name_bact(x, y, radius, name):
    font = pygame.font.Font(None, int(radius // 2))
    text = font.render(name, True, "black")
    rect = text.get_rect(center=(x, y))
    screen.blit(text, rect)


def draw_bact(data: list[str]):
    for num, bact in enumerate(data):
        data = bact.split(" ")
        x = center_screen[0] + int(data[0])
        y = center_screen[1] + int(data[1])
        size = int(data[2])
        color = data[3]
        pygame.draw.circle(screen, color, (x, y), size)

        if len(data) == 5:
            name_bact(x, y, size, data[4])


class Grid:
    def __init__(self, screen, color):
        self.screen = screen
        self.color = color
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size

    def update(self, param):
        x, y, L = param
        self.size = self.start_size // L
        self.x = -self.size + (-x) % self.size
        self.y = -self.size + (-y) % self.size

    def draw(self):
        for i in range(width // self.size + 2):
            pygame.draw.line(self.screen, self.color, (self.x + i * self.size, 0),
                             (self.x + i * self.size, height), 1)
        for i in range(height // self.size + 2):
            pygame.draw.line(self.screen, self.color, (0, self.y + i * self.size),
                             (width, self.y + i * self.size), 1)



# Заголовок
title_label = tk.Label(window, text="agar.io", font=("Arial", 24))
title_label.pack(pady=20)

# Фрейм для полей ввода
input_frame = tk.Frame(window)
input_frame.pack()

# Поле ввода имени
name_label = tk.Label(input_frame, text="NAME:", font=("Arial", 14))
name_label.grid(row=0, column=0, padx=5, pady=5)
name_entry = tk.Entry(input_frame, width=20)
name_entry.grid(row=0, column=1, padx=5, pady=5)


# Поле выбора цвета
color_label = tk.Label(input_frame, text="Color:", font=("Arial", 14))
color_label.grid(row=1, column=0, padx=5, pady=5)
color_var = tk.StringVar(value="red")  # Начальное значение - красный
color_combo = ttk.Combobox(input_frame, textvariable=color_var, values=["red", "blue", "green", "yellow"])
color_combo.bind("<<ComboboxSelected>>", get_color)
color_combo.grid(row=1, column=1, padx=5, pady=5)

# Кнопка Play
play_button = tk.Button(window, text="PLAY", width=20, command=start)
play_button.pack(pady=20)

window.mainloop()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.connect(("localhost", 10000))
sock.send(f"color:<{name},{color}>".encode())
pygame.init()

width = 800
height = 600
center_screen = (width // 2, height // 2)
old = (0, 0)
radius = 50

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("agar.io")

grid = Grid(screen, "grey")

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if pygame.mouse.get_focused():
            pos = pygame.mouse.get_pos()
            vector = pos[0] - center_screen[0], pos[1] - center_screen[1]
            v_len = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
            vector = vector[0] / v_len, vector[1] / v_len
            if v_len <= radius:
                vector = 0, 0

            if vector != old:
                old = vector
                msg = f"<{vector[0]},{vector[1]}>"
                sock.send(msg.encode())

    message = sock.recv(buffer).decode()
    message = find(message).split(",")

    font = pygame.font.Font(None, int(radius // 1.5))

    text_surface = font.render(name, True, "black")
    text_rect = text_surface.get_rect(center=(center_screen[0], center_screen[1]))

    screen.fill("white")

    if message != [""]:
        param = list(map(int, message[0].split(" ")))
        radius = param[0]
        grid.update(param[1:])
        grid.draw()
        x, y, L = param[1], param[2], param[3]
        pygame.draw.rect(screen, "red", (center_screen[0] - x, center_screen[1] - y,
                                         round(4000 / L), round(4000 / L)), 3)
        draw_bact(message[1:])

    pygame.draw.circle(screen, color, center_screen, radius)
    screen.blit(text_surface, text_rect)

    pygame.display.update()

pygame.quit()