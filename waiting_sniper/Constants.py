from enum import Enum


class PacketType(Enum):
    #  게임이 종료될 때 어떤 유형으로 누가 이겼는지를 나타냅니다.
    GAMESET = 1  # |--WinType(1)--|---WinTeam(1)---|
    #  매 턴마다 Server가 Player에게 제공하는 시야 정보
    SIGHTDATA = 10  # |--protocol buffer data(X)--|
    #  Client가 Server에게 전달하는 단일 캐릭터 명령
    UNITCOMMANDDATA = 11  # |--Order of command(4)--|--protocol buffer data(X)--|
    #  Client가 Server에게 전달하는 다중 캐릭터 명령
    COMMANDDATA = 12  # |--Order of command(4)--|--protocol buffer data(X)--|

    #  Server가 Client에게 전달하는 현재 픽 상황
    PICKSTATEDATA = 15  # |--Protocol buffer data(X)--|
    # Client가 Server에게 전달하는 픽
    PICKCHOOSEDATA = 16  # |--Charactertype(1)--|

    # Client의 입력에 대한 Feedback입니다.
    # 입력이 Command 계열일 경우 Command_feedback이 제공되며, 그렇지 않을 경우 Noncommand_feedback이 제공됩니다.
    NONCOMMAND_FEEDBACK = 32  # |--S2CFeedbackType(1)--|
    COMMAND_FEEDBACK = 33  # |--Order of command(4)--|--S2CFeedbackType(1)--|

    # 맨 처음에 Client가 Server에게 전달해야 하는 ID
    LOGIN = 40  # |--ID(X)--| [[1]]
    # Server에게 NTPv4를 활용한 시간 동기화 요청
    NTPREQUEST = 123  # |--NTP packet(48)--|
    # Server에서 제공하는 시간 동기화에 사용할 수 있는 NTP packet
    NTPRESPONSE = 124  # |--NTP packet(48)--|
    # DOS 공격을 시도했다고 간주되어 연결을 종료합니다.
    BANNED_BY_DOS_ATTEMPT = 144  # 뒤에 더 오는 데이터가 없습니다.


class S2CFeedbackType(Enum):
    # 0X type은 COMMAND_FEEDBACK packettype에 사용됩니다.
    ACCEPT = 0  # 입력한 명령 데이터가 Game에 정상적으로 전달됨
    TIMEOUT = 1  # 입력한 명령 데이터가 지정된 입력 시간보다 늦게 입력됨
    INVALID_COMMAND = 2  # 입력한 명령 데이터의 값이 유효한 범위를 넘어서서 명령이 무시됨

    # 1X type은 NONCOMMAND_FEEDBACK에 해당합니다.
    LOGIN_ACCEPTED = 10  # Login 성공
    LOGIN_DENIED = 11  # Login 실패
    BAD_NTPREQ = 12  # NTP packet의 규격이 올바르지 않음
    INPUT_TIMEOUT = 13  # Raw packet의 입력 제한시간을 초과하여 Server에 data packet이 전달되지도 않음
    INVALID_TYPE = 14  # Undefined PacketType을 사용
    
    # 10X type은 COMMAND_FEEDBACK 및 NONCOMMAND_FEEDBACK 모두에 사용할 수 있습니다.
    INVALID_FORMAT = 100  # 입력한 PacketType에 맞지 않는 binary data를 입력(Format Violation)


class WinType(Enum):
    #  2X message는 게임의 승패를 나타냅니다. Draw를 제외하면 Submessage에 승리한 팀의 색을 기록합니다.
    #  전멸승리로 게임이 끝났습니다.
    WIN_ELIMINATE = 20
    #  점령승리로 게임이 끝났습니다.
    WIN_DOMINATE = 21
    #  반칙패 등 전멸 및 점령이 아닌 다른 방식으로 승패가 판정되었습니다.
    #  세부 사항은 룰에 제시되어 있습니다.
    #  </summary>
    WIN_DECISIVE = 22
    #  <summary>
    #  무승부로 게임이 끝났습니다.
    #  </summary>
    DRAW = 23


class WinTeam(Enum):
    NULL = 0
    RED = 1
    BLUE = 2
