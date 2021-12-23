import os.path
import random
import Client
from Protobuf import Client2Server_pb2
import math
from enum import Enum

client = Client.Client()
if os.path.isfile('./Login.txt'):
    f = open("./Login.txt", "r")
    t = f.read().splitlines()
    ID = t[0].split(':')[1]
    IP = t[1].split(':')[1]
    client.connect(ip=IP, ID=ID)
else:
    client.connect()

# 이 아래부터는 여러분의 AI가 들어가면 됩니다. (현재 작성된 코드는 발사를 제외한 랜덤한 행동을 수행하는 AI입니다)

last_turn = -1

command_count = 0

#총알 반지름
radius_bullet = 0.5
#바디 반지름
radius_body = 0.9
#랜덤 이동이 가능한 반경
range_move_efficient = 3
#맵사이즈
map_size = 32
#부딪히기 직전 거리
D = 5

rotate_state_previous = {}
health_previous ={}
is_blue_team = None
turned = False
up_vec = [0, 1]

while True:
    if client.is_end:
        last_turn = -1

    # Pregame Logic: 현재 Pick 정보를 받아 출력한 뒤, 랜덤한 픽을 서버에 전송합니다.
    if not client.recent_pick is None:
        client.send_pick(random.randrange(1, 6))
        client.recent_pick = None

    # Maingame Logic: 각 캐릭터의 시야 정보를 받은 뒤, 랜덤한 명령을 Server에게 전송합니다.
    dataqueue = client.get_player_data()
    if not dataqueue is None and dataqueue.turn > last_turn:
        last_turn = dataqueue.turn
        for d in dataqueue.framedata[0].characterdata:
            attacked = False  # 공격당하고 있는 상태인가?
            linear_move_possible = True  # 직진 운동이 가능한가?
            random_move_possible = True  # 랜덤 운동이 가능한가? 직진 운동보다 우선순위
            enemy = False
            enemy_attack_possible = False  # 적을 공격할 수 있는 범위에 있는가?
            team_attack_possible = False
            enemy_rotat = True  # CCW
            rotate_direction = True
            command = Client2Server_pb2.CharacterCommand()

            if is_blue_team is None and d.state.pos.x > d.state.pos.y:
                is_blue_team = True
            if is_blue_team is None and d.state.pos.x < d.state.pos.y:
                is_blue_team = False

            if is_blue_team and not turned:
                inner_product = up_vec[0] * d.state.faceDirVector.x + up_vec[1] * d.state.faceDirVector.y
                if inner_product > 0.99:
                    turned = True
                else:
                    command.rotate_speed = 3.14 / 2
                    command.mov_dir.x = 0
                    command.mov_dir.y = 0
                    command.focusaction = Client2Server_pb2.NONE
            else:
                x_Face_orthogonal = -radius_body * d.state.faceDirVector.y
                y_Face_orthogonal = radius_body * d.state.faceDirVector.x
                x_Face_orthogonal_bullet = -radius_bullet * d.state.faceDirVector.y
                y_Face_orthogonal_bullet = radius_bullet * d.state.faceDirVector.x
                min_point = [100, 0]
                max_point = [-100, -0]
                if d.tag not in health_previous:
                    health_previous[d.tag] = d.state.health
                else:
                    if health_previous[d.tag] != d.state.health:
                        attacked = True
                for s in d.sight_object:
                    if s.type == 2 or s.type == 3 or s.type == 4:  # OBSTACLE_WALL
                        x_object = s.pos.x - d.state.pos.x
                        y_object = s.pos.y - d.state.pos.y
                        if min_point[0]>x_object:
                            min_point[0]=x_object
                            min_point[1]=y_object
                        if max_point[0]<x_object:
                            max_point[0]=x_object
                            max_point[1]=y_object
                        if math.sqrt(x_object * x_object + y_object * y_object) < range_move_efficient:
                            random_move_possible = False
                        if abs(x_object * x_Face_orthogonal + y_object * y_Face_orthogonal) < radius_body * radius_body and math.sqrt(x_object * x_object + y_object * y_object) < range_move_efficient:
                            linear_move_possible = False
                    if s.type == 1:
                        pass
                    # 총이 나한테 맞을 수 있는지 판단하는 코드 짜기
                if min_point[1]<=max_point[1]:
                    rotate_direction = False
                else:
                    rotate_direction = True
                for s in d.sight_character:
                    x_enemy = s.pos.x - d.state.pos.x
                    y_enemy = s.pos.y - d.state.pos.y
                    if s.team == 2: # enemy
                        enemy = True
                        if abs(x_enemy * x_Face_orthogonal_bullet + y_enemy * y_Face_orthogonal_bullet) < radius_bullet * radius_bullet:
                            enemy_attack_possible = True
                        cross_product = d.state.faceDirVector.x * y_enemy - d.state.faceDirVector.y * x_enemy
                        theta = abs((d.state.faceDirVector.x * x_enemy + d.state.faceDirVector.y * y_enemy)/math.sqrt(x_enemy*x_enemy+y_enemy*y_enemy))
                        if cross_product < 0:
                            enemy_rotat = False
                    if s.team == 1:
                        if abs(
                                x_enemy * x_Face_orthogonal_bullet + y_enemy * y_Face_orthogonal_bullet) < radius_bullet * radius_bullet:
                            team_attack_possible = True
                        # 적을 공격하면서 피해갈 수 있는 코드 짜기
                if d.state.faceDirVector.x <= 0 and d.state.pos.x < - map_size + D:
                    random_move_possible = False
                    linear_move_possible = False
                if d.state.faceDirVector.x >= 0 and d.state.pos.x > map_size - D:
                    random_move_possible = False
                    linear_move_possible = False
                if d.state.faceDirVector.y <= 0 and d.state.pos.y < - map_size + D:
                    random_move_possible = False
                    linear_move_possible = False
                if d.state.faceDirVector.y >= 0 and d.state.pos.y > map_size - D:
                    random_move_possible = False
                    linear_move_possible = False
                if d.tag not in rotate_state_previous:
                    rotate_state_previous[d.tag] = {"rotate": False, "direction": True}
                if not attacked and not enemy:
                    if random_move_possible:
                        if rotate_state_previous[d.tag]["rotate"]:
                            rotate_state_previous[d.tag]["rotate"] = False
                        if not linear_move_possible:
                            command.mov_dir.x = random.uniform(-3.5, 3.5)
                            command.mov_dir.y = random.uniform(0, 10)
                            command.rotate_speed = 0
                            command.focusaction = 0
                        else:
                            command.mov_dir.x = 3 * d.state.faceDirVector.x
                            command.mov_dir.y = 3 * d.state.faceDirVector.y
                            command.rotate_speed = 0
                            command.focusaction = 0
                    else:
                        if linear_move_possible:
                            if rotate_state_previous[d.tag]["rotate"]:
                                rotate_state_previous[d.tag]["rotate"] = False
                            #10은 비율로써 확인해야함
                            command.mov_dir.x = 10 * d.state.faceDirVector.x
                            command.mov_dir.y = 10 * d.state.faceDirVector.y
                            command.rotate_speed = 0
                            command.focusaction = 0
                        else:
                            command.mov_dir.x = 0
                            command.mov_dir.y = 0
                            command.focusaction = 0
                            if not rotate_state_previous[d.tag]["rotate"]:
                                rotate_state_previous[d.tag]["rotate"] = True
                                if rotate_direction:
                                    rotate_state_previous[d.tag]["direction"] = True
                                    command.rotate_speed = 30
                                else:
                                    rotate_state_previous[d.tag]["direction"] = False
                                    command.rotate_speed = -30
                            else:
                                if rotate_state_previous[d.tag]["direction"]:
                                    command.rotate_speed = 30
                                else:
                                    command.rotate_speed = -30
                elif not attacked and enemy:
                    if enemy_attack_possible:
                        if team_attack_possible:
                            command.mov_dir.x = 3 * x_Face_orthogonal_bullet + random.uniform(-1, 1)
                            command.mov_dir.y = 3 * y_Face_orthogonal_bullet + random.uniform(-1, 1)
                            command.rotate_speed = 0
                            command.focusaction = 0
                        else:
                            command.mov_dir.x = -5 * d.state.faceDirVector.x
                            command.mov_dir.y = -5 * d.state.faceDirVector.y
                            command.rotate_speed = 0
                            command.focusaction = 1
                    else:
                        if enemy_rotat:
                            command.mov_dir.x = random.uniform(-2, 2)
                            command.mov_dir.y = random.uniform(-2, 2)
                            command.rotate_speed = 2 * theta/0.52
                            command.focusaction = 1
                        else:
                            command.mov_dir.x = random.uniform(-2, 2)
                            command.mov_dir.y = random.uniform(-2, 2)
                            command.rotate_speed = -2 * theta/0.52
                            command.focusaction = 1
                elif attacked and not enemy:
                    command.mov_dir.x = random.uniform(-10, 10)
                    command.mov_dir.y = random.uniform(-10, 10)
                    command.rotate_speed = 30
                    command.focusaction = 0
                else:
                    command.mov_dir.x = random.uniform(-10, 10)
                    command.mov_dir.y = random.uniform(-10, 10)
                    if enemy_rotat:
                        command.rotate_speed = 2 * theta / 0.52
                    else:
                        command.rotate_speed = -2 * theta / 0.52
                    command.focusaction = 1
            command.tag = d.tag
            command.turn = dataqueue.turn + 1
            client.send_unit_command(command_count, command)
            command_count += 1
