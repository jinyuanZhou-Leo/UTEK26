import time
from sentinel.models import ContextFeatures

class MockContextSensor:
    name = "context"

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self) -> ContextFeatures:
        categories = ["code", "browser", "meeting"]
        apps = ["Code", "Google Chrome", "zoom.us"]
        i = int(time.time() // 60) % 3
        cat = categories[i]
        return ContextFeatures(
            available=True,
            active_app=apps[i],
            app_category=cat,
            in_meeting=(cat == "meeting"),
        )