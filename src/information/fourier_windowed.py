from fastapi import FastAPI, WebSocket
import pytz, numpy as np
from datetime import datetime as dt, timedelta
from scipy.fft import fft, fftfreq

GMTM3 = pytz.timezone("America/Sao_Paulo")

app = FastAPI()

connections = []

@app.websocket("/ws/fourier/windowed")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket.client)
    buffer = {}
    while True:
        try:
            timestamps = list(buffer.keys())
            signal = np.asarray(list(buffer.values()))
            buffer.update(await websocket.receive_json())
            if len(buffer) == 1:
                await websocket.send_json(buffer)
                continue
            t0 :dt = timestamps[0]
            # https://docs.scipy.org/doc/scipy/tutorial/fft.html
            # Number of sample points
            N = len(buffer)
            # sample spacing
            _indexes = range(1, len(timestamps))
            millisecs = lambda i: (timestamps[i] - timestamps[i-1]).microseconds / 1e3
            x = [0] + [millisecs(i)/1e3 for i in _indexes]
            y = signal
            yf = fft(y)
            from scipy.signal.windows import blackman
            w = blackman(N)
            ywf = fft(y*w)
            xf = fftfreq(N, T)[:N//2]
            import matplotlib.pyplot as plt
            plt.semilogy(xf[1:N//2], 2.0/N * np.abs(yf[1:N//2]), '-b')
            plt.semilogy(xf[1:N//2], 2.0/N * np.abs(ywf[1:N//2]), '-r')
            plt.legend(['FFT', 'FFT w. window'])
            plt.grid()
            plt.show()
            await websocket.send_json(buffer)
        except Exception as e:
            print(e)
            break
    connections.remove(websocket.client)
    await websocket.close()