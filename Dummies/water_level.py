import random
import time

time.sleep(2)
i = random.randint(0, 100)

if(i<=20):
    state = "ADD (0%-20%)"
elif(i>=90):
    state = "FULL (90%-100%)"
else:
    state = "NORMAL (21%-8%9)"

print(f"Water Level: {i}% | State: {state}")

# ADD (0%-20%) | NORMAL (21%-89%) | FULL (90%-100%))