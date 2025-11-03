import subprocess
import threading
import time

INPUT_UDP = "udp://0.0.0.0:5001"

class StreamOutput:
    def __init__(self, name, input_url, output_url):
        self.name = name
        self.input_url = input_url
        self.output_url = output_url
        self.process = None
        self.running = False
        self.thread = None
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        while self.running:
            try:
                print(f"[{self.name}] Starting stream to {self.output_url}")
                
                cmd = [
                    'ffmpeg',
                    '-reconnect', '1',
                    '-reconnect_streamed', '1',
                    '-reconnect_delay_max', '5',
                    '-i', self.input_url,
                    '-c', 'copy',
                    '-f', 'mpegts',
                    self.output_url
                ]
                
                print(f"[{self.name}] Command: {' '.join(cmd)}")
                
                # Run without hiding output so we can see errors
                self.process = subprocess.Popen(cmd)
                
                self.process.wait()
                
                if self.running:
                    print(f"[{self.name}] Stream died, reconnecting in 5 seconds...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                if self.running:
                    time.sleep(5)
    
    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()

class StreamManager:
    def __init__(self, input_url):
        self.input_url = input_url
        self.streams = {}
    
    def add_stream(self, name, output_url):
        if name in self.streams:
            print(f"Stream '{name}' already exists")
            return
        
        stream = StreamOutput(name, self.input_url, output_url)
        stream.start()
        self.streams[name] = stream
        print(f"Added stream '{name}'")
    
    def remove_stream(self, name):
        if name not in self.streams:
            print(f"Stream '{name}' not found")
            return
        
        self.streams[name].stop()
        del self.streams[name]
        print(f"Removed stream '{name}'")
    
    def list_streams(self):
        if not self.streams:
            print("No active streams")
        else:
            print("Active streams:")
            for name in self.streams.keys():
                print(f"  - {name}: {self.streams[name].output_url}")
    
    def stop_all(self):
        for stream in self.streams.values():
            stream.stop()
        self.streams.clear()

def main():
    manager = StreamManager(INPUT_UDP)
    
    # Add initial streams
    manager.add_stream("UDP-1", "udp://192.168.11.23:5000")
    
    print("\nCommands: add, remove, list, quit")
    
    try:
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == "quit":
                break
            elif cmd == "list":
                manager.list_streams()
            elif cmd == "add":
                name = input("Name: ")
                url = input("URL: ")
                manager.add_stream(name, url)
            elif cmd == "remove":
                name = input("Name: ")
                manager.remove_stream(name)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    
    manager.stop_all()
    print("Done")

if __name__ == "__main__":
    main()