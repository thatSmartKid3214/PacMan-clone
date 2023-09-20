#Game stuff Library
import pygame
import xml.etree.ElementTree as ET
import json
import math
import os
pygame.init()

#functions
def swap_color(img,old_c,new_c):
    img.set_colorkey(old_c)
    surf = img.copy()
    surf.fill(new_c)
    surf.blit(img,(0,0))
    surf.set_colorkey((0,0,0))
    return surf

def perfect_outline(img, surf, loc, color, colorkey=(0,0,0), colorkey2=(0,0,0)):
    img.set_colorkey(colorkey)
    mask = pygame.mask.from_surface(img)
    mask_surf = mask.to_surface(setcolor=color)
    mask_surf.set_colorkey((0,0,0))
    surf.blit(mask_surf,(loc[0]-1,loc[1]))
    surf.blit(mask_surf,(loc[0]+1,loc[1]))
    surf.blit(mask_surf,(loc[0],loc[1]-1))
    surf.blit(mask_surf,(loc[0],loc[1]+1))

def blit_center(surf, other_surf, pos):
    x = int(other_surf.get_width()/2)
    y = int(other_surf.get_height()/2)
    surf.blit(other_surf, (pos[0]-x,pos[1]-y))

#math stuff
def angle_from_points(point1,point2,scroll,offset,degrees):
    if degrees == False:
        return math.atan2(point1[1] - (int(point2[1])-scroll[1] + offset[1]), point1[0] - (int(point2[0])-scroll[0] + offset[0]))
    else:
        return math.degrees(math.atan2(point1[1] - (int(point2[1])-scroll[1] + offset[1]), point1[0] - (int(point2[0])-scroll[0] + offset[0])))

def normalize_vec(vec):
    # get the magnitude
    mag = math.sqrt( (vec[0])**2 + (vec[1])**2 )
    new_vec = [ vec[0]/mag, vec[1]/mag ]
    return new_vec

def line_to_line_vec_collide(start,end,origin,end2):
    P = pygame.math.Vector2(start)
    R = (pygame.math.Vector2(end)-P)
    Q = pygame.math.Vector2(origin)
    S = (pygame.math.Vector2(end2)-Q)
    d = R.dot((S.y, -S.x))
    if d == 0:
        return
    t = (Q-P).dot((S.y, -S.x))/d
    u = (Q-P).dot((R.y, -R.x))/d
    if 0 <= t <= 1 and 0 <= u <= 1:
        point = P+(R*t)
        return [point.x,point.y]
    return None

def line_to_rect_collide(start,end,rect):
    #Line points of the rect
    #Basically lines going around the border of the rect
    r_lines = {"L1":(rect.topleft,rect.bottomleft),"L2":(rect.topleft,rect.topright),"L3":(rect.topright, rect.bottomright),"L4":(rect.bottomleft,rect.bottomright)}
    for line in r_lines:
        point = line_to_line_vec_collide(start,end,r_lines[line][0],r_lines[line][1])
        if point != None:
            return [point,True]
    return [[0,0],False]

def rect_with_circle(rect, c_radius, c_pos):
    dis = dis_between_points(rect.topleft, c_pos)
    if dis < c_radius:
        return True
    
    if dis_between_points(rect.topright, c_pos) < c_radius:
        return True

    return False

def rotate_on_pivot(image, angle, pivot: pygame.Vector2, pos: pygame.Vector2):
    surf = pygame.transform.rotate(image, angle)
    offset = pivot + (pos - pivot).rotate(-angle)
    rect = surf.get_rect(center = offset)
    
    return surf, rect


def dis_between_points(p1, p2):
    dis = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
    return dis

def dis_between_points_opt(p1, p2):
    dis = (p2[0]-p1[0])**2 + (p2[1]-p1[1])**2
    return dis

def rotate(point, angle, origin, Round = False):
    x = point[0] - origin[0]
    y = point[1] - origin[1]
    
    Cos = math.cos(math.radians(angle))
    Sin = math.sin(math.radians(angle))

    if Round == True:
        xPrime = (round(x * Cos)) - (round(y * Sin))
        yPrime = (round(x * Sin)) + (round(y * Cos))
    else:
        xPrime = (x * Cos) - (y * Sin)
        yPrime = (x * Sin) + (y * Cos)
        
    xPrime += origin[0]
    yPrime += origin[1]
    newPoint = [xPrime, yPrime]
    return newPoint

def find_min_and_max(rect, angle, axis, normal):
    a = (pygame.math.Vector2(rotate(rect.topleft, angle, rect.center))).dot(normal)
    b = (pygame.math.Vector2(rotate(rect.topright, angle, rect.center))).dot(normal)
    c = (pygame.math.Vector2(rotate(rect.bottomleft, angle, rect.center))).dot(normal)
    d = (pygame.math.Vector2(rotate(rect.bottomright, angle, rect.center))).dot(normal)

    projections = [a,b,c,d]

    Min = projections[0]
    for proj in projections:
        if proj < Min:
            Min = proj
    
    Max = projections[0]
    for proj in projections:
        if proj > Max:
            Max = proj
    
    return [Min, Max]

