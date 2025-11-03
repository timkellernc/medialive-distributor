import subprocess
import threading
import time

INPUT_UDP = "udp://0.0.0.0:5001"

class MultiOutputStream:
    def __init__(self, input_url):
        self.input_url = input_url
        self.outputs = {}
        self.process = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _build_command(self):
        if not self.outputs:
            return None
        
        cmd = ['ffmpeg', '-i', self.input_url]
        
        for name, url in self.outputs.items():
            cmd.extend(['-c', 'copy', '-f', 'mpegts', url])
        
        return cmd
    
    def _run(self):
        while self.running:
            with self.lock:
                cmd = self._build_command()
            
            if not cmd:
                print("No outputs configured, waiting...")
                time.sleep(1)
                continue
            
            try:
                print(f"Starting stream with {len(self.outputs)} outputs")
                print(f"Command: {' '.join(cmd)}")
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                self.process.wait()
                
                if self.running:
                    print("Stream died, restarting in 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"Error: {e}")
                if self.running:
                    time.sleep(5)
    
    def add_output(self, name, url):
        with self.lock:
            if name in self.outputs:
                print(f"Output '{name}' already exists")
                return False
            
            self.outputs[name] = url
            print(f"Added output '{name}': {url}")
            
            # Restart ffmpeg with new output
            if self.process:
                self.process.terminate()
            
            return True
    
    def remove_output(self, name):
        with self.lock:
            if name not in self.outputs:
                print(f"Output '{name}' not found")
                return False
            
            del self.outputs[name]
            print(f"Removed output '{name}'")
            
            # Restart ffmpeg without this output
            if self.process:
                self.process.terminate()
            
            return True
    
    def list_outputs(self):
        with self.lock:
            if not self.outputs:
                print("No outputs configured")
            else:
                print("Configured outputs:")
                for name, url in self.outputs.items():
                    print(f"  - {name}: {url}")
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except:
                self.process.kill()

def main():
    stream = MultiOutputStream(INPUT_UDP)
    stream.start()
    
    # Add initial outputs
    stream.add_output("SRT-1", "srt://192.168.11.23:5001?mode=caller")
    
    print("\nCommands: add, remove, list, quit")
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == "quit":
                break
            elif cmd == "list":
                stream.list_outputs()
            elif cmd == "add":
                name = input("Name: ")
                url = input("URL: ")
                stream.add_output(name, url)
            elif cmd == "remove":
                name = input("Name: ")
                stream.remove_output(name)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    
    stream.stop()
    print("Done")

if __name__ == "__main__":
    main()