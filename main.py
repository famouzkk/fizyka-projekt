from dataclasses import dataclass
from vec import Vec
import arcade
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Projekt"
CHARGES_FILENAME = "stationary.txt"
OUTPUT_FILENAME = "out.txt"
SIMULATION_OUTPUT_FILENAME = "simulation_out.txt"
DELTA_T = 0.001
K = 9 * 10e9


@dataclass
class StationaryCharge:
    position: Vec = Vec(0, 0)
    q: float = 0.0


class MovableCharge:
    position: Vec
    velocity: Vec 
    acceleration: Vec
    q: float
    m: float

    def __init__(self):
        self.position = Vec(0, 0)
        self.velocity = Vec(0, 0)
        self.acceleration = Vec(0, 0)
        self.q = 0.0
        self.m = 0.0

    def get_input_from_user(self):
        self.velocity.x = float(input("Podaj Vx: ")) #0.01 
        self.velocity.y = float(input("Podaj Vy: ")) #0.02 
        self.position.x = int(input("Podaj x poczatkowe: ")) #50 
        self.position.y = int(input("Podaj y poczatkowe: ")) #50 
        self.q = float(input("Podaj q: ")) #0.0001 
        self.m = float(input("Podaj m: ")) #1 

    def calculate_acc_at(self, pos: Vec, f) -> Vec:
        return (self.q * f.grid[int(pos.x)][int(pos.y)].e) / self.m


class FieldCell:
    e: Vec
    v: float
    is_stationary: bool
    def __init__(self, e: Vec, v: float, is_stationary: bool):
        self.e = e
        self.v = v
        self.is_stationary = is_stationary


class Field:
    w: int
    h: int
    grid: list[list[FieldCell]]
    stationary_charges: list[StationaryCharge]

    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self.grid = [[None] * self.h for _ in range(self.w)]
        self.stationary_charges = []

    def calculate_intensity(self, x: int, y: int) -> tuple[Vec, float]:
        intensity = Vec(0, 0)
        potential = 0.0
        for sc in self.stationary_charges:
            f_cell_pos = Vec(x, y)
            r_vec = f_cell_pos - sc.position
            r = abs(r_vec)  
            if r == 0.0: # ladunek staly
                return Vec(0, 0), 0.0, True
            intensity += (sc.q / pow(r, 3)) * r_vec
            potential += sc.q / r
        return intensity * K, potential * K, False

    def populate_field_values(self) -> None:
        for y_cord in range(self.h):
            for x_cord in range(self.w):
                self.grid[x_cord][y_cord] = FieldCell(*self.calculate_intensity(x_cord, y_cord))                

    def save_field_to_file(self, filename : str) -> None:
        with open(filename, "w") as f:
            for y_cord in range(self.h):
                for x_cord in range(self.w):
                    cell = self.grid[x_cord][y_cord]
                    q = 0
                    if cell.is_stationary == True:
                        found = [s for s in self.stationary_charges if s.position == Vec(x_cord, y_cord)]
                        if found:
                            q = found[0].q
                    f.write(f"{x_cord} {y_cord} {q} {cell.e.x} {cell.e.y} {abs(cell.e)} {cell.v}\n")

    def read_data_from_file(self, filename: str):
        with open(filename) as f:
            number_of_charges = int(f.readline())
            for _ in range(0, number_of_charges):
                x, y, q = list(map(float, f.readline().split(" ")))
                self.stationary_charges.append(StationaryCharge(Vec(x, y), q))


class Simulation:
    delta_t: float
    movable: MovableCharge
    time_elapsed: float
    field = Field
    output_buffer = str

    def __init__(self, delta_t: float):
        self.delta_t = delta_t
        self.time_elapsed = 0
        self.movable = MovableCharge()
        self.field = Field(256, 256)
        self.set_up_field()
        self.movable.get_input_from_user()
        self.output_buffer = ""
        self.movable.acceleration = self.movable.calculate_acc_at(self.movable.position, self.field)
    
    def set_up_field(self) -> None:
        self.field.read_data_from_file(CHARGES_FILENAME)
        self.field.populate_field_values()
        self.field.save_field_to_file(OUTPUT_FILENAME)

    def simulate(self):
        self.movable.position = self.movable.position + self.movable.velocity * self.delta_t + 0.5 * self.movable.acceleration * math.pow(self.delta_t, 2)
        if not self.out_of_boundaries() and not self.collision_with_stationary():
            self.movable.velocity += self.movable.acceleration * self.delta_t
            self.movable.acceleration = self.movable.calculate_acc_at(self.movable.position, self.field)
            print(f"T: {self.time_elapsed} POS: {self.movable.position} VEL: {self.movable.velocity} ACC: {self.movable.acceleration}")
            self.output_buffer += f"{self.time_elapsed} {self.movable.position.x} {self.movable.position.y} {self.movable.velocity.x} {self.movable.velocity.y} {self.movable.acceleration.x} {self.movable.acceleration.y}" + "\n"
            self.time_elapsed += self.delta_t

    def out_of_boundaries(self):
        if self.movable.position.x >= self.field.w - 1 or self.movable.position.x < 0 or \
            self.movable.position.y >= self.field.h - 1 or self.movable.position.y < 0:
            print("Out of boundaries!")
            return True
        return False
    
    def collision_with_stationary(self):
        if len([s for s in self.field.stationary_charges if self.movable.position == s.position]) == 0:
            return False
        else:
            print("Colision with stationary charge!")
            return True
            
    
    def draw_stationary_charges(self, scale: Vec):
        for s in self.field.stationary_charges:
            color = arcade.color.RED if s.q > 0 else arcade.color.BABY_BLUE
            arcade.draw_circle_filled(s.position.x * scale.x, s.position.y * scale.y, 5., color)
    
    def draw_moving_charge(self, scale: Vec):
        arcade.draw_circle_filled(self.movable.position.x * scale.x, self.movable.position.y * scale.y, 4., arcade.color.WHITE_SMOKE)

    def draw(self, scale: Vec):
        arcade.start_render()
        self.draw_stationary_charges(scale)
        self.draw_moving_charge(scale)
    
    def save_simulation_to_file(self, filename):
        with open(filename, "w") as f:
            f.write(self.output_buffer)
        

                
class Arcade(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.s = Simulation(DELTA_T)
        self.scale_x = width / self.s.field.w
        self.scale_y = height / self.s.field.h
        arcade.set_background_color(arcade.color.BLACK)


    def on_update(self, delta_time):
        self.s.simulate()
        pass

    def on_draw(self):
        self.clear()
        self.s.draw(Vec(self.scale_x, self.scale_y))

    def on_key_press(self, key: int, modifier: int):
        if key == arcade.key.ESCAPE:
            self.s.save_simulation_to_file(SIMULATION_OUTPUT_FILENAME)




Arcade(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
arcade.run()
