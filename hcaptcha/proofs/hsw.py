from ..utils import is_main_process
import multiprocessing
import threading
import subprocess
import socketio

if is_main_process():
    from flask import Flask
    from flask_socketio import SocketIO
    
    app = Flask(__name__)
    sio_server = SocketIO(app)

    @sio_server.on("request")
    def request_passer(data):
        sio_server.emit("request", data)

    @sio_server.on("response")
    def response_passer(token):
        sio_server.emit("response", token)

    @app.route("/")
    def index_view():
        with open("hcaptcha-js/hsw.js") as fp:
            code = fp.read()
        
        return f"""
        <html>
        <head></head>
        <body>
            <h1>OK</h1>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>{code}</script>
            <script type="text/javascript" charset="utf-8">
                var socket = io()
                socket.on('request', async function(data) {{
                    let token = await hsw(data)
                    socket.emit('response', token)
                }})
            </script>
        </body>
        </html>
        """
        
    threading.Thread(
        target=sio_server.run,
        daemon=True,
        args=(app,),
        kwargs={"port": 9932}
        ).start()

    browser = subprocess.Popen([
        "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "--start-maximized",
        "--disable-gpu",
        "--new-window",
        "-incognito",
        "http://localhost:9932/"])

sio = socketio.Client()
lock = multiprocessing.Lock()
event = multiprocessing.Event()
proof = None

sio.connect("http://localhost:9932")

@sio.on("response")
def on_response(token):
    global proof
    proof = token
    event.set()

def get_proof(data):
    with lock:
        sio.emit("request", data)
        event.wait()
        event.clear()
        return proof
