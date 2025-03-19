from pymodbus.client.sync import ModbusTcpClient  # pip3 install pymodbus==2.5.3
from pymodbus.pdu import ExceptionResponse
import time
import copy

# 寄存器字典
regdict = {
    'ID': 1000,
    'baudrate': 1001,
    'clearErr': 1004,
    'forceClb': 1009,
    'angleSet': 1486,
    'forceSet': 1498,
    'speedSet': 1522,
    'angleAct': 1546,
    'forceAct': 1582,
    'errCode': 1606,
    'statusCode': 1612,
    'temp': 1618,
    'actionSeq': 2320,
    'actionRun': 2322,  # 运行当前动作序列
    'tactile': 3000
}

TOUCH_SENSOR_BASE_ADDR_PINKY = 3000  # 小拇指
TOUCH_SENSOR_END_ADDR_PINKY = 3369

TOUCH_SENSOR_BASE_ADDR_RING = 3370  # 无名指
TOUCH_SENSOR_END_ADDR_RING = 3739

TOUCH_SENSOR_BASE_ADDR_MIDDLE = 3740  # 中指
TOUCH_SENSOR_END_ADDR_MIDDLE = 4109

TOUCH_SENSOR_BASE_ADDR_INDEX = 4110  # 食指
TOUCH_SENSOR_END_ADDR_INDEX = 4479

TOUCH_SENSOR_BASE_ADDR_THUMB = 4480  # 大拇指
TOUCH_SENSOR_END_ADDR_THUMB = 4899

TOUCH_SENSOR_BASE_ADDR_PALM = 4900  # 掌心
TOUCH_SENSOR_END_ADDR_PALM = 5123
# Modbus 每次最多读取寄存器的数量

MAX_REGISTERS_PER_READ = 125


def open_modbus(ip, port):
    client = ModbusTcpClient(ip, port)
    client.connect()
    return client


def write_register(client, address, values):
    # Modbus 写入寄存器，传入寄存器地址和要写入的值列表
    client.write_registers(address, values)


def read_register(client, address, count):
    # Modbus 读取寄存器
    response = client.read_holding_registers(address, count)
    return response.registers if response.isError() is False else []


def write6(client, reg_name, val):
    if reg_name in ['angleSet', 'forceSet', 'speedSet']:
        val_reg = []
        for i in range(6):
            val_reg.append(val[i] & 0xFFFF)  # 取低16位
        write_register(client, regdict[reg_name], val_reg)
    else:
        print(
            '函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'，val为长度为6的list，值为0~1000，允许使用-1作为占位符')


def read6(client, reg_name):
    # 检查寄存器名称是否在允许的范围内
    if reg_name in ['angleSet', 'forceSet', 'speedSet', 'angleAct', 'forceAct']:
        # 直接读取与reg_name对应的寄存器，读取的数量为6
        val = read_register(client, regdict[reg_name], 6)
        if len(val) < 6:
            print('没有读到数据')
            return
        # print('读到的值依次为：', end='')
        return val

    elif reg_name in ['errCode', 'statusCode', 'temp']:
        # 读取错误代码、状态代码或温度，每次读取3个寄存器
        val_act = read_register(client, regdict[reg_name], 3)
        if len(val_act) < 3:
            print('没有读到数据')
            return

        # 初始化存储高低位的数组
        results = []

        # 将每个寄存器的高位和低位分开存储
        for i in range(len(val_act)):
            # 读取当前寄存器和下一个寄存器
            low_byte = val_act[i] & 0xFF  # 低八位
            high_byte = (val_act[i] >> 8) & 0xFF  # 高八位

            results.append(low_byte)  # 存储低八位
            results.append(high_byte)  # 存储高八位

        print('读到的值依次为：', end='')
        for v in results:
            print(v, end=' ')
        print()

    else:
        print(
            '函数调用错误，正确方式：str的值为\'angleSet\'/\'forceSet\'/\'speedSet\'/\'angleAct\'/\'forceAct\'/\'errCode\'/\'statusCode\'/\'temp\'')


# 读触觉
# def read_tactile(client):
#     tactile_data = []
#     while len(tactile_data) < 2124:
#         for addr in range(regdict['tactile'], 5124, 60):
#             remaining_registers = min(60, 5124 - addr)
#             response = client.read_holding_registers(addr, remaining_registers)
#
#             if response.isError():
#                 print(f"Failed to read from address: {addr}")
#                 continue
#
#             data = response.registers
#
#             for value in data:
#                 sensor_value = value
#                 tactile_data.append(sensor_value)
#     return tactile_data

def read_register_range(client, start_addr, end_addr):
    """
    批量读取指定地址范围内的寄存器数据。
    """
    register_values = []
    # 分段读取寄存器
    for addr in range(start_addr, end_addr + 1, MAX_REGISTERS_PER_READ * 2):

        current_count = min(MAX_REGISTERS_PER_READ, (end_addr - addr) // 2 + 1)


        response = client.read_holding_registers(address=addr, count=current_count)

        if isinstance(response, ExceptionResponse) or response.isError():
            print(f"读取寄存器 {addr} 失败: {response}")
            register_values.extend([0] * current_count)
        else:
            register_values.extend(response.registers)

    return register_values

def read_tactile(client):

    tactile_data = []
    pinky_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_PINKY,
        TOUCH_SENSOR_END_ADDR_PINKY
    )
    tactile_data.extend(copy.deepcopy(pinky_register_values))
    ring_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_RING,
        TOUCH_SENSOR_END_ADDR_RING
    )
    tactile_data.extend(copy.deepcopy(ring_register_values))
    middle_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_MIDDLE,
        TOUCH_SENSOR_END_ADDR_MIDDLE
    )
    tactile_data.extend(copy.deepcopy(middle_register_values))
    index_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_INDEX,
        TOUCH_SENSOR_END_ADDR_INDEX
    )
    tactile_data.extend(copy.deepcopy(index_register_values))
    thumb_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_THUMB,
        TOUCH_SENSOR_END_ADDR_THUMB
    )
    tactile_data.extend(copy.deepcopy(thumb_register_values))
    palm_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_PALM,
        TOUCH_SENSOR_END_ADDR_PALM
    )
    tactile_data.extend(copy.deepcopy(palm_register_values))
    return tactile_data





