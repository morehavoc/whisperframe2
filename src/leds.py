import settings

class DummyLEDs:
    """Dummy implementation when LEDs are disabled"""
    def percent(self, p=0.5):
        pass
        
    def error(self):
        pass

class RealLEDs:
    """Real LED implementation using hardware"""
    def __init__(self):
        from gpiozero import LED
        import adafruit_dotstar as dotstar
        import board
        import time
        
        self.power = LED(5)
        self.dots = dotstar.DotStar(board.SCK, board.MOSI, 12, brightness=0.2)
        self.power.on()
        
        # Initialize LEDs
        self.dots[0] = [255,0,0]
        self.dots[1] = [255,0,0]
        for i in range(5):
            self.dots.fill((255,0,0))
            time.sleep(.1)
        for i in range(5):
            self.dots.fill((0,0,0))
            time.sleep(.1)
            
    def percent(self, p=0.5):
        self.dots.fill((0,0,0))
        time.sleep(.1)
        cnt = 0
        if p < 0:
            cnt = 0
        elif p > 1:
            cnt = 12
        else:
            cnt = int(round(12*p))
        for i in range(0, cnt):
            self.dots[i] = [255,0,0]
            time.sleep(0.5)
            
    def error(self):
        self.dots.fill((0,0,255))
        time.sleep(1)

# Create the appropriate LED implementation based on settings
leds = RealLEDs() if settings.ENABLE_LEDS else DummyLEDs()

# Export the functions at module level for backwards compatibility
def percent(p=0.5):
    leds.percent(p)
    
def error():
    leds.error()

if __name__ == '__main__':
    print("ready")
    time.sleep(2)
    for i in range(10):
        print(i)
        percent(i*10/100.0)
        time.sleep(2)
    error()
