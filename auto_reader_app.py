from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
import random
import time
from datetime import datetime
import threading
import os

# 尝试导入Android特定模块
try:
    from jnius import autoclass
    # 获取Android相关类
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Instrumentation = autoclass('android.app.Instrumentation')
    SystemClock = autoclass('android.os.SystemClock')
    MotionEvent = autoclass('android.view.MotionEvent')
    
    # 初始化Instrumentation用于模拟触摸事件
    instrumentation = Instrumentation()
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

class AutoReaderApp(App):
    def build(self):
        self.title = '自动阅读工具'
        self.running = False
        self.page_count = 0
        self.start_time = None
        self.reader_thread = None
        
        # 主布局
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 标题
        title_label = Label(text='安卓自动阅读工具', font_size=22, size_hint=(1, 0.1))
        layout.add_widget(title_label)
        
        # 模式选择
        mode_layout = BoxLayout(size_hint=(1, 0.1))
        mode_label = Label(text='翻页模式:', size_hint=(0.4, 1))
        self.mode_spinner = Spinner(
            text='滑动模式',
            values=('滑动模式', '点击模式', '智能模式'),
            size_hint=(0.6, 1)
        )
        mode_layout.add_widget(mode_label)
        mode_layout.add_widget(self.mode_spinner)
        layout.add_widget(mode_layout)
        
        # 翻页间隔
        interval_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        interval_label = Label(text='翻页间隔(秒): 3.0 - 5.0', size_hint=(1, 0.5))
        self.min_interval = 3.0
        self.max_interval = 5.0
        
        slider_layout = BoxLayout(size_hint=(1, 0.5))
        self.min_slider = Slider(min=0.5, max=10, value=3.0, step=0.1, size_hint=(0.45, 1))
        slider_sep = Label(text='-', size_hint=(0.1, 1))
        self.max_slider = Slider(min=0.5, max=10, value=5.0, step=0.1, size_hint=(0.45, 1))
        
        slider_layout.add_widget(self.min_slider)
        slider_layout.add_widget(slider_sep)
        slider_layout.add_widget(self.max_slider)
        
        self.min_slider.bind(value=self.on_slider_change)
        self.max_slider.bind(value=self.on_slider_change)
        
        interval_layout.add_widget(interval_label)
        interval_layout.add_widget(slider_layout)
        layout.add_widget(interval_layout)
        
        # 反检测级别
        detection_layout = BoxLayout(size_hint=(1, 0.1))
        detection_label = Label(text='反检测级别:', size_hint=(0.4, 1))
        self.detection_spinner = Spinner(
            text='中等',
            values=('低', '中等', '高'),
            size_hint=(0.6, 1)
        )
        detection_layout.add_widget(detection_label)
        detection_layout.add_widget(self.detection_spinner)
        layout.add_widget(detection_layout)
        
        # 翻页次数
        pages_layout = BoxLayout(size_hint=(1, 0.1))
        pages_label = Label(text='翻页次数:', size_hint=(0.4, 1))
        self.pages_input = TextInput(
            text='', 
            hint_text='无限制',
            input_filter='int',
            multiline=False,
            size_hint=(0.6, 1)
        )
        pages_layout.add_widget(pages_label)
        pages_layout.add_widget(self.pages_input)
        layout.add_widget(pages_layout)
        
        # 状态信息
        self.status_label = Label(
            text='准备就绪',
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.status_label)
        
        # 控制按钮
        button_layout = BoxLayout(size_hint=(1, 0.1))
        self.start_button = Button(
            text='开始阅读',
            background_color=(0, 0.7, 0, 1)
        )
        self.start_button.bind(on_press=self.toggle_reading)
        button_layout.add_widget(self.start_button)
        layout.add_widget(button_layout)
        
        # 更新状态显示的计时器
        Clock.schedule_interval(self.update_status, 1)
        
        return layout
    
    def on_slider_change(self, instance, value):
        # 确保最小值不大于最大值
        if instance == self.min_slider:
            self.min_interval = value
            if value > self.max_slider.value:
                self.max_slider.value = value
        else:
            self.max_interval = value
            if value < self.min_slider.value:
                self.min_slider.value = value
                
        # 更新显示的文本
        min_val = self.min_slider.value
        max_val = self.max_slider.value
        self.min_interval = min_val
        self.max_interval = max_val
        
        # 查找interval_label并更新文本
        for child in self.root.children:
            if isinstance(child, BoxLayout) and len(child.children) > 0:
                if isinstance(child.children[0], Label) and '翻页间隔' in child.children[0].text:
                    child.children[0].text = f'翻页间隔(秒): {min_val:.1f} - {max_val:.1f}'
                    break
    
    def get_screen_size(self):
        """获取屏幕尺寸"""
        if IS_ANDROID:
            activity = PythonActivity.mActivity
            display = activity.getWindowManager().getDefaultDisplay()
            size = autoclass('android.graphics.Point')()
            display.getSize(size)
            return size.x, size.y
        else:
            # 模拟屏幕尺寸用于测试
            return 1080, 2340
    
    def perform_swipe(self, start_x, start_y, end_x, end_y, duration):
        """执行滑动操作"""
        if IS_ANDROID:
            try:
                # 使用Instrumentation执行滑动
                downTime = SystemClock.uptimeMillis()
                eventTime = downTime
                
                # 按下
                event = MotionEvent.obtain(
                    downTime, eventTime, MotionEvent.ACTION_DOWN, 
                    start_x, start_y, 0
                )
                instrumentation.sendPointerSync(event)
                event.recycle()
                
                # 移动的步数
                steps = int(duration / 50)  # 每50ms一步
                
                for i in range(steps):
                    # 计算当前位置
                    t = i / steps
                    x = start_x + (end_x - start_x) * t
                    y = start_y + (end_y - start_y) * t
                    
                    # 更新时间
                    eventTime = SystemClock.uptimeMillis()
                    
                    # 移动
                    event = MotionEvent.obtain(
                        downTime, eventTime, MotionEvent.ACTION_MOVE, 
                        x, y, 0
                    )
                    instrumentation.sendPointerSync(event)
                    event.recycle()
                    
                    # 短暂暂停
                    time.sleep(0.01)
                
                # 抬起
                eventTime = SystemClock.uptimeMillis()
                event = MotionEvent.obtain(
                    downTime, eventTime, MotionEvent.ACTION_UP, 
                    end_x, end_y, 0
                )
                instrumentation.sendPointerSync(event)
                event.recycle()
                
                return True
            except Exception as e:
                print(f"滑动操作错误: {e}")
                return False
        else:
            # 非安卓环境下模拟成功
            print(f"模拟滑动: {start_x},{start_y} -> {end_x},{end_y}")
            return True
    
    def perform_tap(self, x, y):
        """执行点击操作"""
        if IS_ANDROID:
            try:
                # 使用Instrumentation执行点击
                downTime = SystemClock.uptimeMillis()
                eventTime = downTime
                
                # 按下
                event = MotionEvent.obtain(
                    downTime, eventTime, MotionEvent.ACTION_DOWN, 
                    x, y, 0
                )
                instrumentation.sendPointerSync(event)
                event.recycle()
                
                # 短暂暂停
                time.sleep(0.1)
                
                # 抬起
                eventTime = SystemClock.uptimeMillis()
                event = MotionEvent.obtain(
                    downTime, eventTime, MotionEvent.ACTION_UP, 
                    x, y, 0
                )
                instrumentation.sendPointerSync(event)
                event.recycle()
                
                return True
            except Exception as e:
                print(f"点击操作错误: {e}")
                return False
        else:
            # 非安卓环境下模拟成功
            print(f"模拟点击: {x},{y}")
            return True
    
    def next_page(self):
        """执行下一页操作"""
        width, height = self.get_screen_size()
        mode = self.mode_spinner.text
        detection_level = self.detection_spinner.text
        
        # 根据模式和反检测级别选择操作
        if mode == '滑动模式' or (mode == '智能模式' and self.page_count % 10 < 7):
            # 使用滑动模式
            
            # 随机起始点，在屏幕下半部分
            start_x = random.randint(width // 4, width * 3 // 4)
            start_y = random.randint(int(height * 0.6), int(height * 0.8))
            
            # 随机终点
            end_x = start_x + random.randint(-width // 10, width // 10)
            swipe_distance = random.randint(int(height * 0.3), int(height * 0.5))
            end_y = max(start_y - swipe_distance, height // 10)
            
            # 随机滑动时间
            duration = random.randint(200, 400)
            
            # 执行滑动
            return self.perform_swipe(start_x, start_y, end_x, end_y, duration)
            
        else:
            # 使用点击模式
            
            # 大多数阅读APP在屏幕右侧点击翻页
            side = random.choice(["right"] * 8 + ["left"] * 2)  # 80%几率点击右侧
            
            if side == "right":
                x = random.randint(int(width * 0.7), int(width * 0.95))
            else:
                x = random.randint(int(width * 0.05), int(width * 0.3))
            
            # 垂直位置随机，但避开顶部和底部的导航/菜单区域
            y = random.randint(int(height * 0.3), int(height * 0.7))
            
            # 执行点击
            return self.perform_tap(x, y)
    
    def start_reading(self):
        """开始自动阅读线程"""
        # 解析参数
        mode = self.mode_spinner.text
        detection_level = self.detection_spinner.text
        
        try:
            pages_text = self.pages_input.text.strip()
            total_pages = int(pages_text) if pages_text else None
        except ValueError:
            total_pages = None
        
        self.running = True
        self.page_count = 0
        self.start_time = datetime.now()
        
        while self.running:
            if total_pages and self.page_count >= total_pages:
                break
            
            # 执行翻页
            if self.next_page():
                self.page_count += 1
                
                # 根据反检测级别调整翻页间隔
                if detection_level == '低':
                    wait_time = random.uniform(self.min_interval * 0.8, self.max_interval * 1.2)
                elif detection_level == '中等':
                    # 使用稍微复杂的随机分布
                    if random.random() < 0.8:  # 80%的页面
                        wait_time = random.normalvariate(
                            (self.min_interval + self.max_interval) / 2, 
                            (self.max_interval - self.min_interval) / 4
                        )
                    else:  # 20%的页面
                        wait_time = random.normalvariate(
                            self.max_interval * 1.2, 
                            (self.max_interval - self.min_interval) / 3
                        )
                else:  # 高级别
                    # 使用更复杂的人类行为模拟
                    if random.random() < 0.7:  # 70%正常翻页
                        wait_time = random.normalvariate(
                            (self.min_interval + self.max_interval) / 2, 
                            (self.max_interval - self.min_interval) / 3
                        )
                    elif random.random() < 0.9:  # 20%仔细阅读
                        wait_time = random.normalvariate(
                            self.max_interval * 1.5, 
                            self.max_interval / 2
                        )
                    else:  # 10%快速翻页
                        wait_time = random.normalvariate(
                            self.min_interval * 0.7, 
                            self.min_interval / 4
                        )
                
                # 确保等待时间在合理范围内
                wait_time = max(self.min_interval * 0.5, min(self.max_interval * 2.5, wait_time))
                
                # 等待
                time.sleep(wait_time)
            else:
                # 翻页失败，短暂等待后重试
                time.sleep(2)
    
    def toggle_reading(self, instance):
        """切换开始/停止自动阅读"""
        if self.running:
            # 停止阅读
            self.running = False
            self.start_button.text = '开始阅读'
            self.start_button.background_color = (0, 0.7, 0, 1)
            if self.reader_thread and self.reader_thread.is_alive():
                self.reader_thread.join(1)  # 等待线程结束，最多1秒
        else:
            # 开始阅读
            self.start_button.text = '停止阅读'
            self.start_button.background_color = (0.8, 0, 0, 1)
            self.reader_thread = threading.Thread(target=self.start_reading)
            self.reader_thread.daemon = True
            self.reader_thread.start()
    
    def format_time(self, seconds):
        """将秒数格式化为时分秒"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def update_status(self, dt):
        """更新状态显示"""
        if self.running and self.start_time:
            current_time = datetime.now()
            runtime_seconds = (current_time - self.start_time).total_seconds()
            runtime_formatted = self.format_time(runtime_seconds)
            
            # 计算速度
            if runtime_seconds > 0:
                pages_per_hour = (self.page_count / runtime_seconds) * 3600
                speed = f"{pages_per_hour:.1f} 页/小时"
            else:
                speed = "计算中..."
            
            status_text = f"运行中: 已翻页 {self.page_count} 次\n运行时间: {runtime_formatted}\n速度: {speed}"
            self.status_label.text = status_text
        elif not self.running and self.start_time and self.page_count > 0:
            # 显示上次运行的统计信息
            end_time = datetime.now()
            runtime_seconds = (end_time - self.start_time).total_seconds()
            runtime_formatted = self.format_time(runtime_seconds)
            
            if runtime_seconds > 0:
                pages_per_hour = (self.page_count / runtime_seconds) * 3600
                speed = f"{pages_per_hour:.1f} 页/小时"
            else:
                speed = "N/A"
            
            status_text = f"已停止: 共翻页 {self.page_count} 次\n运行时间: {runtime_formatted}\n平均速度: {speed}"
            self.status_label.text = status_text

if __name__ == '__main__':
    AutoReaderApp().run()