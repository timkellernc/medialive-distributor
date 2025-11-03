import subprocess
import threading
import time
import sys
import select

INPUT_UDP = "udp://0.0.0.0:5001"

class MultiOutputStream:
    def __init__(self, input_url):
        self.input_url = input_url
        self.outputs = {}
        self.process = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.restart_flag = False
    
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
            cmd = None
            with self.lock:
                cmd = self._build_command()
                self.restart_flag = False
            
            if not cmd:
                print("\nNo outputs configured, waiting...")
                time.sleep(1)
                continue
            
            try:
                print(f"\nStarting stream with {len(self.outputs)} outputs")
                
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Wait for process to end or restart flag
                while self.running:
                    # Check if process died
                    if self.process.poll() is not None:
                        break
                    
                    # Check if restart requested
                    if self.restart_flag:
                        print("\nRestart requested, stopping current stream...")
                        self.process.terminate()
                        self.process.wait(timeout=2)
                        break
                    
                    time.sleep(0.5)
                
                if self.running and not self.restart_flag:
                    print("\nStream died, restarting in 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"\nError: {e}")
                if self.running:
                    time.sleep(5)
    
    def add_output(self, name, url):
        with self.lock:
            if name in self.outputs:
                print(f"Output '{name}' already exists")
                return False
            
            self.outputs[name] = url
            print(f"Added output '{name}': {url}")
            self.restart_flag = True
            
            return True
    
    def remove_output(self, name):
        with self.lock:
            if name not in self.outputs:
                print(f"Output '{name}' not found")
                return False
            
            del self.outputs[name]
            print(f"Removed output '{name}'")
            self.restart_flag = True
            
            return True
    
    def list_outputs(self):
        with self.lock:
            if not self.outputs:
                print("No outputs configured")
            else:
                print("Configured outputs:")
                for name, url in self.outputs.items():
                    print(f"  - {name}: {url}")
    
    def get_status(self):
        if not self.running:
            return "Stopped"
        if self.process and self.process.poll() is None:
            return f"Running ({len(self.outputs)} outputs)"
        return "Starting..."
    
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
    stream.add_output("UDP-1", "udp://192.168.11.23:5000")
    
    print("\nCommands: add, remove, list, status, quit")
    print("(Press Enter if prompt doesn't appear)")
    
    try:
        while True:
            try:
                cmd = input("\n> ").strip().lower()
            except EOFError:
                break
            
            if not cmd:
                continue
            
            if cmd == "quit" or cmd == "q":
                break
            elif cmd == "list" or cmd == "l":
                stream.list_outputs()
            elif cmd == "status" or cmd == "s":
                print(f"Status: {stream.get_status()}")
            elif cmd == "add" or cmd == "a":
                name = input("Name: ").strip()
                url = input("URL: ").strip()
                if name and url:
                    stream.add_output(name, url)
            elif cmd == "remove" or cmd == "r":
                name = input("Name: ").strip()
                if name:
                    stream.remove_output(name)
            else:
                print("Unknown command. Available: add, remove, list, status, quit")
                
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    stream.stop()
    print("Done")

if __name__ == "__main__":
    main()