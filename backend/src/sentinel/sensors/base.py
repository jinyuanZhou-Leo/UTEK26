from typing import Protocol, Any

class Sensor(Protocol):
    name: str                    # "keyboard" | "mouse" | "context" | "vision"

    def start(self) -> None:
        """开始采集。在后台线程里运行，这个函数本身必须马上返回。"""

    def stop(self) -> None:
        """停止采集，释放资源（监听器、摄像头）。重复调用不能报错。"""

    def snapshot(self) -> Any:
        """返回从上一次调用到现在这段时间的数据，然后把"本窗口"计数清零。
        要求：
        - 5 毫秒内返回（不要在这里做慢操作）
        - 不抛异常（出错就返回 available=False 的数据）
        - 线程安全（用 threading.Lock 保护共享变量）"""