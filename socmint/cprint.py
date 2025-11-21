from datetime import datetime

def block(text, r, g, b):
    return f"\033[48;2;{r};{g};{b}m\033[97m {text} \033[0m"

def info(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = block("INFO", 100, 100, 100)
    print(f"{timestamp} {label} {text}")

def success(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = block("SUCCESS", 0, 180, 0)
    print(f"{timestamp} {label} {text}")

def error(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = block("ERROR", 180, 0, 0)
    print(f"{timestamp} {label} {text}")
