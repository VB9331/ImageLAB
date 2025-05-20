import sys
import cv2
import numpy as np
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                            QSlider, QLineEdit, QGroupBox, QMessageBox, QRubberBand,
                            QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QCursor
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QSize, QMimeData
from PyQt5.QtWidgets import QApplication

class LABThresholdApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.img = None
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # 剪裁相关变量
        self.cropping = False
        self.crop_origin = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.image_label)
        self.cropped_img = None
        
        # 阈值结果
        self.threshold_result = ""
        
        # 固定图像大小
        self.fixed_width = 640
        self.fixed_height = 480
        
    def initUI(self):
        self.setWindowTitle('LAB颜色阈值提取器')
        self.setGeometry(100, 100, 900, 800)  # 增大窗口默认大小
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建滚动区域来容纳图像
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 图像显示区域
        self.image_label = QLabel('请选择或拍摄图像')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(640, 480)  # 设置固定的最小大小
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.start_crop
        self.image_label.mouseMoveEvent = self.update_crop
        self.image_label.mouseReleaseEvent = self.end_crop
        
        # 将图像标签放入滚动区域
        scroll_area.setWidget(self.image_label)
        main_layout.addWidget(scroll_area)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton('上传图片')
        self.upload_btn.clicked.connect(self.upload_image)
        button_layout.addWidget(self.upload_btn)
        
        self.camera_btn = QPushButton('打开相机')
        self.camera_btn.clicked.connect(self.toggle_camera)
        button_layout.addWidget(self.camera_btn)
        
        self.capture_btn = QPushButton('截图')
        self.capture_btn.clicked.connect(self.capture_image)
        self.capture_btn.setEnabled(False)
        button_layout.addWidget(self.capture_btn)
        
        self.crop_btn = QPushButton('剪裁')
        self.crop_btn.clicked.connect(self.toggle_crop_mode)
        self.crop_btn.setEnabled(False)
        button_layout.addWidget(self.crop_btn)
        
        self.reset_btn = QPushButton('重置图像')
        self.reset_btn.clicked.connect(self.reset_image)
        self.reset_btn.setEnabled(False)
        button_layout.addWidget(self.reset_btn)
        
        main_layout.addLayout(button_layout)
        
        # 容差设置区域
        tolerance_group = QGroupBox('容差设置')
        tolerance_layout = QVBoxLayout()
        
        # 亮度容差
        l_layout = QHBoxLayout()
        l_layout.addWidget(QLabel('亮度容差:'))
        self.l_slider = QSlider(Qt.Horizontal)
        self.l_slider.setRange(0, 50)
        self.l_slider.setValue(0)
        self.l_slider.valueChanged.connect(self.update_l_value)
        l_layout.addWidget(self.l_slider)
        self.l_value = QLineEdit('0')
        self.l_value.setMaximumWidth(50)
        self.l_value.textChanged.connect(self.set_l_slider)
        l_layout.addWidget(self.l_value)
        tolerance_layout.addLayout(l_layout)
        
        # 颜色容差
        c_layout = QHBoxLayout()
        c_layout.addWidget(QLabel('颜色容差:'))
        self.c_slider = QSlider(Qt.Horizontal)
        self.c_slider.setRange(0, 50)
        self.c_slider.setValue(0)
        self.c_slider.valueChanged.connect(self.update_c_value)
        c_layout.addWidget(self.c_slider)
        self.c_value = QLineEdit('0')
        self.c_value.setMaximumWidth(50)
        self.c_value.textChanged.connect(self.set_c_slider)
        c_layout.addWidget(self.c_value)
        tolerance_layout.addLayout(c_layout)
        
        tolerance_group.setLayout(tolerance_layout)
        main_layout.addWidget(tolerance_group)
        
        # 结果显示区域
        result_group = QGroupBox('LAB阈值结果')
        result_layout = QVBoxLayout()
        
        # 结果显示和复制按钮水平布局
        result_copy_layout = QHBoxLayout()
        
        self.result_label = QLabel('(minL,maxL,minA,maxA,minB,maxB)')
        self.result_label.setAlignment(Qt.AlignCenter)
        result_copy_layout.addWidget(self.result_label)
        
        self.copy_btn = QPushButton('复制结果')
        self.copy_btn.clicked.connect(self.copy_result)
        self.copy_btn.setEnabled(False)
        result_copy_layout.addWidget(self.copy_btn)
        
        result_layout.addLayout(result_copy_layout)
        
        # 计算按钮
        self.calculate_btn = QPushButton('计算阈值')
        self.calculate_btn.clicked.connect(self.calculate_thresholds)
        self.calculate_btn.setEnabled(False)
        result_layout.addWidget(self.calculate_btn)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # 设置主窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择图片', '', 'Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)')
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                # 尝试添加扩展名
                if not file_path.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                        if os.path.exists(file_path + ext):
                            file_path += ext
                            break
            
            # 使用QImage直接加载图像
            qimg = QImage(file_path)
            if qimg.isNull():
                raise Exception(f"QImage无法加载图像: {file_path}")
                
            # 转换为OpenCV格式
            pixmap = QPixmap.fromImage(qimg)
            img_bytes = qimg.bits()
            img_bytes.setsize(qimg.byteCount())
            img_np = np.frombuffer(img_bytes, dtype=np.uint8).reshape(qimg.height(), qimg.width(), 4)
            img = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
            
            # 调整图像大小为固定尺寸
            self.img = cv2.resize(img, (self.fixed_width, self.fixed_height))
                
            # 保存原始图像用于重置
            self.original_img = self.img.copy()
            
            # 转换为Qt图像并显示
            self.display_image(self.img)
            self.calculate_btn.setEnabled(True)
            self.crop_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, '错误', f'无法读取图像: {file_path}\n错误信息: {str(e)}')
    
    def display_image(self, img):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = rgb_img.shape
        q_img = QImage(rgb_img.data, w, h, w * c, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # 设置图像标签大小与图像大小一致
        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.width(), pixmap.height())
        
        # 保存当前显示图像的尺寸，用于裁剪计算
        self.display_width = w
        self.display_height = h
    
    def toggle_camera(self):
        if self.timer.isActive():
            # 停止相机
            self.timer.stop()
            if self.camera is not None:
                self.camera.release()
                self.camera = None
            self.camera_btn.setText('打开相机')
            self.capture_btn.setEnabled(False)
            # 相机关闭后，如果有图像，则启用裁剪和计算按钮
            if self.img is not None:
                self.crop_btn.setEnabled(True)
                self.calculate_btn.setEnabled(True)
                self.reset_btn.setEnabled(True)
        else:
            # 启动相机
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, '错误', '无法打开相机')
                return
                
            # 设置相机分辨率为固定尺寸
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.fixed_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.fixed_height)
            
            self.timer.start(30)  # 30ms刷新一次，约33fps
            self.camera_btn.setText('关闭相机')
            self.capture_btn.setEnabled(True)
            # 相机打开时，禁用裁剪和计算按钮
            self.crop_btn.setEnabled(False)
            self.calculate_btn.setEnabled(False)
            self.reset_btn.setEnabled(False)
            # 如果正在裁剪，取消裁剪模式
            if self.cropping:
                self.cropping = False
                self.crop_btn.setText('剪裁')
                self.setCursor(QCursor(Qt.ArrowCursor))
                self.rubber_band.hide()
    
    def update_frame(self):
        ret, frame = self.camera.read()
        if ret:
            # 确保帧大小一致
            frame = cv2.resize(frame, (self.fixed_width, self.fixed_height))
            
            # 转换为Qt图像并显示
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, c = rgb_frame.shape
            q_img = QImage(rgb_frame.data, w, h, w * c, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap)
            self.image_label.setFixedSize(pixmap.width(), pixmap.height())
            
            self.img = frame  # 保存当前帧
            
            # 更新显示尺寸
            self.display_width = w
            self.display_height = h
    
    def capture_image(self):
        if self.img is not None:
            self.timer.stop()
            self.camera_btn.setText('打开相机')
            if self.camera is not None:
                self.camera.release()
                self.camera = None
            self.capture_btn.setEnabled(False)
            self.calculate_btn.setEnabled(True)
            self.crop_btn.setEnabled(True)
            self.reset_btn.setEnabled(True)
            # 保存原始图像用于重置
            self.original_img = self.img.copy()
            
            # 自动开启裁剪模式
            self.toggle_crop_mode()
    
    def toggle_crop_mode(self):
        # 只有在相机关闭时才能使用裁剪功能
        if self.img is not None and not self.timer.isActive():
            if not self.cropping:
                self.statusBar().showMessage('请在图像上拖动鼠标选择要剪裁的区域')
                self.cropping = True
                self.crop_btn.setText('取消剪裁')
                self.setCursor(QCursor(Qt.CrossCursor))
            else:
                self.statusBar().showMessage('')
                self.cropping = False
                self.crop_btn.setText('剪裁')
                self.setCursor(QCursor(Qt.ArrowCursor))
                self.rubber_band.hide()
        elif self.timer.isActive():
            QMessageBox.warning(self, '提示', '请先关闭相机或截图后再进行裁剪')
    
    def start_crop(self, event):
        if self.cropping:
            self.crop_origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.crop_origin, QSize()))
            self.rubber_band.show()
    
    def update_crop(self, event):
        if self.cropping and not self.crop_origin.isNull():
            self.rubber_band.setGeometry(QRect(self.crop_origin, event.pos()).normalized())
    
    def end_crop(self, event):
        if self.cropping and not self.crop_origin.isNull():
            crop_rect = self.rubber_band.geometry()
            
            # 直接使用裁剪矩形的坐标，因为图像标签大小与图像大小一致
            x = crop_rect.x()
            y = crop_rect.y()
            w = crop_rect.width()
            h = crop_rect.height()
            
            # 确保剪裁区域在图像范围内
            x = max(0, min(x, self.display_width - 1))
            y = max(0, min(y, self.display_height - 1))
            w = min(w, self.display_width - x)
            h = min(h, self.display_height - y)
            
            # 检查剪裁区域是否有效
            if w > 0 and h > 0:
                # 在OpenCV中剪裁图像
                self.img = self.img[y:y+h, x:x+w]
                
                # 将裁剪后的图像调整回固定大小
                self.img = cv2.resize(self.img, (self.fixed_width, self.fixed_height))
                
                self.display_image(self.img)
            
            self.rubber_band.hide()
            self.cropping = False
            self.crop_btn.setText('剪裁')
            self.setCursor(QCursor(Qt.ArrowCursor))
            self.statusBar().showMessage('')
    
    def reset_image(self):
        if hasattr(self, 'original_img'):
            self.img = self.original_img.copy()
            self.display_image(self.img)
    
    def update_l_value(self):
        self.l_value.setText(str(self.l_slider.value()))
    
    def set_l_slider(self):
        try:
            value = int(self.l_value.text())
            self.l_slider.setValue(value)
        except ValueError:
            pass
    
    def update_c_value(self):
        self.c_value.setText(str(self.c_slider.value()))
    
    def set_c_slider(self):
        try:
            value = int(self.c_value.text())
            self.c_slider.setValue(value)
        except ValueError:
            pass
    
    def calculate_thresholds(self):
        # 只有在相机关闭时才能计算阈值
        if self.timer.isActive():
            QMessageBox.warning(self, '提示', '请先关闭相机或截图后再计算阈值')
            return
            
        if self.img is None:
            QMessageBox.warning(self, '错误', '请先选择或拍摄图像')
            return
            
        l_tol = float(self.l_value.text())
        c_tol = float(self.c_value.text())
        
        try:
            thresholds = self.get_lab_thresholds(self.img, l_tol, c_tol)
            self.threshold_result = f"({thresholds[0]},{thresholds[1]},{thresholds[2]},{thresholds[3]},{thresholds[4]},{thresholds[5]})"
            self.result_label.setText(self.threshold_result)
            self.copy_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, '错误', f'计算阈值时出错: {str(e)}')
    
    def copy_result(self):
        if self.threshold_result:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.threshold_result)
            self.statusBar().showMessage('结果已复制到剪贴板', 2000)
    
    def get_lab_thresholds(self, img, l_tol=0, c_tol=0):
        """
        分析图像并返回LAB颜色空间阈值，可配置亮度和颜色容差。
        """
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
    app = QApplication(sys.argv)
    window = LABThresholdApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()