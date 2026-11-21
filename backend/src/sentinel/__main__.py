import argparse
import logging

import uvicorn

from sentinel import config
from sentinel.api import server
from sentinel.core.loop import Engine
from sentinel.core.placeholders import NoInterventions, OfflineSensor
from sentinel.models import KeyboardFeatures, VisionFeatures
from sentinel.scoring.rules import Rules
from sentinel.sensors.vision.sensor import VisionSensor
# from sentinel.sensors.mouse.sensor import MouseSensor
from sentinel.sensors.mouse.mock import MockMouseSensor
from sentinel.sensors.context.mock import MockContextSensor

# >>> AI-GENERATED (Claude, 2026-11-21) | reviewed by: Chris | purpose: CLI entry point wiring sensors, engine and server
def main() -> None:
    parser = argparse.ArgumentParser(description="UTEKinetics fatigue sentinel")
    parser.add_argument("--mock", action="store_true", help="use fake sensor data")
    parser.add_argument("--no-camera", action="store_true", help="disable the webcam")
    parser.add_argument("--headless", action="store_true", help="run without the desktop app")
    parser.add_argument("--port", type=int, default=config.PORT)
    args = parser.parse_args()          # e.g. args.mock is True if --mock was given

    logging.basicConfig(level=logging.INFO)

    try:
        from sentinel.sensors.keyboard.sensor import KeyboardSensor  # needs the `input` extra (pynput)
        keyboard = KeyboardSensor()
    except ImportError:
        logging.warning("pynput not installed; keyboard sensor disabled")
        keyboard = OfflineSensor("keyboard", KeyboardFeatures(False, 5.0, 0, 0, 0, 0, 0, 0, 0))
    try:
        from sentinel.sensors.mouse.sensor import MouseSensor  # needs the `input` extra (pynput)
        mouse = MouseSensor()
    except ImportError:
        logging.warning("pynput not installed; using mock mouse data")
        mouse = MockMouseSensor()
    context = MockContextSensor()       # real ContextSensor comes in step 5
    if args.mock or args.no_camera:
        vision = OfflineSensor("vision", VisionFeatures(False, False, 0, 0, 0, 0, 0, None, 1.0))
    else:
        vision = VisionSensor()
    sensors = [keyboard, mouse, context, vision]
    for s in sensors:
        s.start()
    server.engine = Engine(keyboard, mouse, context, vision, Rules(), NoInterventions())
    uvicorn.run(server.app, host=config.HOST, port=args.port)


if __name__ == "__main__":
    main()