import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
import sounddevice as sd
import threading
import time

# Параметры по умолчанию
params = {
    'A': 0.5,    # Амплитуда по X (громкость)
    'B': 0.5,    # Амплитуда по Y (громкость)
    'a': 220.0,  # Частота по X (Гц)
    'b': 440.0,  # Частота по Y (Гц)
    'delta': 0.0 # Фазовое смещение
}

# Настройки аудио
SAMPLE_RATE = 44100
audio_active = False
stream = None

# Создание фигуры
fig = plt.figure(figsize=(12, 8))
ax_plot = plt.axes([0.1, 0.3, 0.8, 0.6])

# Инициализация графики
line, = ax_plot.plot([], [], 'b-', lw=2, alpha=0.7)
point, = ax_plot.plot([], [], 'ro', markersize=8)
time_text = ax_plot.text(0.02, 0.95, '', transform=ax_plot.transAxes)

# Настройка осей
ax_plot.set_xlim(-1.5, 1.5)
ax_plot.set_ylim(-1.5, 1.5)
ax_plot.grid(True)
ax_plot.set_title('Lambda F Лиссажу ', pad=20)
ax_plot.set_xlabel('x(t) = A·sin(a·t + δ)')
ax_plot.set_ylabel('y(t) = B·sin(b·t)')

# Создание слайдеров
slider_axes = {
    'A': plt.axes([0.15, 0.25, 0.65, 0.03]),
    'B': plt.axes([0.15, 0.20, 0.65, 0.03]),
    'a': plt.axes([0.15, 0.15, 0.65, 0.03]),
    'b': plt.axes([0.15, 0.10, 0.65, 0.03]),
    'delta': plt.axes([0.15, 0.05, 0.65, 0.03])
}

sliders = {
    'A': Slider(slider_axes['A'], 'Громкость X', 0.0, 1.0, valinit=params['A']),
    'B': Slider(slider_axes['B'], 'Громкость Y', 0.0, 1.0, valinit=params['B']),
    'a': Slider(slider_axes['a'], 'Частота X (Гц)', 20, 1000, valinit=params['a']),
    'b': Slider(slider_axes['b'], 'Частота Y (Гц)', 20, 1000, valinit=params['b']),
    'delta': Slider(slider_axes['delta'], 'Смещение δ', 0, 2*np.pi, valinit=params['delta'])
}

# Кнопка звука
audio_ax = plt.axes([0.45, 0.01, 0.1, 0.04])
audio_button = Button(audio_ax, '🔊 Звук ВКЛ', color='lightgoldenrodyellow')

def toggle_audio(event):
    global audio_active
    if audio_active:
        audio_active = False
        audio_button.label.set_text('Звук ВКЛ')
        stop_audio_stream()
    else:
        audio_active = True
        audio_button.label.set_text('Звук ВЫКЛ')
        start_audio_stream()

audio_button.on_clicked(toggle_audio)

t_audio_global = 0.0
def audio_callback(outdata, frames, time_info, status):
    global t_audio_global
    t = (np.arange(frames) + t_audio_global) / SAMPLE_RATE
    t_audio_global += frames

    left = params['A'] * np.sin(2 * np.pi * params['a'] * t + params['delta'])
    right = params['B'] * np.sin(2 * np.pi * params['b'] * t)
    stereo_sound = np.column_stack((left, right)).astype(np.float32)
    
    outdata[:] = stereo_sound

def start_audio_stream():
    global stream, t_audio_global
    t_audio_global = 0.0
    stream = sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=2,
        callback=audio_callback
    )
    stream.start()

def stop_audio_stream():
    global stream
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None

# Обновление параметров
def update_params(val):
    for name in params:
        params[name] = sliders[name].val

for slider in sliders.values():
    slider.on_changed(update_params)

# Анимация
def init():
    line.set_data([], [])
    point.set_data([], [])
    time_text.set_text('')
    return line, point, time_text

def animate(i):
    t = np.linspace(0, 2*np.pi, 1000)
    current_t = 2*np.pi * i / 100
    
    x = params['A'] * np.sin(params['a']/50 * t + params['delta'])
    y = params['B'] * np.sin(params['b']/50 * t)
    x_point = params['A'] * np.sin(params['a']/50 * current_t + params['delta'])
    y_point = params['B'] * np.sin(params['b']/50 * current_t)
    
    line.set_data(x, y)
    point.set_data(x_point, y_point)
    
    freq_info = f'Частоты: {params["a"]:.1f} Гц (X) и {params["b"]:.1f} Гц (Y)'
    time_text.set_text(f'{freq_info}\nГромкость: X={params["A"]:.1f}, Y={params["B"]:.1f}')
    
    ax_plot.set_xlim(-1.2, 1.2)
    ax_plot.set_ylim(-1.2, 1.2)
    
    return line, point, time_text

ani = FuncAnimation(fig, animate, frames=100, init_func=init, interval=50, blit=True)

def on_close(event):
    global audio_active
    audio_active = False
    stop_audio_stream()

fig.canvas.mpl_connect('close_event', on_close)
plt.tight_layout()
plt.show()
