from lzhasynctcpclient import AsyncTcpClient
import asyncio
import json
import logging
from typing import Optional, Callable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class GripperWithForceSensor:
    """
    ```python
    # Expample:

    form lzh_gripper_with_force_sensor import GripperWithForceSensor

    GRIPPER_IP = '192.168.0.123'
    gripper = GripperWithForce_sensor(host=GRIPPER_IP)

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
    """
    def __init__(
        self,
        host: str = "127.0.0.1",
        force_callback: Optional[Callable[[float], None]] = None,
        callback_threshold: float = 0.1,
        single_callback_mode: bool = False,
        name: str = 'Gripper'
    ):
        """
        构造抓手实例

        - `host` : 抓手 IP
        - `force_callback` : 注册力值变化回调函数`(Callable[[float], None])` 接收一个`float`形参(力值)，也可以不注册回调函数，只用`force()`轮询
        - `callback_threshold` : 力绝对值或力的变化绝对值超过此值触发回调，单位 kg
        - `single_callback_mode` : 此值为真(单阈值模式): `callback_threshold`为力的绝对值阈值，为假(差值模式): `callback_threshold`为力的变化绝对值阈值。达到阈值触发回调
        - `name` : 日志抬头
        """
        self._host:str = host
        self._force_callback  = force_callback
        self._callback_threshold = callback_threshold
        self._single_callback_mode = single_callback_mode
        self._name:str = name
        self._status:dict = {}
        self._status["mode"] = 1
        self._status["action"] = "release"
        self._status["force"] = 0.0
        self._last_force:float = 0.0
        self._atc = AsyncTcpClient(host=self._host, port=11516, on_message=self._on_atc_message, on_connect=self._on_connect,heartbeat_require_response=True)
        self._atc.start()
        
    def _on_connect(self):
        logging.info(f"[{self._name}] Connected to {self._host}")
        self._atc.send(json.dumps(self._status))
    
    def prepare(self):
        """
        开始抓取步骤 1 : 准备

        > 共 3 个步骤命令 :
        >    1. 准备 `prepare()` 
        >    2. 抓取 `grip() `
        >    3. 释放 `release()`
        """
        self._atc.send('{"action": "prepare"}')

    def grip(self):
        """
        开始抓取步骤 2 : 抓取

        > 共 3 个步骤命令 :
        >    1. 准备 `prepare()` 
        >    2. 抓取 `grip()` 
        >    3. 释放 `release()`
        """
        self._atc.send('{"action": "grip"}')
    
    def release(self):
        """
        开始抓取步骤 3 : 释放

        > 共 3 个步骤命令 :
        >    1. 准备 `prepare()` 
        >    2. 抓取 `grip()` 
        >    3. 释放 `release()`
        """
        self._atc.send('{"action": "release"}')
    
    def set_mode (self, mode: int):
        """
        设置抓手的抓取模式。如果切换到了不同模式，抓手会自动设置当前抓取步骤为步骤 1 `prepare`

        - `mode (int)`: 模式编号,范围 1~4

        Raises:
            `ValueError`: 如果 mode 不在 1~4 范围内
        """
        if not isinstance(mode, int) or not (1 <= mode <= 4):
            raise ValueError("mode 参数必须是 1~4 之间的整数")
        self._atc.send(f'{{"mode": {mode}}}')
    
    def force(self):
        """
        返回力传感器的值 (单位 kg)
        """
        return self._status["force"]
    
    def force_sensor_zeroing(self):
        """
        力传感器调零
        """
        self._atc.send('{"force_sensor_zeroing": ""}')

    def status(self):
        """
        返回包含抓手当前的模式、抓取步骤和力传感器的值 (单位 kg) 的字典

        内容示例: `{'mode': 1, 'action': 'prepare', 'force': 1.23}`
        """
        return self._status

    def set_force_callback(
            self, 
            callback: Optional[Callable[[float], None]] = None,
            callback_threshold:float = 0.1, 
            single_callback_mode: bool = False):
        """
        注册并设置力值的回调函数，也可以不注册回调函数，只用 force() 轮询

        - `callback` : 注册力值变化回调函数`(Callable[[float], None])`, 接收一个`float`形参(力值)
        - `callback_threshold` : 力绝对值或力的变化绝对值超过此值触发回调，单位 kg
        - `single_callback_mode` : 此值为真则: `callback_threshold`为力的绝对值阈值，为假: `callback_threshold`为力的变化绝对值阈值。达到阈值触发回调
        """
        self._force_callback  = callback
        self._callback_threshold = callback_threshold
        self._single_callback_mode = single_callback_mode
    
    def _on_atc_message(self, msg: str):
        try:
            res = json.loads(msg)
            if "force_sensor_zeroing" in res:
                res.pop("force_sensor_zeroing")
            self._status.update(res)

            if "force" in res and self._force_callback:
                force_val:float = res["force"]
                if self._single_callback_mode:
                    if abs(force_val) >= self._callback_threshold and self._last_force < self._callback_threshold:
                        self._force_callback(force_val)
                    self._last_force = force_val
                else:
                    if abs(self._last_force - force_val) >= self._callback_threshold:
                        self._last_force = force_val
                        self._force_callback(force_val)
                

        except Exception as e:
            logging.error(f'[{self._name}] 抓手响应解析失败 : error: {e} | msg : {msg}')

    def stop(self):
        """
        关闭抓手连接
        """
        self._atc.stop()
        logging.info(f"[{self._name}] Stopped connection")

if __name__ == "__main__":
    """
    测试示例
    """
    CLIENT_IP = "192.168.0.102"

    def callback(kg:float):
        print(f'new force value print form callback : {kg} kg')

    gripper = GripperWithForceSensor(host=CLIENT_IP)
    gripper.set_force_callback(callback, 18, True)
    gripper.set_force_callback(
        callback = callback,
        callback_threshold = 0.1,
        single_callback_mode = False
    )
    gripper.set_force_callback(
        callback = callback,
        callback_threshold = 3.0,
        single_callback_mode = True
    )
    

    import random
    async def test_gripper(s1,s2):
        while True:
            gripper.set_mode (random.randint(1, 4)) # 随机设置模式 1 到 4
            await asyncio.sleep(s1)
            gripper.grip() # 开始抓取
            await asyncio.sleep(s2)
            gripper.grip() # 开始抓取
            await asyncio.sleep(s2)
            gripper.release() # 开始释放
            await asyncio.sleep(s2)

    async def test_force_status(s):
        while True:
            await asyncio.sleep(s)
            print(f'force value : {gripper.force()} kg')
            await asyncio.sleep(s)
            print(f'gripper status : {gripper.status()}')

    async def test_force_sensor_zeroing(s):
        while True:
            await asyncio.sleep(s)
            gripper.force_sensor_zeroing()
            print(f'force value : {gripper.force()} kg')
            await asyncio.sleep(s)
            print(f'gripper status : {gripper.status()}')
    
    
    async def main():
        await asyncio.gather(
            test_gripper(0.5, 2),
            test_force_status(0.2),
            test_force_sensor_zeroing(2)
        )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        gripper.stop()
        print("程序终止")
