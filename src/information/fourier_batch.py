
import pytz, numpy as np
from scipy.fft import fft, fftfreq
from fastapi import WebSocket
from src.information import fourier_router
from scipy.signal.windows import blackman

GMTM3 = pytz.timezone("America/Sao_Paulo")
TEMPLATE = {'p': {'mag': {}, 'ang': {}}, 'w': {'mag': {}, 'ang': {}}}
@fourier_router.websocket("/ws/fourier-batch")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            received = await websocket.receive_json()
            x = np.asarray([float(v) for v in list(received.keys())])
            y = np.asarray(list(received.values()))
            # Number of sample points
            N = len(y)
            half = int((N/2)-1) if N % 2 == 0 else int((N-1)/2)
            # sample spacing
            T = x[1]
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