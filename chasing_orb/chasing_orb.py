import os.path
import math

import Client
from Protobuf import Client2Server_pb2


# connect to server
client = Client.Client()
if os.path.isfile('./Login.txt'):
    f = open("./Login.txt", "r")
    t = f.read().splitlines()
    ID = t[0].split(':')[1]
    IP = t[1].split(':')[1]
    client.connect(ip=IP, ID=ID)
else:
    client.connect()

last_turn = -1
command_count = 0
map_size = 32
character_speed = 6
character_rotate = 3.14
character_sight_length = 12
character_sight_angle = 3.14 / 3
wall_tolerance = 3
map_tolerance = 2
is_turning = dict()

while True:
    if client.is_end:
        last_turn = -1

    if not client.recent_pick is None:
        client.send_pick(4)  # DUMMY=0, ROLLER=1, TANKER=2, HERMIT=3, ORB=4
        client.recent_pick = None

    dataqueue = client.get_player_data()  # 서버로부터 데이터 받음

    if dataqueue is not None and dataqueue.turn > last_turn:
        last_turn = dataqueue.turn
        for d in dataqueue.framedata[0].characterdata:
            command = Client2Server_pb2.CharacterCommand()
            move_speed = character_speed

            if d.tag not in is_turning.keys():
                is_turning[d.tag] = None

            is_there_wall = False
            for so in d.sight_object:
                if so.type == 2 or so.type == 3 or so.type == 4:  # BULLET=0, OBSTACLE_WALL=2, OBSTACLE_CRACK=3, OBSTACLE_FRAGILE=4
                    rel_wall_pos = [so.pos.x - d.state.pos.x, so.pos.y - d.state.pos.y]  # 상대적인 위치
                    wall_dis = math.sqrt(rel_wall_pos[0] ** 2 + rel_wall_pos[1] ** 2)
                    normalized_wall_dir = [rel_wall_pos[0] / wall_dis , rel_wall_pos[1] / wall_dis]
                    wall_inner_producted = normalized_wall_dir[0] * d.state.faceDirVector.x + normalized_wall_dir[1] * d.state.faceDirVector.y
                    if wall_dis < wall_tolerance and wall_inner_producted > 0.92:
                        is_there_wall = True
                        # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                        wall_outer_producted = rel_wall_pos[0] * d.state.faceDirVector.y - rel_wall_pos[1] * d.state.faceDirVector.x
                        break

            for sc in d.sight_character:
                if sc.team == 1:  # NEUTRAL=0, FRIEND=1, ENEMY=2
                    rel_team_pos = [sc.pos.x - d.state.pos.x, sc.pos.y - d.state.pos.y]
                    team_dis = math.sqrt(rel_team_pos[0] ** 2 + rel_team_pos[1] ** 2)
                    normalized_team_dir = [rel_team_pos[0] / team_dis, rel_team_pos[1] / team_dis]
                    team_inner_producted = normalized_team_dir[0] * d.state.faceDirVector.x + normalized_team_dir[1] * d.state.faceDirVector.y
                    if team_inner_producted > 0.92 and team_dis < wall_tolerance:
                        is_there_wall = True
                        wall_outer_producted = rel_team_pos[0] * d.state.faceDirVector.y - rel_team_pos[1] * d.state.faceDirVector.x
                        break

            is_there_team = False
            my_team_dis = 0
            for sc in d.sight_character:
                if sc.team == 1:  # NEUTRAL=0, FRIEND=1, ENEMY=2
                    rel_team_pos = [sc.pos.x - d.state.pos.x, sc.pos.y - d.state.pos.y]
                    team_dis = math.sqrt(rel_team_pos[0] ** 2 + rel_team_pos[1] ** 2)
                    normalized_team_dir = [rel_team_pos[0] / team_dis, rel_team_pos[1] / team_dis]
                    team_inner_producted = normalized_team_dir[0] * d.state.faceDirVector.x + normalized_team_dir[1] * d.state.faceDirVector.y
                    if team_inner_producted > 0.95:
                        is_there_team = True
                        my_team_dis = team_dis
                        break

            # 경기장 바깥 쪽도 벽으로 인식
            if d.state.faceDirVector.x <= 0 and d.state.pos.x < - map_size + map_tolerance:
                is_there_wall = True
                wall_outer_producted = -d.state.faceDirVector.y
            if d.state.faceDirVector.x >= 0 and d.state.pos.x > map_size - map_tolerance:
                is_there_wall = True
                wall_outer_producted = d.state.faceDirVector.y
            if d.state.faceDirVector.y <= 0 and d.state.pos.y < - map_size + map_tolerance:
                is_there_wall = True
                wall_outer_producted = d.state.faceDirVector.x
            if d.state.faceDirVector.y >= 0 and d.state.pos.y > map_size - map_tolerance:
                is_there_wall = True
                wall_outer_producted = -d.state.faceDirVector.x

            if is_there_wall:
                if not is_turning[d.tag]:
                    if wall_outer_producted > 0:
                        is_turning[d.tag] = character_rotate
                    else:
                        is_turning[d.tag] = -character_rotate
                command.rotate_speed = is_turning[d.tag]
                move_speed = 0
            else:
                command.rotate_speed = 0
                move_speed = character_speed
                is_turning[d.tag] = None

            is_there_enemy = False
            enemy_pos = None
            for sc in d.sight_character:
                if sc.team == 2:  # NEUTRAL=0, FRIEND=1, ENEMY=2
                    is_there_enemy = True
                    enemy_pos = [sc.pos.x, sc.pos.y]
                    break
            if is_there_enemy:
                rel_enemy_pos = [enemy_pos[0] - d.state.pos.x, enemy_pos[1] - d.state.pos.y]
                enemy_dis = math.sqrt(rel_enemy_pos[0] ** 2 + rel_enemy_pos[1] ** 2)
                normalized_enemy_dir = [rel_enemy_pos[0] / enemy_dis, rel_enemy_pos[1] / enemy_dis]
                enemy_inner_producted = normalized_enemy_dir[0] * d.state.faceDirVector.x + normalized_enemy_dir[1] * d.state.faceDirVector.y
                # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                enemy_outer_producted = rel_enemy_pos[0] * d.state.faceDirVector.y - rel_enemy_pos[1] * d.state.faceDirVector.x
                rotate_speed = max(0, min(1, (1 - enemy_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                if enemy_outer_producted < 0:
                    command.rotate_speed = rotate_speed
                else:
                    command.rotate_speed = -rotate_speed

                if is_there_team and my_team_dis < enemy_dis:
                    command.focusaction = Client2Server_pb2.NONE
                else:
                    command.focusaction = Client2Server_pb2.ATTACK

                move_speed = character_speed
                if enemy_dis < character_sight_length * 2 / 3:
                    command.mov_dir.x = 0
                    command.mov_dir.y = 0
                else:
                    command.mov_dir.x = move_speed * normalized_enemy_dir[0]
                    command.mov_dir.y = move_speed * normalized_enemy_dir[1]
            else:
                command.focusaction = Client2Server_pb2.NONE
                command.mov_dir.x = move_speed * d.state.faceDirVector.x
                command.mov_dir.y = move_speed * d.state.faceDirVector.y

            command.tag = d.tag

            command.turn = dataqueue.turn + 1
            client.send_unit_command(command_count, command)
            command_count += 1
