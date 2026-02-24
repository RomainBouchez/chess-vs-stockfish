import requests
import socketio
import time

def test_http():
    try:
        r = requests.get("http://localhost:8000/")
        print(f"HTTP Root: {r.status_code} {r.json()}")
    except Exception as e:
        print(f"HTTP Failed: {e}")

def test_socket():
    sio = socketio.Client()
    
    @sio.on('connect')
    def on_connect():
        print("Socket Connected!")
        # Send a move
        sio.emit('make_move', {'uci': 'e2e4'})

    @sio.on('game_state')
    def on_state(data):
        print(f"Received Game State: FEN={data.get('fen')}")
        if data.get('turn') == 'black': # Wait for stockfish response if any
             print("It is now black's turn.")

    try:
        sio.connect('http://localhost:8000')
        time.sleep(2)
        sio.disconnect()
    except Exception as e:
        print(f"Socket Failed: {e}")

if __name__ == "__main__":
    print("Testing Backend...")
    test_http()
    test_socket()