def SAT_Collision(A, B, rotA, rotB):
    #X axis
    Axis1 = rotate([1,0], rotA, [0,0])
    Axis2 = rotate([1,0], rotB, [0,0])

    #Y axis
    Axis3 = rotate([0,1], rotA, [0,0])
    Axis4 = rotate([0,1], rotB, [0,0])

    x_axis = [Axis1, Axis2]
    y_axis = [Axis3, Axis4]

    axis_check = [False,False,False,False]
    #check x-axis
    for i, axis in enumerate(x_axis):
        Amin, Amax = find_min_and_max(A, rotA, 'x', axis)
        Bmin, Bmax = find_min_and_max(B, rotB, 'x', axis)

        if Bmin < Amax and Bmax > Amin:
            axis_check[i] = True
    
    #check y-axis
    for i, axis in enumerate(y_axis):
        j = i + 2

        Amin, Amax = find_min_and_max(A, rotA, 'y', axis)
        Bmin, Bmax = find_min_and_max(B, rotB, 'y', axis)

        if Bmin < Amax and Bmax > Amin:
            axis_check[j] = True
    
    collision = (axis_check == [True,True,True,True])
    return collision


#Image manager
VALID_IMAGE_FORMATS = ["png", "jpg"]

class ImageManager:
    
    @staticmethod
    def load(path, colorkey=None):
        """
        load an image params:
        path -> path to the image being loaded
        colorkey -> If it is not None, sets a colorkey to the image
        """
        img = pygame.image.load(path).convert()
        if colorkey:
            img.set_colorkey(colorkey)
        return img
    
    @staticmethod
    def load_image_scale(path,scale,colorkey=None):
        img = pygame.image.load(path).convert()
        img = pygame.transform.scale(img, (scale, scale))
        if colorkey:
            img.set_colorkey(colorkey)
        return img

    @staticmethod
    def get_image(image,x,y,w,h,scale):
        surf = pygame.Surface((w,h))
        surf.set_colorkey((0,0,0))
        surf.blit(image, (0,0), (x,y,w,h))
        return pygame.transform.scale(surf, (w*scale, h*scale))

    @staticmethod
    def load_folder(folder_path):
        folder_list = os.listdir(folder_path)
        img_list = []
        for file in folder_path:
            if file.split('.')[1] in VALID_IMAGE_FORMATS:
                img_list.append(pygame.image.load(f"{folder_path}.{file}").convert())

        return img_list


class Timer:
    def __init__(self, cooldown):
        self.var = True
        self.time = None
        self.cooldown = cooldown*1000

    def set_time(self):
        self.time = pygame.time.get_ticks()

    def set_var(self):
        self.var = False
    
    def set(self):
        self.set_time()
        self.set_var()

    def timed_out(self):
        return self.var

    def reset(self):
        self.var = True
        self.time = None
    
    def set_cooldown(self, cooldown):
        self.cooldown = cooldown*1000

    def update(self):
        if self.var == False:
            current_time = pygame.time.get_ticks()

            if current_time - self.time >= self.cooldown:
                self.var = True

class JSON_Handler:
    def __init__(self):
        self.files = {}

    def load(self, file_path, file_key):
        with open(file_path) as file:
            info = json.load(file)
            self.files[file_key] = info
        return info

    def write(self, data,file_path):
        with open(file_path, "r") as file:
            json.dump(data,file_path)
            file.close()

    def get_data(self,file_key):
        return self.files[file_key]

    def del_file(self,file_key,return_data=False):
        if return_data == False:
            del self.files[file_key]
        else:
            data = self.files[file_key]
            del self.files[file_key]
            return data

#Physics and collisions
def collision_test(rect,rect_group):
    hit_list = []
    for other_rect in rect_group:
        if rect.colliderect(other_rect):
            hit_list.append(other_rect)

    return hit_list

class Physics:
    def __init__(self,x,y,w,h):
        self.rect = pygame.Rect(x,y,w,h)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def movement(self,movement,tiles):
        #x-axis(tiles)
        self.x += movement[0]
        self.rect.x = int(self.x)
        collision_types = {"right":False,"left":False,"up":False,"down":False}
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                collision_types["right"] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                collision_types["left"] = True
            self.x = self.rect.x
            
        #y-axis(tiles)
        self.y += movement[1]
        self.rect.y = int(self.y)
        hit_list = collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types["down"] = True
            if movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types["up"] = True
            self.y = self.rect.y

        return collision_types

    def change_rect(self,rect):
        self.rect = rect

