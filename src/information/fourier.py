
import pytz, numpy as np
from scipy.fft import fft, fftfreq
from datetime import datetime as dt, timedelta
from fastapi import WebSocket
from src.information import fourier_router

GMTM3 = pytz.timezone("America/Sao_Paulo")

@fourier_router.websocket("/ws/fourier")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    buffer = {}
    while True:
        try:
            measure = await websocket.receive_json()
            buffer.update(measure)
            timestamps = list(buffer.keys())
            signal = np.asarray(list(buffer.values()))
            if len(buffer) == 1:
                await websocket.send_json({0: float(signal[0])})
                continue
            # Number of sample points
            N = len(buffer)
            half = int((N/2)-1) if N % 2 == 0 else int((N-1)/2)
            # sample spacing
            _indexes = range(1, len(timestamps))
            
            millisecs = lambda i: (dt.fromisoformat(timestamps[i])
                                   - dt.fromisoformat(timestamps[i-1])).microseconds / 1e3
            x = [0] + [millisecs(i)/1e3 for i in _indexes]
            T = np.average(x[1:])
            #  fft
            y = signal
            yf = fft(y)
            xf = fftfreq(N, T)[:half + 1]
            magnitudes = np.append(1/N * np.abs([yf[0]]), 2/N * np.abs(yf[1:half+1]))
            angles = np.angle(yf[:half+1])
            response = {'mag': {xf[i]: magnitudes[i] for i in range(half+1)},
                        'ang': {xf[i]: angles[i] for i in range(half+1)}}
            await websocket.send_json(response)
        except Exception as e:
            print(e)
            break
    await websocket.close()