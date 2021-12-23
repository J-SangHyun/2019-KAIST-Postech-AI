# TCP NetworkIO

from threading import Lock


class NetworkIO:
    _instance = None

    def __init__(self, Client):
        self.client = Client
        self.SendLock = Lock()
        self.RecvLock = Lock()

    @classmethod
    def __getInstance(cls):
        return cls._instance

    @classmethod
    def instance(cls, Client):
        cls._instance = NetworkIO(Client)  # 생성은 단 한번만
        cls.instance = cls.__getInstance  # 생성된 후는 instance를 호출하는 함수로 리다이렉트
        return cls._instance

    def send_bytelist(self, data):
        len_byte = bytearray([len(data) >> i & 0xff for i in (24, 16, 8, 0)])
        with self.SendLock:
            if len(data) == 0:
                self.client.send(b'\x00')
            else:
                r = 0
                while r < 4:
                    r += self.client.send(len_byte)
                r = 0
                while r < len(data):
                    r += self.client.send(data)

    def recv_bytelist(self):
        with self.RecvLock:
            len_byte = b''
            while len(len_byte) < 4:
                packet = self.client.recv(4 - len(len_byte))
                len_byte += packet

            data_len = int.from_bytes(len_byte, byteorder='big', signed=True)
            if data_len == 0:
                return -1
            byte_data = b''
            while len(byte_data) < data_len:
                packet = self.client.recv(data_len - len(byte_data))
                byte_data += packet
            return byte_data
