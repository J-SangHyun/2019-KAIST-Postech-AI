from datetime import datetime

import Constants
import Network.NetworkIO as NetworkIO
from Protobuf import Pick_pb2 as Pick
from Protobuf import Server2Client_pb2 as S2C


class Listener:

    def __init__(self):
        self.IOagent = NetworkIO.NetworkIO.instance()
        self.wintext = {Constants.WinType.WIN_DECISIVE: "판정승",
                        Constants.WinType.WIN_DOMINATE: "점령승",
                        Constants.WinType.WIN_ELIMINATE: "섬멸승"}

    def get_unitdata(self):
        rawdata = self.IOagent.recv_bytelist()
        recv_time = datetime.now()
        msg_buf = rawdata[1:]
        header = rawdata[0]

        if header == Constants.PacketType.SIGHTDATA.value:
            data = S2C.TurnData()
            data.ParseFromString(msg_buf)
            return data
        elif header == Constants.PacketType.NTPRESPONSE.value:
            pass
        elif header == Constants.PacketType.COMMAND_FEEDBACK.value:
            pass
        elif header == Constants.PacketType.NONCOMMAND_FEEDBACK.value:
            pass
        elif header == Constants.PacketType.GAMESET.value:
            print(str(Constants.WinTeam(msg_buf[1])) + "팀의 " +
                  self.wintext[Constants.WinType(msg_buf[0])] + "입니다.")
            return 20
        elif header == Constants.PacketType.PICKSTATEDATA.value:
            data = Pick.Pick()
            data.ParseFromString(msg_buf)
            return data
