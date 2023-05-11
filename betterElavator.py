import random
import threading
import time
import sys
import parse
from PyQt5 import QtWidgets,QtCore
import ui_ElevatorDesign
import queue

# 输出信息
msg = "当前任务：\n"

# 定义一个电梯类
class Elevator:
    def __init__(self, id):
        self.lock = threading.Lock()
        self.id = id  # 电梯编号
        self.current_floor = 1  # 当前楼层
        self.direction = 0  # 电梯方向（0：静止，1：上行，-1：下行）
        self.status = '等待'  # 电梯状态
        self.door_status = '关闭'  # 电梯门状态
        self.alarm = False  # 是否有报警

        self.floor_queue = []  # 楼层队列，用来存放乘客按下的楼层

    # 打印电梯状态
    def print_status(self):
        print(
            f'{self.id}电梯，当前楼层：{self.current_floor}，方向：{self.direction}，状态：{self.status}，门状态：{self.door_status}，是否有报警：{self.alarm}')

    # 开门
    def open_door(self):
        global msg
        with self.lock:
            if self.status == '等待':
                self.door_status = '打开'
                print(f'{self.id}电梯门已打开')

                msg +=f"电梯{self.id}已开门，等待两秒\n"
                time.sleep(2)
                self.door_status = '关闭'
                print(f'{self.id}电梯门已关闭')
                msg +=f"电梯{self.id}已关闭\n"
            else:
                msg +=f"电梯{self.id}运行中，开门失败！\n"


    # 关门
    def close_door(self):
        global msg
        if self.status == '等待':
            self.door_status = '关闭'
            self.status = 0
            print(f'{self.id}电梯门已关闭')
            msg += f"电梯{self.id}已关闭\n"
        else:
            msg += f"电梯{self.id}运行中，关门失败！\n"


    # 上行
    def go_up(self):
        self.direction = 1
        self.status = '运行'
        print(f'{self.id}电梯上行')
        time.sleep(1)
        self.current_floor += 1
        print(f'{self.id}电梯到达{self.current_floor}楼')

    # 下行
    def go_down(self):
        self.direction = -1
        self.status = '运行'
        print(f'{self.id}电梯下行')
        time.sleep(1)
        self.current_floor -= 1
        print(f'{self.id}电梯到达{self.current_floor}楼')



    # 添加楼层到队列
    def add_floor_to_queue(self, floor):
        if floor not in self.floor_queue:
            self.floor_queue.append(floor)
            self.floor_queue.sort(reverse=True if self.direction == 1 else False)  # 根据方向排序

    # 从队列中移除楼层
    def remove_floor_from_queue(self, floor):
        if floor in self.floor_queue:
            self.floor_queue.remove(floor)


# 定义一个楼层类
class Floor:
    def __init__(self, number):
        self.number = number # 楼层号码
        self.up_button_status = False # 上行按钮状态
        self.down_button_status = False # 下行按钮状态
    # 打印楼层状态
    def print_status(self):
        print(f'{self.number}楼，上行按钮状态：{"开启" if self.up_button_status else "关闭"}，下行按钮状态：{"开启" if self.down_button_status else "关闭"}')

    def UpButOn(self):
        self.up_button_status = True


    def UpButOff(self):
        self.up_button_status = False

    def DownButOff(self):
        self.down_button_status = False

    def DownButOn(self):
        self.down_button_status = True

# 定义一个电梯调度类
class ElevatorScheduler:
    def __init__(self):
        self.elevators = [] # 电梯列表
        self.floors = [] # 楼层列表
        self.floortask = queue.Queue() # 外部任务列表
        self.lock = threading.Lock() # 保护楼层列表的安全
        self.elevator_threads = [] # 电梯线程列表
        # 初始化电梯和楼层
        for i in range(0,5):
            elevator = Elevator(f'{i+1}')
            self.elevators.append(elevator)
            thread = threading.Thread(target=self.elevator_thread, args=[elevator])
            self.elevator_threads.append(thread)
        # 第0个是被抛弃掉的
        for i in range(0, 21):
            floor = Floor(i)
            self.floors.append(floor)



