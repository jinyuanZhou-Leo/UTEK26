import argparse
import logging

import uvicorn

from sentinel import config
from sentinel.api import server
from sentinel.core.loop import Engine
from sentinel.core.placeholders import NoInterventions, OfflineSensor, PlaceholderModel
from sentinel.models import KeyboardFeatures, VisionFeatures
from sentinel.sensors.context.mock import MockContextSensor
from sentinel.sensors.mouse.mock import MockMouseSensor
from sentinel.sensors.vision.sensor import VisionSensor

# >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: Chris | purpose: CLI entry point wiring sensors, engine and server
def main() -> None:
    parser = argparse.ArgumentParser(description="UTEKinetics fatigue sentinel")
    parser.add_argument("--mock", action="store_true", help="use fake sensor data")
    parser.add_argument("--no-camera", action="store_true", help="disable the webcam")
    parser.add_argument("--headless", action="store_true", help="run without the desktop app")
    parser.add_argument("--port", type=int, default=config.PORT)
    args = parser.parse_args()          # e.g. args.mock is True if --mock was given

    logging.basicConfig(level=logging.INFO)

    keyboard = OfflineSensor("keyboard", KeyboardFeatures(False, 5.0, 0, 0, 0, 0, 0, 0, 0))
    mouse = MockMouseSensor()           # real MouseSensor comes in step 4
    context = MockContextSensor()       # real ContextSensor comes in step 5
    if args.mock or args.no_camera:
        vision = OfflineSensor("vision", VisionFeatures(False, False, 0, 0, 0, 0, 0, None, 1.0))
    else:
        vision = VisionSensor()
    sensors = [keyboard, mouse, context, vision]
    for s in sensors:
        s.start()
    server.engine = Engine(keyboard, mouse, context, vision, PlaceholderModel(), NoInterventions())
    uvicorn.run(server.app, host=config.HOST, port=args.port)


if __name__ == "__main__":
    main()