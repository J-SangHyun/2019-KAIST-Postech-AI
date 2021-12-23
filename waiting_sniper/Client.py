#TCP server

import ipaddress
import socket
import threading

import Constants
import Network.Listener as Listener
import Network.NetworkIO as NetIO
from Protobuf import Pick_pb2 as Pick
from Protobuf import Server2Client_pb2 as S2C


class Client:

    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IOagent = None
        self.listener = None

        self.recent_pick = None
        self.sight = None
        self.is_end = False

    def connect(self, ip=None, port=6614, ID=None):

        while ip is None:
            try:
                val = input("서버의 ipv4 주소를 입력해주세요(port제외)\n")
                ip = ipaddress.ip_address(val)
                break
            except ValueError:
                print("유효한 ipv4 주소를 입력해주세요")
        while port is None:
            try:
                val = input("서버의 Port를 입력해주세요\n")
                port = int(val)
                if 1024 <= port <= 65535:
                    break
                else:
                    port = None
                    print("1024 <= port <= 65535를 충족하는 port 번호를 입력해주세요")
            except ValueError:
                print("유효한 port 번호를 입력해주세요")
        while True:
            if ID is None:
                ID = input("ID를 입력해주세요\n")

            print(str(ip) + ":" + str(port) + "로 연결을 시도합니다...")
            self.client_socket.connect((str(ip), port))
            self.IOagent = NetIO.NetworkIO.instance(self.client_socket)

            if self.Login(ID):
                print("ID: " + ID + "로 IP:" + str(ip) + ":" + str(port) + "와 연결했습니다.")
                break
            else:
                print("ID: {}로 접속을 시도했으나 거부당했습니다. 유효환 ID로 다시 시도해주세요.".format(ID))
                ID = None

        #  Server Input을 지속적으로 Handle할 객체를 만들어 줍니다.
        self.listener = Listener.Listener()

        #  데이터를 지속적으로 입력받고 처리하는 Thread를 개설합니다.
        t = threading.Thread(target=self.save_data)
        t.start()

    def get_player_data(self):
        return self.sight

    def save_data(self):
        while True:
            data = self.listener.get_unitdata()
            if type(data) is Pick.Pick:
                self.is_end = False
                self.recent_pick = data
            elif type(data) is S2C.TurnData:
                self.is_end = False
                self.sight = data
            elif type(data) is int:
                if data / 10 == 2:
                    print("게임이 종료되었습니다.")
                    self.is_end = True
            # TODO: Feedback과 NTP 구현!

    def send_unit_command(self, cmd_number, data):

        if data is None:
            return False

        raw_data = bytearray(cmd_number.to_bytes(4, 'little'))
        raw_data += data.SerializeToString()
        raw_data = bytearray(Constants.PacketType.UNITCOMMANDDATA.value.to_bytes(1, 'little')) + raw_data
        self.IOagent.send_bytelist(raw_data)
        return True

    def send_pick(self, chara=Pick.ROLLER):
        data = bytearray(Constants.PacketType.PICKCHOOSEDATA.value.to_bytes(1, 'little'))
        data += chara.to_bytes(1, 'little')
        self.IOagent.send_bytelist(data)

    def Login(self, ID):
        byte_id = bytearray(Constants.PacketType.LOGIN.value.to_bytes(1, 'little'))
        byte_id += ID.encode('ascii')
        self.IOagent.send_bytelist(byte_id)

        res = self.IOagent.recv_bytelist()
        return res[0] == Constants.PacketType.NONCOMMAND_FEEDBACK.value and \
               res[1] == Constants.S2CFeedbackType.LOGIN_ACCEPTED.value
