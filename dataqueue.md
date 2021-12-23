## dataqueue

* framedata[n]
  * characterdata: iterable
    * tag: int
    * state
      * health: int
      * pos
        * x: float
        * y: float
      * faceDirVector
        * x: float
        * y: float
    * sight_object: iterable
      * type: BULLET=0, OBSTACLE_WALL=2, OBSTACLE_CRACK=3, OBSTACLE_FRAGILE=4
      * pos
        * x: float
        * y: float
    * sight_character: iterable
      * team: NEUTRAL=0, FRIEND=1, ENEMY=2
      * type: DUMMY=0, ROLLER=1, TANKER=2, HERMIT=3, ORB=4
      * pos
        * x: float
        * y: float
      * faceDir
        * x: float
        * y: float
  * framenumber: int
* turn: int
* sendtime: int
* recvlimittime: int