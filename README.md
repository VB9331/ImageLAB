# LAB颜色阈值提取器

这个工具用于分析图像并输出标准LAB颜色空间阈值，格式为：(minL,maxL,minA,maxA,minB,maxB)。

## LAB颜色空间说明
- L（亮度）：范围0-100，0为纯黑，100为纯白
- a（红绿色度）：范围-128至+127，正值偏红，负值偏绿
- b（黄蓝色度）：范围-128至+127，正值偏黄，负值偏蓝

## 环境要求

- Python 3.x
- OpenCV (cv2)
- NumPy
- PyQt5 (仅GUI版本需要)

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行版本

基本用法：
```bash
python lab_threshold.py 图像路径/图像名称.jpg
```

带容差的用法：
```bash
python lab_threshold.py 图像路径/图像名称.jpg -l 5 -c 10
```

参数说明：
- `path`：输入图像的路径（必需参数）
- `-l`：亮度容差值（L通道，默认为0）
- `-c`：颜色容差值（a和b通道共用，默认为0）

### 图形界面版本

启动图形界面：
```bash
python lab_threshold_gui.py
```

功能：
- 上传图片：从本地选择图片文件
- 打开相机：使用电脑摄像头实时预览
- 截图：捕获当前相机画面
- 剪裁：选择图像中的特定区域进行分析
- 重置图像：恢复到原始上传或截图的图像
- 设置容差：调整亮度和颜色容差
- 计算阈值：分析图像并显示LAB阈值
- 复制结果：一键复制阈值结果到剪贴板

#### 剪裁功能使用方法
1. 点击"剪裁"按钮进入剪裁模式
2. 在图像上按住鼠标左键并拖动选择要剪裁的区域
3. 释放鼠标左键完成剪裁

#### 复制结果功能
1. 计算阈值后，点击"复制结果"按钮
2. 阈值结果将自动复制到系统剪贴板
3. 可以直接粘贴到其他应用程序中使用

## 输出格式

输出格式为：(minL,maxL,minA,maxA,minB,maxB)

示例：
```
(10.59,90.2,15.63,-20.78,30.2,-5.49)
```