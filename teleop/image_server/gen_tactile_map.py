import matplotlib.pyplot as plt

import impire_hand_wr_tactile as hand_wr
import numpy as np
import cv2
from matplotlib import cm
# 自定义颜色映射（从白色到红色）
from matplotlib.colors import LinearSegmentedColormap

from image_server import RealSenseCamera

class leftHand:
    def __init__(self):
        self.MODBUS_IP = '172.16.11.210'
        self.MODBUS_PORT = 6000
        self.client = hand_wr.open_modbus(self.MODBUS_IP, self.MODBUS_PORT)
        if self.client.connect():
            print("连接成功！")
        else:
            print("连接失败！")
        self.PALM_ROWS = 50
        self.PALM_COLS = 36

    def _get_tactile(self):
        tactile_data = hand_wr.read_tactile(self.client)
        if tactile_data is None or len(tactile_data) == 0:
            print("Warning: No tactile data received!")
            return np.zeros(1062)  # 确保不会导致索引错误
        return tactile_data

    def create_palm_matrix(self,data, spacing=1):

        palm = np.zeros((self.PALM_ROWS, self.PALM_COLS))
        regions = [
            # 小拇指
            {"indices": (0, 9), "shape": (3, 3), "pos": (0, 0)},
            {"indices": (9, 105), "shape": (12, 8), "pos": (3 + spacing, 0)},
            {"indices": (105, 185), "shape": (10, 8), "pos": (15 + 2 * spacing, 0)},

            # 无名指
            {"indices": (185, 194), "shape": (3, 3), "pos": (0, 8 + spacing)},
            {"indices": (194, 290), "shape": (12, 8), "pos": (3 + spacing, 8 + spacing)},
            {"indices": (290, 370), "shape": (10, 8), "pos": (15 + 2 * spacing, 8 + spacing)},

            # 中指
            {"indices": (370, 379), "shape": (3, 3), "pos": (0, 16 + 2 * spacing)},
            {"indices": (379, 475), "shape": (12, 8), "pos": (3 + spacing, 16 + 2 * spacing)},
            {"indices": (475, 555), "shape": (10, 8), "pos": (15 + 2 * spacing, 16 + 2 * spacing)},

            # 食指
            {"indices": (555, 564), "shape": (3, 3), "pos": (0, 24 + 3 * spacing)},
            {"indices": (564, 660), "shape": (12, 8), "pos": (3 + spacing, 24 + 3 * spacing)},
            {"indices": (660, 740), "shape": (10, 8), "pos": (15 + 2 * spacing, 24 + 3 * spacing)},

            # 大拇指
            {"indices": (740, 749), "shape": (3, 3), "pos": (30, 0)},
            {"indices": (749, 845), "shape": (12, 8), "pos": (33 + spacing, 0)},
            {"indices": (845, 854), "shape": (3, 3), "pos": (30, 8 + spacing)},
            {"indices": (854, 950), "shape": (12, 8), "pos": (33 + spacing, 8 + spacing)},

            # 掌心
            {"indices": (950, 1062), "shape": (8, 14), "pos": (35, 18)}
        ]

        for reg in regions:
            start, end = reg["indices"]
            r, c = reg["pos"]
            rows, cols = reg["shape"]
            flat = np.array(data[start:end])  # 确保转换为 NumPy 数组
            if flat.size != rows * cols:
                print(
                    f"Warning: Data size mismatch for region {reg['indices']}. Expected {rows * cols}, got {flat.size}")
                continue
            matrix = flat.reshape(rows, cols)  # 现在不会报错了
            end_r = min(r + rows, self.PALM_ROWS)
            end_c = min(c + cols, self.PALM_COLS)
            palm[r:end_r, c:end_c] = matrix[:end_r - r, :end_c - c]

        return palm

    def tactile_map(self,color_img):
        tactile_data=self._get_tactile()
        palm_matrix=self.create_palm_matrix(tactile_data)
        #用tactile_data绘制热力图，数值越大，颜色越深，数值范围在0-4096 ，返回能和np.array格式转换之后的realsense d455获取的图像覆盖的格式
        # Normalize the tactile data to a range between 0 and 1
        norm_palm_matrix = palm_matrix/2048

        print("palm_matrix min:", np.min(palm_matrix), "max:", np.max(palm_matrix))
        print("norm_palm_matrix min:", np.min(norm_palm_matrix), "max:", np.max(norm_palm_matrix))

        # 创建自定义色图
        colors = [(1, 1, 1), (1, 0, 0)]  # 白色到红色
        n_bins = 100  # 色图的色阶
        cmap_name = 'white_to_red'
        custom_cmap = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)
        # 将归一化的触觉数据映射到自定义的色图
        colored_palm_matrix = custom_cmap(norm_palm_matrix)
        # 去除 alpha 通道，只保留 RGB 部分
        colored_palm_matrix = colored_palm_matrix[:, :, :3]
        # # Convert normalized tactile data to color map using jet colormap
        # cmap = plt.colormaps['jet']
        # print("jet(0):", cmap(0))

        # colored_palm_matrix = cmap(norm_palm_matrix)[:, :, :3]

        # 触觉图像大小
        tactile_width = color_img.shape[1] // 4  # 1/4 宽度
        tactile_height = color_img.shape[0] // 4  # 1/4 高度
        resized_tactile = cv2.resize(colored_palm_matrix, (tactile_width, tactile_height))
        # 转换为 8bit 格式
        tactile_img = (resized_tactile * 255).astype(np.uint8)

        # 计算放置坐标 (竖直中轴线左侧，上边缘贴齐)
        x_offset = (color_img.shape[1] // 2) - tactile_width  # 左侧紧贴中轴线
        y_offset = 0  # 上边缘对齐

        # 叠加图像
        overlay = color_img.copy()
        overlay[y_offset:y_offset + tactile_height, x_offset:x_offset + tactile_width] = tactile_img

        return overlay


if __name__ == "__main__":
    config = {
        'fps': 30,
        'head_camera_type': 'realsense',
        'head_camera_image_shape': [480, 640],  # Head camera resolution
        'head_camera_id_numbers': ['309122300773',],
        # 'wrist_camera_type': 'opencv',
        # 'wrist_camera_image_shape': [480, 640],  # Wrist camera resolution
        # 'wrist_camera_id_numbers': [2, 4],
    }
    fps = config.get('fps', 30)
    head_camera_type = config.get('head_camera_type', 'opencv')
    head_image_shape = config.get('head_camera_image_shape', [480, 640])  # (height, width)
    head_camera_id_numbers = config.get('head_camera_id_numbers', [0])
    head_cameras = []
    for serial_number in head_camera_id_numbers:
        camera = RealSenseCamera(img_shape=head_image_shape, fps=fps, serial_number=serial_number)
        head_cameras.append(camera)
    head_frames = []
    for cam in head_cameras:
        color_image, depth_image = cam.get_frame()
        if color_image is None:
            print("[Image Server] Head camera frame read is error.")
            break
        # 加上触觉热力图
    left_hand = leftHand()
    result_image = left_hand.tactile_map(color_image)
    # 保存图像到本地
    cv2.imwrite('result_image_holding_bottle.png', result_image)
    # Display the result image
    cv2.imshow('Tactile Heat Map on RGB Frame', result_image)


    cv2.waitKey(0)
    cv2.destroyAllWindows()