def read_multiple_registers(client):
    tactile_data = []
    # 读取各部分数据
    pinky_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_PINKY,
        TOUCH_SENSOR_END_ADDR_PINKY
    )

    ring_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_RING,
        TOUCH_SENSOR_END_ADDR_RING
    )

    middle_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_MIDDLE,
        TOUCH_SENSOR_END_ADDR_MIDDLE
    )

    index_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_INDEX,
        TOUCH_SENSOR_END_ADDR_INDEX
    )

    thumb_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_THUMB,
        TOUCH_SENSOR_END_ADDR_THUMB
    )

    palm_register_values = read_register_range(
        client,
        TOUCH_SENSOR_BASE_ADDR_PALM,
        TOUCH_SENSOR_END_ADDR_PALM
    )

    pinky_output_str = ", ".join(map(str, pinky_register_values))
    ring_output_str = ", ".join(map(str, ring_register_values))
    middle_output_str = ", ".join(map(str, middle_register_values))
    index_output_str = ", ".join(map(str, index_register_values))
    thumb_output_str = ", ".join(map(str, thumb_register_values))
    palm_output_str = ", ".join(map(str, palm_register_values))
    return  pinky_output_str,ring_output_str,middle_output_str,index_output_str,thumb_output_str,palm_output_str


    # if __name__ == '__main__':
    #     ip_address = '172.16.11.210'
    #     port = 6000
    #     print('打开Modbus TCP连接！')
    #     client = open_modbus(ip_address, port)
    #     if client.connect():
    #         print("连接成功！")
    #     else:
    #         print("连接失败！")
    # print('设置灵巧手运动速度参数，-1为不设置该运动速度！')
    # print('手掌触觉：')
    # readTactile(client,'palmTactile')
    # read6(client, 'temp')
    # time.sleep(1)

    # write6(client, 'speedSet', [100, 100, 100, 100, 100, 100])
    # time.sleep(2)
    #
    # print('设置灵巧手抓握力度参数！')
    # write6(client, 'forceSet', [500, 500, 500, 500, 500, 500])
    # time.sleep(1)
    #
    # print('设置灵巧手运动角度参数0，-1为不设置该运动角度！')
    # write6(client, 'angleSet', [0, 0, 0, 0, 400, -1])
    # time.sleep(3)


# read6(client, 'angleAct')
# time.sleep(1)

# # print('设置灵巧手运动角度参数1000，-1为不设置该运动角度！')
# # write6(client, 'angleSet', [1000, 1000, 1000, 1000, 1000, -1])
# # time.sleep(5)
# #
# # read6(client, 'angleAct')
# # time.sleep(1)
# #
# # print('故障信息：')
# # read6(client, 'errCode')
# # time.sleep(1)
# # print('电缸温度：')
# # read6(client, 'temp')
# # time.sleep(1)
#
# print('设置灵巧手动作库序列：2！')
# write_register(client, regdict['actionSeq'], [2])
# time.sleep(1)
#
# print('运行灵巧手当前序列动作！')
# write_register(client, regdict['actionRun'], [1])

# 关闭 Modbus TCP 连接
# client.close()