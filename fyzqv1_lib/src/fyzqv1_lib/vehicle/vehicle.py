#!/usr/bin/env python3

import struct
import time
import serial
import threading

class Vehicle:
    __uart_state = 0

    def __init__(self, car_type=0x05, com="/dev/myserial", delay=.002, debug=False):
               
        self.ser = serial.Serial(com, 115200)

        self.__delay_time = delay
        self.__debug = debug

        self.__HEAD = 0xFF
        self.__DEVICE_ID = 0xFC
        self.__COMPLEMENT = 257 - self.__DEVICE_ID
        self.__CAR_TYPE = car_type
        self.__CAR_ADJUST = 0x80

        self.FUNC_AUTO_REPORT = 0x01
        self.FUNC_BEEP = 0x02
        self.FUNC_PWM_SERVO = 0x03
        self.FUNC_PWM_SERVO_ALL = 0x04
        self.FUNC_RGB = 0x05
        self.FUNC_RGB_EFFECT = 0x06

        self.FUNC_REPORT_SPEED = 0x0A
        self.FUNC_REPORT_IMU_ATT = 0x0C
        self.FUNC_REPORT_ENCODER = 0x0D
        self.FUNC_REPORT_ICM_RAW = 0x0E
        
        self.FUNC_RESET_STATE = 0x0F

        self.FUNC_MOTOR = 0x10
        self.FUNC_CAR_RUN = 0x11
        self.FUNC_MOTION = 0x12
        self.FUNC_SET_MOTOR_PID = 0x13
        self.FUNC_SET_CAR_TYPE = 0x15

        self.FUNC_AKM_DEF_ANGLE = 0x30
        self.FUNC_AKM_STEER_ANGLE = 0x31

        self.FUNC_REQUEST_DATA = 0x50
        self.FUNC_VERSION = 0x51

        self.FUNC_RESET_FLASH = 0xA0

        self.CARTYPE_FYZQV1 = 0x05

        self.__ax = 0.0
        self.__ay = 0.0
        self.__az = 0.0
        self.__gx = 0.0
        self.__gy = 0.0
        self.__gz = 0.0
        self.__mx = 0.0
        self.__my = 0.0
        self.__mz = 0.0
        self.__vx = 0.0
        self.__vy = 0.0
        self.__vz = 0.0

        self.__yaw = 0.0
        self.__roll = 0.0
        self.__pitch = 0.0

        self.__encoder_m1 = 0
        self.__encoder_m2 = 0
        self.__encoder_m3 = 0
        self.__encoder_m4 = 0

        self.__version_H = 0
        self.__version_L = 0
        self.__version = 0

        self.__pid_index = 0
        self.__kp1 = 0
        self.__ki1 = 0
        self.__kd1 = 0

        self.__battery_voltage = 0

        self.__akm_def_angle = 100
        self.__akm_readed_angle = False
        self.__AKM_SERVO_ID = 0x01

        self.__read_car_type = 0

        if self.__debug:
            print("cmd_delay=" + str(self.__delay_time) + "s")

        if self.ser.is_open:
            print("Vehicle Serial Opened! Baudrate=115200")
        else:
            print("Vehicle Serial Open Failed!")
            
    def __del__(self):
        self.ser.close()
        self.__uart_state = 0
        print("serial Close!")

    # 根据数据帧的类型来做出对应的解析
    def __parse_data(self, ext_type, ext_data):
        if ext_type == self.FUNC_REPORT_SPEED:
            self.__vx = int(struct.unpack('h', bytearray(ext_data[0:2]))[0]) / 1000.0
            self.__vy = int(struct.unpack('h', bytearray(ext_data[2:4]))[0]) / 1000.0
            self.__vz = int(struct.unpack('h', bytearray(ext_data[4:6]))[0]) / 1000.0
            self.__battery_voltage = struct.unpack('B', bytearray(ext_data[6:7]))[0]

            # 解析ICM20948原始陀螺仪、加速度计、磁力计数据
        elif ext_type == self.FUNC_REPORT_ICM_RAW:
            gyro_ratio = 1 / 1000.0
            self.__gx = struct.unpack('h', bytearray(ext_data[0:2]))[0]*gyro_ratio
            self.__gy = struct.unpack('h', bytearray(ext_data[2:4]))[0]*gyro_ratio
            self.__gz = struct.unpack('h', bytearray(ext_data[4:6]))[0]*gyro_ratio

            accel_ratio = 1 / 1000.0
            self.__ax = struct.unpack('h', bytearray(ext_data[6:8]))[0]*accel_ratio
            self.__ay = struct.unpack('h', bytearray(ext_data[8:10]))[0]*accel_ratio
            self.__az = struct.unpack('h', bytearray(ext_data[10:12]))[0]*accel_ratio

            mag_ratio = 1 / 1000.0
            self.__mx = struct.unpack('h', bytearray(ext_data[12:14]))[0]*mag_ratio
            self.__my = struct.unpack('h', bytearray(ext_data[14:16]))[0]*mag_ratio
            self.__mz = struct.unpack('h', bytearray(ext_data[16:18]))[0]*mag_ratio

        # 解析板子的姿态角
        elif ext_type == self.FUNC_REPORT_IMU_ATT:
            self.__roll = struct.unpack('h', bytearray(ext_data[0:2]))[0] / 10000.0
            self.__pitch = struct.unpack('h', bytearray(ext_data[2:4]))[0] / 10000.0
            self.__yaw = struct.unpack('h', bytearray(ext_data[4:6]))[0] / 10000.0
            
        # 解析四个轮子的编码器数据
        elif ext_type == self.FUNC_REPORT_ENCODER:
            self.__encoder_m1 = struct.unpack('i', bytearray(ext_data[0:4]))[0]
            self.__encoder_m2 = struct.unpack('i', bytearray(ext_data[4:8]))[0]
            self.__encoder_m3 = struct.unpack('i', bytearray(ext_data[8:12]))[0]
            self.__encoder_m4 = struct.unpack('i', bytearray(ext_data[12:16]))[0]

        elif ext_type == self.FUNC_VERSION:
            self.__version_H = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__version_L = struct.unpack('B', bytearray(ext_data[1:2]))[0]
            if self.__debug:
                print("FUNC_VERSION:", self.__version_H, self.__version_L)

        elif ext_type == self.FUNC_SET_MOTOR_PID:
            self.__pid_index = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__kp1 = struct.unpack('h', bytearray(ext_data[1:3]))[0]
            self.__ki1 = struct.unpack('h', bytearray(ext_data[3:5]))[0]
            self.__kd1 = struct.unpack('h', bytearray(ext_data[5:7]))[0]
            if self.__debug:
                print("FUNC_SET_MOTOR_PID:", self.__pid_index, [self.__kp1, self.__ki1, self.__kd1])

        elif ext_type == self.FUNC_AKM_DEF_ANGLE:
            id = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__akm_def_angle = struct.unpack('B', bytearray(ext_data[1:2]))[0]
            self.__akm_readed_angle = True
            if self.__debug:
                print("FUNC_AKM_DEF_ANGLE:", id, self.__akm_def_angle)
            
        elif ext_type == self.FUNC_SET_CAR_TYPE:
            car_type = struct.unpack('B', bytearray(ext_data[0:1]))[0]
            self.__read_car_type = car_type

    # 接收数据
    def __receive_data(self):
        # 清空缓冲区
        self.ser.reset_input_buffer()
        while True:
            head1 = bytearray(self.ser.read())[0]
            if head1 == self.__HEAD:
                head2 = bytearray(self.ser.read())[0]
                check_sum = 0
                rx_check_num = 0
                if head2 == self.__DEVICE_ID - 1:
                    ext_len = bytearray(self.ser.read())[0]
                    ext_type = bytearray(self.ser.read())[0]
                    ext_data = []
                    check_sum = ext_len + ext_type
                    data_len = ext_len - 2
                    while len(ext_data) < data_len:
                        value = bytearray(self.ser.read())[0]
                        ext_data.append(value)
                        if len(ext_data) == data_len:
                            rx_check_num = value
                        else:
                            check_sum = check_sum + value
                    if check_sum % 256 == rx_check_num:
                        self.__parse_data(ext_type, ext_data)
                    else:
                        if self.__debug:
                            print("check sum error:", ext_len, ext_type, ext_data)

    # 请求数据， function：对应要返回数据的功能字，param：传入的参数
    def __request_data(self, function, param=0):
        cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_REQUEST_DATA, int(function) & 0xff, int(param) & 0xff]
        checksum = sum(cmd, self.__COMPLEMENT) & 0xff
        cmd.append(checksum)
        self.ser.write(cmd)
        if self.__debug:
            print("request:", cmd)
        time.sleep(0.002)

    # 限制电机输入的PWM占空比数值，value=127则保持原来的数据，不修改当前电机速度
    def __limit_motor_value(self, value):
        if value == 127:
            return 127
        elif value > 100:
           return 100
        elif value < -100:
            return -100
        else:
            return int(value)

    # 开启接收和处理数据的线程
    def create_receive_threading(self):
        try:
            if self.__uart_state == 0:
                name1 = "task_serial_receive"
                task_receive = threading.Thread(target=self.__receive_data, name=name1)
                task_receive.daemon = True
                task_receive.start()
                print("----------------create receive threading--------------")
                self.__uart_state = 1
                time.sleep(.05)
        except:
            print('---create_receive_threading error!---')
            pass
    
    # 单片机自动返回数据状态位，默认为开启，如果设置关闭会影响部分读取数据功能
    # enable=True,底层扩展板会每隔10毫秒发送一包数据，总共四包不同数据，所以每包数据每40毫秒刷新一次。enable=False，则不发送
    # forever=True永久保存，=False临时作用
    def set_auto_report_state(self, enable, forever=False):
        try:
            state1 = 0
            state2 = 0
            if enable:
                state1 = 1
            if forever:
                state2 = 0x5F
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_AUTO_REPORT, state1, state2]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("report:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_auto_report_state error!---')
            pass

    # 蜂鸣器开关，on_time=0：关闭，on_time=1：一直响
    # on_time>=10：响xx毫秒后自动关闭（on_time是10的倍数）
    def set_beep(self, on_time):
        try:
            if on_time < 0:
                print("beep input error!")
                return
            value = bytearray(struct.pack('h', int(on_time)))

            cmd = [self.__HEAD, self.__DEVICE_ID, 0x05, self.FUNC_BEEP, value[0], value[1]]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("beep:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_beep error!---')
            pass

    # PWM舵机控制，servo_id：舵机通道编号，angle：舵机角度
    # servo_id范围：[1, 4]，angle范围：[0, 180]
    def set_pwm_servo(self, servo_id, angle):
        try:
            if servo_id < 1 or servo_id > 4:
                if self.__debug:
                    print("set_pwm_servo input invalid")
                return
            if angle > 180:
                angle = 180
            elif angle < 0:
                angle = 0
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_PWM_SERVO, int(servo_id), int(angle)]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("pwmServo:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_pwm_servo error!---')
            pass

    # 同时控制四路PWM的角度，angle_sX=[0, 180]
    def set_pwm_servo_all(self, angle_s1, angle_s2, angle_s3, angle_s4):
        try:
            if angle_s1 < 0 or angle_s1 > 180:
                angle_s1 = 255
            if angle_s2 < 0 or angle_s2 > 180:
                angle_s2 = 255
            if angle_s3 < 0 or angle_s3 > 180:
                angle_s3 = 255
            if angle_s4 < 0 or angle_s4 > 180:
                angle_s4 = 255
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_PWM_SERVO_ALL, \
                   int(angle_s1), int(angle_s2), int(angle_s3), int(angle_s4)]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("all Servo:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_pwm_servo_all error!---')
            pass

    # RGB可编程灯带控制，可单独控制或全体控制，控制前需要先停止RGB灯特效。
    # led_id=[0, 13]，控制对应编号的RGB灯；led_id=0xFF, 控制所有灯。
    # red,green,blue=[0, 255]，表示颜色RGB值。
    def set_colorful_lamps(self, led_id, red, green, blue):
        try:
            id = int(led_id) & 0xff
            r = int(red) & 0xff
            g = int(green) & 0xff
            b = int(blue) & 0xff
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_RGB, id, r, g, b]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("rgb:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_colorful_lamps error!---')
            pass

    # RGB可编程灯带特效展示
    # effect=[0, 6]，0：停止灯效，1：流水灯，2：跑马灯，3：呼吸灯，4：渐变灯，5：星光点点，6：电量显示
    # speed=[1, 10]，数值越小速度变化越快
    # parm，可不填，作为附加参数。用法1：呼吸灯效果传入[0, 6]可修改呼吸灯颜色

    def set_colorful_effect(self, effect, speed=255, parm=255):
        try:
            eff = int(effect) & 0xff
            spe = int(speed) & 0xff
            par = int(parm) & 0xff
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_RGB_EFFECT, eff, spe, par]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("rgb_effect:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_colorful_effect error!---')
            pass

    # 控制电机PWM脉冲，从而控制速度（未使用编码器测速）。speed_X=[-100, 100]
    def set_motor(self, speed_1, speed_2, speed_3, speed_4):
        try:
            t_speed_a = bytearray(struct.pack('b', self.__limit_motor_value(speed_1)))
            t_speed_b = bytearray(struct.pack('b', self.__limit_motor_value(speed_2)))
            t_speed_c = bytearray(struct.pack('b', self.__limit_motor_value(speed_3)))
            t_speed_d = bytearray(struct.pack('b', self.__limit_motor_value(speed_4)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_MOTOR,
                   t_speed_a[0], t_speed_b[0], t_speed_c[0], t_speed_d[0]]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("motor:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_motor error!---')
            pass

    # 控制小车向前、向后、向左、向右等运动
    # state=[0, 7],=0停止,=1前进,=2后退,=3向左,=4向右,=5左旋,=6右旋,=7停车
    # speed=[-100, 100]，=0停止
    # adjust=True开启陀螺仪辅助运动方向。=False则不开启。(此功能未开通)
    def set_car_run(self, state, speed, adjust=False):
        try:
            car_type = self.__CAR_TYPE
            if adjust:
                car_type = car_type | self.__CAR_ADJUST
            t_speed = bytearray(struct.pack('h', int(speed)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_CAR_RUN, \
                car_type, int(state&0xff), t_speed[0], t_speed[1]]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("car_run:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_car_run error!---')
            pass

    # 小车运动控制, 
    def set_car_motion(self, v_x, v_y, v_z):
        '''
        输入范围 input range: 
        fyzqv1：v_x=[-1.8, 1.8], v_y=[-0.045, 0.045], v_z=[-3, 3]
        '''
        try:
            vx_parms = bytearray(struct.pack('h', int(v_x*1000)))
            vy_parms = bytearray(struct.pack('h', int(v_y*1000)))
            vz_parms = bytearray(struct.pack('h', int(v_z*1000)))
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_MOTION, self.__CAR_TYPE, \
                vx_parms[0], vx_parms[1], vy_parms[0], vy_parms[1], vz_parms[0], vz_parms[1]]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("motion:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_car_motion error!---')
            pass

    # PID 参数控制，会影响set_car_motion函数控制小车的运动速度变化情况。默认情况下可不调整
    # kp ki kd = [0, 10.00], 可输入小数
    # forever=True永久保存，=False临时作用
    # 由于永久保存需要写入芯片flash中，操作时间较长，所以加入delay延迟时间，避免导致单片机丢包的问题。
    # 临时作用反应快，单次有效，重启单片后数据不再保持
    def set_pid_param(self, kp, ki, kd, forever=False):
        try:
            state = 0
            if forever:
                state = 0x5F
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x0A, self.FUNC_SET_MOTOR_PID]
            if kp > 10 or ki > 10 or kd > 10 or kp < 0 or ki < 0 or kd < 0:
                print("PID value must be:[0, 10.00]")
                return
            kp_params = bytearray(struct.pack('h', int(kp * 1000)))
            ki_params = bytearray(struct.pack('h', int(ki * 1000)))
            kd_params = bytearray(struct.pack('h', int(kd * 1000)))
            cmd.append(kp_params[0])  # low
            cmd.append(kp_params[1])  # high
            cmd.append(ki_params[0])  # low
            cmd.append(ki_params[1])  # high
            cmd.append(kd_params[0])  # low
            cmd.append(kd_params[1])  # high
            cmd.append(state)
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("pid:", cmd)
            time.sleep(self.__delay_time)
            if forever:
                time.sleep(.1)
        except:
            print('---set_pid_param error!---')
            pass

    # 设置小车类型
    def set_car_type(self, car_type):
        if str(car_type).isdigit():
            self.__CAR_TYPE = int(car_type) & 0xff
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_SET_CAR_TYPE, self.__CAR_TYPE, 0x5F]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("car_type:", cmd)
            time.sleep(.1)
        else:
            print("set_car_type input invalid")

    # 设置阿克曼小车前轮的默认角度，angle=[60, 120]
    # forever=True永久保存，=False临时作用
    # 由于永久保存需要写入芯片flash中，操作时间较长，所以加入delay延迟时间，避免导致单片机丢包的问题
    # 临时作用反应快，单次有效，重启单片后数据不再保持
    def set_akm_default_angle(self, angle, forever=False):
        try:
            if int(angle) > 120 or int(angle) < 60:
                return
            id = self.__AKM_SERVO_ID
            state = 0
            if forever:
                state = 0x5F
                self.__akm_def_angle = angle
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_AKM_DEF_ANGLE, id, int(angle), state]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("akm set def angle:", cmd)
            time.sleep(self.__delay_time)
            if forever:
                time.sleep(.1)
        except:
            print('---set_akm_default_angle error!---')
            pass

    # 控制阿克曼小车相对于默认角度的转向角，向左为负数，向右为正数，angle=[-45, 45]
    # ctrl_car=False，只控制舵机角度，=True，控制舵机角度同时修改左右电机的速度
    def set_akm_steering_angle(self, angle, ctrl_car=False):
        try:
            if int(angle) > 45 or int(angle) < -45:
                return
            id = self.__AKM_SERVO_ID
            if ctrl_car:
                id = self.__AKM_SERVO_ID + 0x80
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x00, self.FUNC_AKM_STEER_ANGLE, id, int(angle)&0xFF]
            cmd[2] = len(cmd) - 1
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("akm_steering_angle:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---set_akm_steering_angle error!---')
            pass

    # 重置小车flash保存的数据，恢复出厂默认值。
    # Reset the car flash saved data, restore the factory default value
    def reset_flash_value(self):
        try:
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x04, self.FUNC_RESET_FLASH, 0x5F]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("flash:", cmd)
            time.sleep(self.__delay_time)
            time.sleep(.1)
        except:
            print('---reset_flash_value error!---')
            pass

    # 重置小车状态，包括停车，关灯，关蜂鸣器
    def reset_car_state(self):
        try:
            cmd = [self.__HEAD, self.__DEVICE_ID, 0x04, self.FUNC_RESET_STATE, 0x5F]
            checksum = sum(cmd, self.__COMPLEMENT) & 0xff
            cmd.append(checksum)
            self.ser.write(cmd)
            if self.__debug:
                print("reset_car_state:", cmd)
            time.sleep(self.__delay_time)
        except:
            print('---reset_car_state error!---')
            pass

    # 清除单片机自动发送过来的缓存数据
    def clear_auto_report_data(self):
        self.__battery_voltage = 0
        self.__ax = 0.0
        self.__ay = 0.0
        self.__az = 0.0
        self.__gx = 0.0
        self.__gy = 0.0
        self.__gz = 0.0
        self.__mx = 0.0
        self.__my = 0.0
        self.__mz = 0.0
        self.__vx = 0.0
        self.__vy = 0.0
        self.__vz = 0.0
        self.__yaw = 0.0
        self.__roll = 0.0
        self.__pitch = 0.0

    # 读取阿克曼小车前轮舵机默认角度
    def get_akm_default_angle(self):
        if not self.__akm_readed_angle:
            self.__request_data(self.FUNC_AKM_DEF_ANGLE, self.__AKM_SERVO_ID)
            akm_count = 0
            while True:
                if self.__akm_readed_angle:
                    break
                akm_count = akm_count + 1
                if akm_count > 100:
                    return -1
                time.sleep(.01)
        return self.__akm_def_angle

    # 获取加速度计三轴数据，返回a_x, a_y, a_z
    def get_accelerometer_data(self):
        a_x, a_y, a_z = self.__ax, self.__ay, self.__az
        return a_x, a_y, a_z

    # 获取陀螺仪三轴数据，返回g_x, g_y, g_z
    def get_gyroscope_data(self):
        g_x, g_y, g_z = self.__gx, self.__gy, self.__gz
        return g_x, g_y, g_z

    # 获取磁力计三轴数据，返回m_x, m_y, m_z
    def get_magnetometer_data(self):
        m_x, m_y, m_z = self.__mx, self.__my, self.__mz
        return m_x, m_y, m_z

    # 获取板子姿态角，返回yaw, roll, pitch
    # ToAngle=True返回角度，ToAngle=False返回弧度。
    def get_imu_attitude_data(self, ToAngle=True):
        if ToAngle:
            RtA = 57.2957795
            roll = self.__roll * RtA
            pitch = self.__pitch * RtA
            yaw = self.__yaw * RtA
        else:
            roll, pitch, yaw = self.__roll, self.__pitch, self.__yaw
        return roll, pitch, yaw

    # 获取小车速度，val_vx, val_vy, val_vz
    def get_motion_data(self):
        val_vx = self.__vx
        val_vy = self.__vy
        val_vz = self.__vz
        return val_vx, val_vy, val_vz

    # 获取电池电压值
    def get_battery_voltage(self):
        vol = self.__battery_voltage / 10.0
        return vol

    # 获取四路电机编码器数据
    def get_motor_encoder(self):
        m1, m2, m3, m4 = self.__encoder_m1, self.__encoder_m2, self.__encoder_m3, self.__encoder_m4
        return m1, m2, m3, m4

    # 获取小车的运动PID参数, 返回[kp, ki, kd]
    def get_motion_pid(self):
        self.__kp1 = 0
        self.__ki1 = 0
        self.__kd1 = 0
        self.__pid_index = 0
        self.__request_data(self.FUNC_SET_MOTOR_PID, int(1))
        for i in range(20):
            if self.__pid_index > 0:
                kp = float(self.__kp1 / 1000.0)
                ki = float(self.__ki1 / 1000.0)
                kd = float(self.__kd1 / 1000.0)
                if self.__debug:
                    print("get_motion_pid: {0}, {1}, {2}".format(self.__pid_index, [kp, ki, kd], i))
                return [kp, ki, kd]
            time.sleep(.001)
        return [-1, -1, -1]

    # 获取当前底层小车类型
    def get_car_type_from_machine(self):
        self.__request_data(self.FUNC_SET_CAR_TYPE)
        for i in range(0, 20):
            if self.__read_car_type != 0:
                car_type = self.__read_car_type
                self.__read_car_type = 0
                return car_type
            time.sleep(.001)
        return -1

    # 获取底层单片机版本号
    def get_version(self):
        if self.__version_H == 0:
            self.__request_data(self.FUNC_VERSION)
            for i in range(0, 20):
                if self.__version_H != 0:
                    val = self.__version_H * 1.0
                    self.__version = val + self.__version_L / 10.0
                    if self.__debug:
                        print("get_version:V{0}, i:{1}".format(self.__version, i))
                    return self.__version
                time.sleep(.001)
        else:
            return self.__version
        return -1

