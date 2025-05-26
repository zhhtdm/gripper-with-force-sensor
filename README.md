
# 控制抓手 (带力传感器) 的 TCP 客户端
基于独立线程+异步 TCP 客户端，支持回调功能

## 示例
```python
# Expample:

from lzhgripperwithforcesensor import GripperWithForceSensor

GRIPPER_IP = '192.168.0.123'
gripper = GripperWithForceSensor(host=GRIPPER_IP)

gripper.set_mode(1)             # 设置抓取模式 (1~4)
gripper.prepare()               # 准备抓取
gripper.grip()                  # 抓取
gripper.release()               # 释放
gripper.force()                 # 查询力值 (kg)
gripper.force_sensor_zeroing()  # 力传感器调零
gripper.status()                # 抓手当前状态汇总
    
# 回调函数相关 (非必须)
def callback(kg: float):        # 定义一个回调函数
    print(f'New force value print from callback : {kg} kg')

gripper.set_force_callback(     # 设置差值模式回调
    callback = callback,
    callback_threshold = 0.1,
    single_callback_mode = False
)
gripper.set_force_callback(     # 设置单阈值模式回调
    callback = callback,
    callback_threshold = 3.0,
    single_callback_mode = True
)
```
## 安装 - [PyPI](https://pypi.org/project/lzhgripperwithforcesensor/)
```shell
pip install lzhgripperwithforcesensor
```

## API
[Document](https://zhhtdm.github.io/gripper-with-force-sensor/)