class Entity:
    def __init__(self,x,y,width,height,vel,jump,anim_obj=None):
        # Entity setup
        self.x = x
        self.y = y
        self.w = width
        self.h = height
        self.rect = pygame.Rect(self.x,self.y,self.w,self.h)
        self.physics_obj = Physics(self.rect.x,self.rect.y,self.rect.width,self.rect.height)
        self.collisions = {"top":False,"bottom":False,"right":False,"left":False}

        #movement variables
        self.vel = vel
        self.jump_height = jump
        self.right = False
        self.left = False
        self.up = False
        self.down = False
        self.gravity = 0
        self.vel_y = 0
        self.vel_x = 0

        self.state = ""
        self.image = pygame.Surface((self.rect.width,self.rect.height))
        self.image.fill((255, 255, 255))
        if anim_obj == None:
            self.animation = Animation()
        else:
            self.animation = anim_obj

    def draw(self, surf, scroll=[0, 0]):
        surf.blit(self.image, (self.rect.x-scroll[0],self.rect.y-scroll[1]))

    def animate(self):
        self.image, frame_name = self.animation.animate(self.state, True, True)
        return frame_name

    def get_center(self):
        center_x = self.rect.x+int(self.rect.width/2)
        center_y = self.rect.y+int(self.rect.height/2)
        return [center_x, center_y]

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y
        self.physics_obj.x = x
        self.physics_obj.y = y
        self.physics_obj.rect.x = x
        self.physics_obj.rect.y = y
        
class Camera:
    def __init__(self):
        self.true_scroll = [0,0]
        self.scroll = [0,0]

    def update(self,target,surf,diviser):
        self.scroll = [0,0]
        self.true_scroll[0] += (target.x-surf.get_width()/2-self.true_scroll[0])/diviser
        self.true_scroll[1] += (target.y-surf.get_height()/2-self.true_scroll[1])/diviser
        self.scroll[0] = int(self.true_scroll[0])
        self.scroll[1] = int(self.true_scroll[1])
        

class Text:
    def __init__(self, font_path, spacing,scale):
        self.font_image = font_path
        self.spacing = spacing
        self.font = {}
        self.scale = scale
        self.y_size = 0
        self.load_font()

    def load_font(self):
        Font_Order = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", ":", "/", "-", ".", "!"]
        font_image = pygame.image.load(self.font_image).convert()
        character_count = 0
        current_char_width = 0
        for x in range(font_image.get_width()):
            c = font_image.get_at((x, 0))
            if c[0] == 127:
                char_img = ImageManager.get_image(font_image, x - current_char_width, 0, current_char_width, font_image.get_height(), self.scale)
                self.font[Font_Order[character_count]] = char_img
                character_count += 1
                current_char_width = 0
            else:
                current_char_width += 1
        self.y_size = font_image.get_height()

    def render(self,surf, text, x, y, color=None):
        spacing = 0
        y_offset = 0
        for index,char in enumerate(text):
            if color != None:
                if char not in [' ','\n']:
                    char_img = swap_color(self.font[char], (255,0,0), color)
            else:
                if char not in [' ','\n']:
                    char_img = self.font[char]

            if char not in [' ','\n']:
                surf.blit(char_img, (x+spacing, y+y_offset))
            if char not in [' ','\n']:
                spacing += self.font[char].get_width() + self.spacing
            else:
                spacing += self.font['A'].get_width()
            
            if char == '\n':
                y_offset += self.font['A'].get_height()+1
                spacing = 0
            

    def get_size(self,text):
        width = 0
        height = self.font['A'].get_height()
        for char in text:
            if char not in [' ','\n']:
                width += self.font[char].get_width()
            else:
                width += self.font['A'].get_width()

            if char == '\n':
                height += self.font['A'].get_height()+1
                width = 0

        width += (len(text)-1)*self.spacing
        return [width, height]

class Animation:
    def __init__(self):
        self.anim_database = {}
        self.frames = {}
        self.frame_count = 0
        self.image = None
        self.loop = True
        self.states = []

    def load_anim(self, anim_name, folder, ext, frame_duration, scale=1, colorkey=None):
        img_id = folder.split('/')[-1]
        self.anim_database[anim_name] = {}
        self.frames[anim_name] = []
        self.states.append(anim_name)
        for i in range(len(frame_duration)):
            path = f"{folder}/{img_id}{i+1}.{ext}"
            if colorkey != None:
                img = ImageManager.load(path, colorkey)
                img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
                self.anim_database[anim_name][path.split('/')[-1].split('.')[0]] = img
            else:
                img = ImageManager.load(path)
                img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
                self.anim_database[anim_name][path.split('/')[-1].split('.')[0]] = img
            for i in range(frame_duration[i]):
                self.frames[anim_name].append(path.split('/')[-1].split('.')[0])

        frame = self.frames[self.states[0]][0]
        self.image = self.anim_database[self.states[0]][frame]

    def set_loop(self, flag: bool):
        self.loop = flag
        
    def animate(self,state,return_img=False,return_frame=False):
        if state in self.states:
            self.frame_count += 1
            if self.loop == True:
                if self.frame_count >= len(self.frames[state]):
                    self.frame_count = 0
            frame_name = self.frames[state][self.frame_count]
            self.image = self.anim_database[state][frame_name]
            if return_img != False and return_frame != True:
                return self.image
            if return_frame != False and return_img != True:
                return frame_name
            if (return_frame and return_img) == True:
                return [self.image, frame_name]
        
