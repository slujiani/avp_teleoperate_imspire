import pyrealsense2 as rs

# 创建 RealSense 上下文
context = rs.context()

# 获取连接的设备列表
devices = context.query_devices()

if not devices:
    print("No RealSense camera detected.")
else:
    for device in devices:
        serial_number = device.get_info(rs.camera_info.serial_number)
        name = device.get_info(rs.camera_info.name)
        print(f"Device Name: {name}, Serial Number: {serial_number}")
