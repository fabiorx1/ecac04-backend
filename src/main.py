from fastapi import FastAPI, WebSocket
from fastapi.responses import RedirectResponse
import json, pytz
from datetime import datetime as dt
from src.information import fourier_router

GMTM3 = pytz.timezone("America/Sao_Paulo")

app = FastAPI()
app.include_router(fourier_router)
connections = []

@app.websocket("/ws/echo")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket.client)
    while True:
        try:
            data = await websocket.receive_json()
            now = dt.now(tz=GMTM3)
            value = list(data.values())[0]
            await websocket.send_json({now.isoformat(): value})
        except Exception as e:
            print(e)
            break
    connections.remove(websocket.client)
    await websocket.close()

@app.get('/')
async def root():
    return RedirectResponse('/docs')

@app.get("/connections")
async def get_connections():
    return json.dumps(connections)