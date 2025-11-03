import subprocess
import threading
import time

INPUT_UDP = "udp://0.0.0.0:5001"

class StreamManager:
    def __init__(self, input_url):
        self.input_url = input_url
        self.outputs = {}
        self.process = None
        self.running = False
        self.needs_restart = False
    
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._stream_loop, daemon=True)
        thread.start()
    
    def _stream_loop(self):
        while self.running:
            if not self.outputs:
                time.sleep(1)
                continue
            
            # Build command
            cmd = ['ffmpeg', '-i', self.input_url]
            for url in self.outputs.values():
                cmd.extend(['-c', 'copy', '-f', 'mpegts', url])
            
            print(f"\n[INFO] Starting ffmpeg with {len(self.outputs)} output(s)")
            
            self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.needs_restart = False
            
            # Wait for ffmpeg to die or restart signal
            while self.process.poll() is None and not self.needs_restart:
                time.sleep(0.5)
            
            if self.needs_restart:
                self.process.terminate()
                self.process.wait()
                print("[INFO] Restarting ffmpeg...")
            else:
                print("[INFO] FFmpeg died, restarting in 5s...")
                time.sleep(5)
    
    def add(self, name, url):
        self.outputs[name] = url
        print(f"Added: {name} -> {url}")
        self.needs_restart = True
    
    def remove(self, name):
        if name in self.outputs:
            del self.outputs[name]
            print(f"Removed: {name}")
            self.needs_restart = True
        else:
            print(f"Not found: {name}")
    
    def list(self):
        if self.outputs:
            for name, url in self.outputs.items():
                print(f"  {name}: {url}")
        else:
            print("  No outputs")
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

# Main
manager = StreamManager(INPUT_UDP)
manager.start()

print("Commands: add / remove / list / quit")

while True:
    cmd = input("\n> ").strip().lower()
    
    if cmd == "add":
        name = input("Name: ").strip()
        url = input("URL: ").strip()
        manager.add(name, url)
    
    elif cmd == "remove":
        name = input("Name: ").strip()
        manager.remove(name)
    
    elif cmd == "list":
        manager.list()
    
    elif cmd == "quit":
        manager.stop()
        break
    
    else:
        print("Unknown command")

print("Stopped")