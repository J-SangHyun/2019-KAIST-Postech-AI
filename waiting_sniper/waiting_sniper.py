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
character_rotate = 3.14 / 2
character_sight_length = 20
character_sight_angle = 3.14 / 4

team_color = None
RED_TEAM = 1
BLUE_TEAM = 2
positioning_step = dict()
last_step_data = dict()
diff_unit = dict()


while True:
    if client.is_end:
        last_turn = -1

    if not client.recent_pick is None:
        client.send_pick(3)  # DUMMY=0, ROLLER=1, TANKER=2, HERMIT=3, ORB=4
        client.recent_pick = None

    dataqueue = client.get_player_data()  # 서버로부터 데이터 받음

    if dataqueue is not None and dataqueue.turn > last_turn:
        last_turn = dataqueue.turn
        command = Client2Server_pb2.CharacterCommand()
        for d in dataqueue.framedata[0].characterdata:
            if d.tag not in diff_unit.keys():
                if 1 <= d.state.pos.y < 2:
                    diff_unit[d.tag] = True
                else:
                    diff_unit[d.tag] = False
            if d.tag not in positioning_step.keys():
                positioning_step[d.tag] = 0
            if d.tag not in last_step_data.keys():
                last_step_data[d.tag] = [None, None]
            if team_color is None:
                if d.state.pos.x > d.state.pos.y:
                    team_color = BLUE_TEAM
                else:
                    team_color = RED_TEAM
            
            if team_color == BLUE_TEAM:
                if positioning_step[d.tag] == 0:
                    if d.state.pos.y < -31:
                        last_step_data[d.tag][0] = d.state.pos.x
                        positioning_step[d.tag] = 1
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.x = 0
                        command.mov_dir.y = -character_speed
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 1:
                    # x + 23
                    if d.state.pos.x >= 23:
                        if d.state.pos.x - last_step_data[d.tag][0] >= 25:
                            last_step_data[d.tag][1] = d.state.pos.y
                            positioning_step[d.tag] = 2
                        else:
                            command.focusaction = Client2Server_pb2.NONE
                            command.mov_dir.x = character_speed
                            command.mov_dir.y = 0
                            command.rotate_speed = 0
                    elif d.state.pos.x - last_step_data[d.tag][0] >= 23:
                        last_step_data[d.tag][1] = d.state.pos.y
                        positioning_step[d.tag] = 2
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.x = character_speed
                        command.mov_dir.y = 0
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 2:
                    if d.state.pos.x >= 24 and d.state.pos.y - last_step_data[d.tag][1] >= 3:
                        positioning_step[d.tag] = 3
                    if d.state.pos.x < 24 and d.state.pos.y - last_step_data[d.tag][1] >= 4:
                        positioning_step[d.tag] = 3
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.x = 0
                        command.mov_dir.y = character_speed
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 3:
                    # waiting mode, target=(15, -31)
                    rel_target_vec = [15 - d.state.pos.x, -31 - d.state.pos.y]
                    target_dis = math.sqrt(rel_target_vec[0] ** 2 + rel_target_vec[1] ** 2)
                    normalized_target_vec = [rel_target_vec[0] / target_dis, rel_target_vec[1] / target_dis]

                    target_inner_producted = normalized_target_vec[0] * d.state.faceDirVector.x + normalized_target_vec[1] * d.state.faceDirVector.y
                    if target_inner_producted >= 0.99:
                        # 조준 완료
                        command.focusaction = Client2Server_pb2.ATTACK
                        command.mov_dir.x = 0
                        command.mov_dir.y = 0
                        positioning_step[d.tag] = 4
                    else:
                        # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                        target_outer_producted = rel_target_vec[0] * d.state.faceDirVector.y - rel_target_vec[1] * d.state.faceDirVector.x
                        
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.x = 0
                        command.mov_dir.y = 0
                        rotate_speed = max(0, min(1, (1 - target_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                        rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                        if target_outer_producted < 0:
                            command.rotate_speed = rotate_speed
                        else:
                            command.rotate_speed = -rotate_speed
                elif positioning_step[d.tag] == 4:
                    command.mov_dir.x = 0
                    command.mov_dir.y = 0
                    command.focusaction = Client2Server_pb2.ATTACK
                    is_there_enemy = False
                    enemy_pos = None
                    for sc in d.sight_character:
                        if sc.team == 2:  # NEUTRAL=0, FRIEND=1, ENEMY=2
                            is_there_enemy = True
                            enemy_pos = [sc.pos.x, sc.pos.y]
                    if is_there_enemy:
                        rel_enemy_vec = [enemy_pos[0] - d.state.pos.x, enemy_pos[1] - d.state.pos.y]
                        enemy_dis = math.sqrt(rel_enemy_vec[0] ** 2 + rel_enemy_vec[1] ** 2)
                        normalized_enemy_dir = [rel_enemy_vec[0] / enemy_dis, rel_enemy_vec[1] / enemy_dis]
                        enemy_inner_producted = normalized_enemy_dir[0] * d.state.faceDirVector.x + normalized_enemy_dir[1] * d.state.faceDirVector.y
                        # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                        enemy_outer_producted = rel_enemy_vec[0] * d.state.faceDirVector.y - rel_enemy_vec[1] * d.state.faceDirVector.x
                        rotate_speed = max(0, min(1, (1 - enemy_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                        rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                        if enemy_outer_producted < 0:
                            command.rotate_speed = rotate_speed
                        else:
                            command.rotate_speed = -rotate_speed
                    else:
                        rel_target_vec = [15 - d.state.pos.x, -31 - d.state.pos.y]
                        target_dis = math.sqrt(rel_target_vec[0] ** 2 + rel_target_vec[1] ** 2)
                        normalized_target_vec = [rel_target_vec[0] / target_dis, rel_target_vec[1] / target_dis]

                        target_inner_producted = normalized_target_vec[0] * d.state.faceDirVector.x + normalized_target_vec[1] * d.state.faceDirVector.y
                        if target_inner_producted >= 0.99:
                            command.rotate_speed = 0
                        else:
                            # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                            target_outer_producted = rel_target_vec[0] * d.state.faceDirVector.y - rel_target_vec[1] * d.state.faceDirVector.x
                            rotate_speed = max(0, min(1, (1 - target_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                            rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                            if target_outer_producted < 0:
                                command.rotate_speed = rotate_speed
                            else:
                                command.rotate_speed = -rotate_speed

            elif team_color == RED_TEAM:
                if positioning_step[d.tag] == 0:
                    if d.state.pos.x < -31:
                        last_step_data[d.tag][0] = d.state.pos.y
                        positioning_step[d.tag] = 1
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.y = 0
                        command.mov_dir.x = -character_speed
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 1:
                    # y + 23
                    if diff_unit[d.tag]:
                        if d.state.pos.y - last_step_data[d.tag][0] >= 21:
                            last_step_data[d.tag][1] = d.state.pos.x
                            positioning_step[d.tag] = 2
                        else:
                            command.focusaction = Client2Server_pb2.NONE
                            command.mov_dir.y = character_speed
                            command.mov_dir.x = 0
                            command.rotate_speed = 0
                    elif d.state.pos.y - last_step_data[d.tag][0] >= 23:
                        last_step_data[d.tag][1] = d.state.pos.x
                        positioning_step[d.tag] = 2
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.y = character_speed
                        command.mov_dir.x = 0
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 2:
                    if d.state.pos.y >= 24 and d.state.pos.x - last_step_data[d.tag][1] >= 3:
                        positioning_step[d.tag] = 3
                    if d.state.pos.y < 24 and d.state.pos.x - last_step_data[d.tag][1] >= 4:
                        positioning_step[d.tag] = 3
                    else:
                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.y = 0
                        command.mov_dir.x = character_speed
                        command.rotate_speed = 0
                elif positioning_step[d.tag] == 3:
                    # waiting mode, target=(-32, 15)
                    rel_target_vec = [-32 - d.state.pos.x, 15 - d.state.pos.y]
                    target_dis = math.sqrt(rel_target_vec[0] ** 2 + rel_target_vec[1] ** 2)
                    normalized_target_vec = [rel_target_vec[0] / target_dis, rel_target_vec[1] / target_dis]

                    target_inner_producted = normalized_target_vec[0] * d.state.faceDirVector.x + normalized_target_vec[1] * d.state.faceDirVector.y
                    if target_inner_producted >= 0.99:
                        # 조준 완료
                        command.focusaction = Client2Server_pb2.ATTACK
                        command.mov_dir.x = 0
                        command.mov_dir.y = 0
                        positioning_step[d.tag] = 4
                    else:
                        # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                        target_outer_producted = rel_target_vec[0] * d.state.faceDirVector.y - rel_target_vec[1] * d.state.faceDirVector.x

                        command.focusaction = Client2Server_pb2.NONE
                        command.mov_dir.x = 0
                        command.mov_dir.y = 0
                        rotate_speed = max(0, min(1, (1 - target_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                        rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                        if target_outer_producted < 0:
                            command.rotate_speed = rotate_speed
                        else:
                            command.rotate_speed = -rotate_speed
                elif positioning_step[d.tag] == 4:
                    command.mov_dir.x = 0
                    command.mov_dir.y = 0
                    command.focusaction = Client2Server_pb2.ATTACK
                    is_there_enemy = False
                    enemy_pos = None
                    for sc in d.sight_character:
                        if sc.team == 2:  # NEUTRAL=0, FRIEND=1, ENEMY=2
                            is_there_enemy = True
                            enemy_pos = [sc.pos.x, sc.pos.y]
                    if is_there_enemy:
                        rel_enemy_vec = [enemy_pos[0] - d.state.pos.x, enemy_pos[1] - d.state.pos.y]
                        enemy_dis = math.sqrt(rel_enemy_vec[0] ** 2 + rel_enemy_vec[1] ** 2)
                        normalized_enemy_dir = [rel_enemy_vec[0] / enemy_dis, rel_enemy_vec[1] / enemy_dis]
                        enemy_inner_producted = normalized_enemy_dir[0] * d.state.faceDirVector.x + normalized_enemy_dir[1] * d.state.faceDirVector.y
                        # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                        enemy_outer_producted = rel_enemy_vec[0] * d.state.faceDirVector.y - rel_enemy_vec[1] * d.state.faceDirVector.x
                        rotate_speed = max(0, min(1, (1 - enemy_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                        rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                        if enemy_outer_producted < 0:
                            command.rotate_speed = rotate_speed
                        else:
                            command.rotate_speed = -rotate_speed
                    else:
                        rel_target_vec = [-32 - d.state.pos.x, 15 - d.state.pos.y]
                        target_dis = math.sqrt(rel_target_vec[0] ** 2 + rel_target_vec[1] ** 2)
                        normalized_target_vec = [rel_target_vec[0] / target_dis, rel_target_vec[1] / target_dis]

                        target_inner_producted = normalized_target_vec[0] * d.state.faceDirVector.x + normalized_target_vec[1] * d.state.faceDirVector.y
                        if target_inner_producted >= 0.99:
                            command.rotate_speed = 0
                        else:
                            # u, v의 외적의 z 성분은 u1 * v2 - u2 * v1
                            target_outer_producted = rel_target_vec[0] * d.state.faceDirVector.y - rel_target_vec[1] * d.state.faceDirVector.x
                            rotate_speed = max(0, min(1, (1 - target_inner_producted) / (math.cos(character_sight_angle / 2) + 0.01)))
                            rotate_speed = character_rotate * rotate_speed ** (1 / 2.2)
                            if target_outer_producted < 0:
                                command.rotate_speed = rotate_speed
                            else:
                                command.rotate_speed = -rotate_speed

            command.tag = d.tag

            command.turn = dataqueue.turn + 1
            client.send_unit_command(command_count, command)
            command_count += 1
