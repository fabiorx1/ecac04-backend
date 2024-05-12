
import pytz, numpy as np
from scipy.fft import fft, fftfreq
from datetime import datetime as dt, timedelta
from fastapi import WebSocket
from src.information import fourier_router
from scipy.signal.windows import blackman

GMTM3 = pytz.timezone("America/Sao_Paulo")
TEMPLATE = {'p': {'mag': {}, 'ang': {}}, 'w': {'mag': {}, 'ang': {}}}
@fourier_router.websocket("/ws/fourier")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    buffer = {}
    while True:
        try:
            received = await websocket.receive_json()
            if received.get('command', None) == 'clear':
                buffer = {}
                await websocket.send_json(TEMPLATE)
                continue
            buffer.update(received)
            if len(buffer) == 1:
                await websocket.send_json(TEMPLATE)
                continue
            timestamps = list(buffer.keys())
            signal = np.asarray(list(buffer.values()))
            # Number of sample points
            N = len(buffer)
            half = int((N/2)-1) if N % 2 == 0 else int((N-1)/2)
            # sample spacing
            _indexes = range(1, len(timestamps))
            millisecs = lambda i: (dt.fromisoformat(timestamps[i])
                                   - dt.fromisoformat(timestamps[i-1])).microseconds / 1e3
            x = [0] + [millisecs(i)/1e3 for i in _indexes]
            T = np.average(x[1:])
            y = signal
            #  fft e windowed fft
            xf = fftfreq(N, T)[:half + 1]
            p_yf = fft(y)
            windows = blackman(N)
            w_yf = fft(y*windows)
            p_magnitudes = np.append(1/N * np.abs([p_yf[0]]), 2/N * np.abs(p_yf[1:half+1]))
            w_magnitudes = np.append(1/N * np.abs([w_yf[0]]), 2/N * np.abs(w_yf[1:half+1]))
            p_angles = np.angle(p_yf[:half+1])
            w_angles = np.angle(w_yf[:half+1])
            p = {'mag': {xf[i]: p_magnitudes[i] for i in range(half+1)},
                 'ang': {xf[i]: p_angles[i] for i in range(half+1)}}
            w = {'mag': {xf[i]: w_magnitudes[i] for i in range(half+1)},
                 'ang': {xf[i]: w_angles[i] for i in range(half+1)}}
            await websocket.send_json({'p': p, 'w': w})
        except Exception as e:
            print(e)
            break
    await websocket.close()