import time
from .sensor import KeyboardSensor

def main():
    sensor = KeyboardSensor()
    sensor.start()
    try:
        while True:
            time.sleep(5)# wait for 5 seconds before taking the next snapshot
            print(sensor.snapshot())
    except KeyboardInterrupt:# handle Ctrl+C gracefully
        print("Stopping keyboard sensor...")

    finally:#release the keyboard listener before exiting
        sensor.stop()
        print("Keyboard sensor stopped.")
if __name__ == "__main__":
    main()