# 启动电梯线程
    def start(self):
        for thread in self.elevator_threads:
            thread.start()

    def AddMissionRandomly(self,num):
        for i in range(num):
            missiontype = random.randint(1,5)
            floornum =random.randint(1,20)
            # 外部命令
            if missiontype == 0 :
               self.outtertask(floornum)
               self.OuterOrder(floornum,random.randint(0,1))
            else :
                assert missiontype>0
                assert missiontype<6
                self.InnerOrder(missiontype,floornum)


    def OuterOrder(self,floornum,option):
        outtertask = self.floors[floornum]
        with self.lock:
            # 如果是顶楼就只有下
            if floornum == 20:
                outtertask.DownButOn()
            # 如果是一楼就只有上
            elif floornum == 1:
                outtertask.UpButOn()
            else:
                outtertask.UpButOn() if option == 0 else outtertask.DownButOn()
            self.floortask.put_nowait(outtertask)
            global msg
            DIR = "上升"
            if option==1:
                DIR = "下降"
            msg +=f"添加任务：外部，{DIR}至{floornum}楼\n"


    def InnerOrder(self,elevatorID,floornum):
        self.elevators[elevatorID-1].add_floor_to_queue(floornum)
        global msg
        msg +=f"添加任务：{elevatorID}号电梯任务，前往{floornum}楼\n"


    # 电梯线程函数
    def elevator_thread(self, elevator):
        while True:
            # 打印电梯状态
            elevator.print_status()

            # 处理电梯队列中的楼层
            if len(elevator.floor_queue) > 0:
                floor = elevator.floor_queue[0]
                if floor == elevator.current_floor:  # 到达楼层
                    elevator.remove_floor_from_queue(floor)
                    global msg
                    msg +=f"电梯{int(elevator.id)}已到达楼层{floor},完成当前任务\n"

                    elevator.status = '等待'
                    if elevator.direction == 1:
                        self.floors[floor].UpButOff()
                    else:
                        self.floors[floor].DownButOff()
                    elevator.open_door()
                elif floor > elevator.current_floor:  # 上行
                    elevator.go_up()
                else:  # 下行
                    elevator.go_down()

            # 处理楼层按钮
            with self.lock:
                if not self.floortask.empty():
                    task = self.floortask.queue[0]
                else:
                    task =None
                if task is not None:
                    if elevator.direction == 1  and task.up_button_status:  # 上行按钮开启
                        elevator.add_floor_to_queue(task.number)
                        self.floortask.get_nowait()
                    elif elevator.direction == -1 and task.down_button_status:  # 下行按钮开启
                        elevator.add_floor_to_queue(task.number)
                        self.floortask.get_nowait()



            # 等待0.5秒
            time.sleep(0.5)



    # 打印电梯和楼层状态
    def print_status(self):
        for elevator in self.elevators:
            elevator.print_status()

        for floor in self.floors:
            floor.print_status()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,control):
        super().__init__()
        self.ui = ui_ElevatorDesign.Ui_Form()
        self.ui.setupUi(self)
        self.control = control

        self.elevator_buttons = [
            [self.ui.A_1_1, self.ui.A_2_1, self.ui.A_3_1, self.ui.A_4_1, self.ui.A_5_1, self.ui.A_6_1, self.ui.A_7_1,
             self.ui.A_8_1, self.ui.A_9_1, self.ui.A_10_1, self.ui.A_11_1, self.ui.A_12_1, self.ui.A_13_1,
             self.ui.A_14_1, self.ui.A_15_1, self.ui.A_16_1, self.ui.A_17_1, self.ui.A_18_1, self.ui.A_19_1,
             self.ui.A_20_1, ],
            [self.ui.A_1_2, self.ui.A_2_2, self.ui.A_3_2, self.ui.A_4_2, self.ui.A_5_2, self.ui.A_6_2, self.ui.A_7_2,
             self.ui.A_8_2, self.ui.A_9_2, self.ui.A_10_2, self.ui.A_11_2, self.ui.A_12_2, self.ui.A_13_2,
             self.ui.A_14_2, self.ui.A_15_2, self.ui.A_16_2, self.ui.A_17_2, self.ui.A_18_2, self.ui.A_19_2,
             self.ui.A_20_2, ],
            [self.ui.A_1_3, self.ui.A_2_3, self.ui.A_3_3, self.ui.A_4_3, self.ui.A_5_3, self.ui.A_6_3, self.ui.A_7_3,
             self.ui.A_8_3, self.ui.A_9_3, self.ui.A_10_3, self.ui.A_11_3, self.ui.A_12_3, self.ui.A_13_3,
             self.ui.A_14_3, self.ui.A_15_3, self.ui.A_16_3, self.ui.A_17_3, self.ui.A_18_3, self.ui.A_19_3,
             self.ui.A_20_3, ],
            [self.ui.A_1_4, self.ui.A_2_4, self.ui.A_3_4, self.ui.A_4_4, self.ui.A_5_4, self.ui.A_6_4, self.ui.A_7_4,
             self.ui.A_8_4, self.ui.A_9_4, self.ui.A_10_4, self.ui.A_11_4, self.ui.A_12_4, self.ui.A_13_4,
             self.ui.A_14_4, self.ui.A_15_4, self.ui.A_16_4, self.ui.A_17_4, self.ui.A_18_4, self.ui.A_19_4,
             self.ui.A_20_4, ],
            [self.ui.A_1_5, self.ui.A_2_5, self.ui.A_3_5, self.ui.A_4_5, self.ui.A_5_5, self.ui.A_6_5, self.ui.A_7_5,
             self.ui.A_8_5, self.ui.A_9_5, self.ui.A_10_5, self.ui.A_11_5, self.ui.A_12_5, self.ui.A_13_5,
             self.ui.A_14_5, self.ui.A_15_5, self.ui.A_16_5, self.ui.A_17_5, self.ui.A_18_5, self.ui.A_19_5,
             self.ui.A_20_5, ], ]
        self.Up_buttons =[self.ui.UP_1,self.ui.UP_2,self.ui.UP_3,self.ui.UP_4,self.ui.UP_5,self.ui.UP_6,self.ui.UP_7,self.ui.UP_8,self.ui.UP_9,self.ui.UP_10,self.ui.UP_11,self.ui.UP_12,self.ui.UP_13,self.ui.UP_14,self.ui.UP_15,self.ui.UP_16,self.ui.UP_17,self.ui.UP_18,self.ui.UP_19]
        self.Down_buttons = [self.ui.Down_2,self.ui.Down_3,self.ui.Down_4,self.ui.Down_5,self.ui.Down_6,self.ui.Down_7,self.ui.Down_8,self.ui.Down_9,self.ui.Down_10,self.ui.Down_11,self.ui.Down_12,self.ui.Down_13,self.ui.Down_14,self.ui.Down_15,self.ui.Down_16,self.ui.Down_17,self.ui.Down_18,self.ui.Down_19,self.ui.Down_20]

        self.LED =[self.ui.ALED_1,self.ui.ALED_2,self.ui.ALED_3,self.ui.ALED_4,self.ui.ALED_5]
        self.Open = [self.ui.Op_1,self.ui.Op_2,self.ui.Op_3,self.ui.Op_4,self.ui.Op_5]
        self.Close = [self.ui.CLO_1,self.ui.CLO_2,self.ui.CLO_3,self.ui.CLO_4,self.ui.CLO_5]
        self.timer = QtCore.QTimer()
        self.setUI()

    def setUI(self):
        for elevator_btns in self.elevator_buttons:
            for (i, btn) in enumerate(elevator_btns):
                btn.setText(f"{i + 1}")
                btn.clicked.connect(self.handle_elevator_button_clicked)

        for (i,Up_btn) in enumerate(self.Up_buttons):
            Up_btn.setText("↑")
            Up_btn.clicked.connect(self.handle_Up_buttons)

        for (i,Down_btn) in enumerate(self.Down_buttons):
            Down_btn.setText("↓")
            Down_btn.clicked.connect(self.handle_Down_buttons)

        for(i,btn) in enumerate(self.Open):
            btn.setText("开门")
            btn.clicked.connect(self.handle_Open_buttons)

        for (i, btn) in enumerate(self.Close):
            btn.setText("关门")
            btn.clicked.connect(self.handle_Close_buttons)

        self.ui.Mission.clicked.connect(self.add_mission_randomly)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.UpdateUI)
        self.timer.start()

    # 实时更新UI
    def UpdateUI(self):
        # 更新当前楼层
        for(i,LEDName) in enumerate(self.LED):
            LEDName.display(control.elevators[i].current_floor)
        # 更新当前信息
        self.ui.MissionText.setText(msg)

    def handle_elevator_button_clicked(self):
        btn=self.sender()
        name = btn.objectName()
        btn_info = parse.parse("A_{}_{}",name)
        control.InnerOrder(int(btn_info[1]),int(btn_info[0]))
        global msg
        msg+=(f"{btn_info[1]}号电梯{btn_info[0]}楼按钮已被按下!\n")

    def handle_Up_buttons(self):
        Upbtn=self.sender()
        name = Upbtn.objectName()
        Upbtn_info = parse.parse("UP_{}",name)
        global msg
        msg += (f"{Upbtn_info[0]}楼向上按钮已被按下！\n")
        control.OuterOrder(int(Upbtn_info[0]),0)


    def handle_Down_buttons(self):
        Downbtn = self.sender()
        name = Downbtn.objectName()
        Downbtn_info = parse.parse("DOWN_{}", name)
        global msg
        msg += (f"{Downbtn_info[0]}楼向下按钮已被按下！\n")
        control.OuterOrder(int(Downbtn_info[0]),1)


    def handle_Open_buttons(self):
        btn = self.sender()
        name = btn.objectName()
        btninfo = parse.parse("Op_{}",name)
        if self.control.elevators[int(btninfo[0])].status == '等待':
            global msg
            msg += (f"{btninfo[0]}号电梯开门按钮已被按下！\n")
            tmp =int(btninfo[0])-1
            self.control.elevators[tmp].open_door()


    def handle_Close_buttons(self):
        btn = self.sender()
        name = btn.objectName()
        btninfo = parse.parse("CLO_{}", name)
        global msg
        msg += (f"{btninfo[0]}号电梯关门按钮已被按下！\n")
        tmp = int(btninfo[0]) - 1
        self.control.elevators[tmp].close_door()

    def add_mission_randomly(self):
        print("Click misson button")
        self.control.AddMissionRandomly(5)


if __name__=="__main__":
   app = QtWidgets.QApplication(sys.argv)
   control = ElevatorScheduler()
   mw = MainWindow(control)
   mw.show()
   mw.control.start()
   sys.exit(app.exec_())



