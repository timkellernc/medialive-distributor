import subprocess
import threading
import time
import sys

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
            cmd = ['ffmpeg', '-nostdin', '-i', self.input_url]
            for url in self.outputs.values():
                cmd.extend(['-c', 'copy', '-f', 'mpegts', url])
            
            sys.stdout.write(f"\n[Starting ffmpeg with {len(self.outputs)} output(s)]\n")
            sys.stdout.flush()
            
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            self.needs_restart = False
            
            # Wait for ffmpeg to die or restart signal
            while self.process.poll() is None and not self.needs_restart:
                time.sleep(0.5)
            
            if self.needs_restart:
                self.process.terminate()
                self.process.wait()
            else:
                sys.stdout.write("[FFmpeg died, restarting in 5s]\n")
                sys.stdout.flush()
                time.sleep(5)
    
    def add(self, name, url):
        self.outputs[name] = url
        sys.stdout.write(f"Added: {name} -> {url}\n")
        sys.stdout.flush()
        self.needs_restart = True
    
    def remove(self, name):
        if name in self.outputs:
            del self.outputs[name]
            sys.stdout.write(f"Removed: {name}\n")
            sys.stdout.flush()
            self.needs_restart = True
        else:
            sys.stdout.write(f"Not found: {name}\n")
            sys.stdout.flush()
    
    def list(self):
        if self.outputs:
            for name, url in self.outputs.items():
                sys.stdout.write(f"  {name}: {url}\n")
                sys.stdout.flush()
        else:
            sys.stdout.write("  (no outputs)\n")
            sys.stdout.flush()
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

# Main
sys.stdout.write("Starting manager...\n")
sys.stdout.flush()

manager = StreamManager(INPUT_UDP)
manager.start()

sys.stdout.write("\nCommands: add / remove / list / quit\n\n")
sys.stdout.flush()

while True:
    try:
        sys.stdout.write("> ")
        sys.stdout.flush()
        cmd = sys.stdin.readline().strip().lower()
        
        if not cmd:
            continue
        
        if cmd == "add":
            sys.stdout.write("Name: ")
            sys.stdout.flush()
            name = sys.stdin.readline().strip()
            sys.stdout.write("URL: ")
            sys.stdout.flush()
            url = sys.stdin.readline().strip()
            manager.add(name, url)
        
        elif cmd == "remove":
            sys.stdout.write("Name: ")
            sys.stdout.flush()
            name = sys.stdin.readline().strip()
            manager.remove(name)
        
        elif cmd == "list":
            manager.list()
        
        elif cmd == "quit":
            manager.stop()
            break
        
        else:
            sys.stdout.write("Unknown command\n")
            sys.stdout.flush()
    
    except KeyboardInterrupt:
        manager.stop()
        break

sys.stdout.write("Stopped\n")
sys.stdout.flush()