import cv2
import numpy as np
import argparse

def get_lab_thresholds(image_path, l_tol=0, c_tol=0):
    """
    分析图像并返回LAB颜色空间阈值，可配置亮度和颜色容差。
    
    参数:
        image_path (str): 输入图像的路径
        l_tol (float): L通道的容差值（亮度容差）
        c_tol (float): a和b通道的容差值（颜色容差）
        
    返回:
        tuple: (minL, maxL, minA, maxA, minB, maxB)
    """
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    # 将BGR转换为LAB
    lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    # 将LAB图像分割为L、A和B通道
    l_channel, a_channel, b_channel = cv2.split(lab_img)
    
    # 计算每个通道的最小值和最大值（OpenCV中的LAB值）
    min_l_cv = np.min(l_channel)
    max_l_cv = np.max(l_channel)
    min_a_cv = np.min(a_channel)
    max_a_cv = np.max(a_channel)
    min_b_cv = np.min(b_channel)
    max_b_cv = np.max(b_channel)
    
    # 将OpenCV的LAB值转换为标准LAB值
    # L: OpenCV范围[0,255] -> 标准范围[0,100]
    min_l = round(min_l_cv * 100 / 255, 2)
    max_l = round(max_l_cv * 100 / 255, 2)
    
    # a和b: OpenCV范围[0,255] -> 标准范围[-128,127]
    min_a = round(min_a_cv - 128, 2)
    max_a = round(max_a_cv - 128, 2)
    min_b = round(min_b_cv - 128, 2)
    max_b = round(max_b_cv - 128, 2)
    
    # 应用容差值
    min_l = max(0, min_l - l_tol)
    max_l = min(100, max_l + l_tol)
    min_a = max(-128, min_a - c_tol)
    max_a = min(127, max_a + c_tol)
    min_b = max(-128, min_b - c_tol)
    max_b = min(127, max_b + c_tol)
    
    return (min_l, max_l, min_a, max_a, min_b, max_b)

def main():
    parser = argparse.ArgumentParser(description='从图像获取LAB颜色空间阈值')
    parser.add_argument('path', help='输入图像的路径')
    parser.add_argument('-l', type=float, default=0, help='亮度容差值')
    parser.add_argument('-c', type=float, default=0, help='颜色容差值(a和b通道共用)')
    args = parser.parse_args()
    
    try:
        thresholds = get_lab_thresholds(args.path, args.l, args.c)
        print(f"({thresholds[0]},{thresholds[1]},{thresholds[2]},{thresholds[3]},{thresholds[4]},{thresholds[5]})")
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()