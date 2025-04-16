import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
import sounddevice as sd
import tkinter as tk
from tkinter import simpledialog

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
mode_lissajous = True  # True = Лиссажу, False = x(t)/y(t)

# Создание фигуры
fig = plt.figure(figsize=(12, 9))

# Основной график Лиссажу
ax_lissajous = plt.axes([0.1, 0.45, 0.8, 0.45])
line_lissajous, = ax_lissajous.plot([], [], 'b-', lw=2, alpha=0.7)
point_lissajous, = ax_lissajous.plot([], [], 'ro', markersize=8)
time_text = ax_lissajous.text(0.02, 0.95, '', transform=ax_lissajous.transAxes)
ax_lissajous.set_title('Lambda F Лиссажу', pad=20)
ax_lissajous.set_xlabel('x(t) = A·sin(a·t + δ)')
ax_lissajous.set_ylabel('y(t) = B·sin(b·t)')
ax_lissajous.set_xlim(-1.5, 1.5)
ax_lissajous.set_ylim(-1.5, 1.5)
ax_lissajous.grid(True)

# График x(t)
ax_xt = plt.axes([0.1, 0.65, 0.8, 0.25])
line_xt, = ax_xt.plot([], [], 'g-', lw=2)
point_xt, = ax_xt.plot([], [], 'ro', markersize=6)
ax_xt.set_title('Lambda F Лиссажу', pad=20)
ax_xt.set_ylabel('x(t)')
ax_xt.grid(True)
ax_xt.set_visible(False)

# График y(t)
ax_yt = plt.axes([0.1, 0.35, 0.8, 0.25])
line_yt, = ax_yt.plot([], [], 'r-', lw=2)
point_yt, = ax_yt.plot([], [], 'ro', markersize=6)
ax_yt.set_xlabel('t')
ax_yt.set_ylabel('y(t)')
ax_yt.grid(True)
ax_yt.set_visible(False)

# Слайдеры
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
    'a': Slider(slider_axes['a'], 'Частота X (Гц)', 100, 1000, valinit=params['a']),
    'b': Slider(slider_axes['b'], 'Частота Y (Гц)', 100, 1000, valinit=params['b']),
    'delta': Slider(slider_axes['delta'], 'Смещение δ', 0, 2*np.pi, valinit=params['delta'])
}

def update_params(val):
    for name in params:
        params[name] = sliders[name].val

for slider in sliders.values():
    slider.on_changed(update_params)

# Кнопка звука
audio_ax = plt.axes([0.05, 0.01, 0.1, 0.04])
audio_button = Button(audio_ax, 'Звук ВКЛ', color='lightgoldenrodyellow')

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

# Кнопка переключения режима
mode_ax = plt.axes([0.2, 0.01, 0.15, 0.04])
mode_button = Button(mode_ax, 'Режим: Лиссажу', color='lightblue')

def toggle_mode(event):
    global mode_lissajous
    mode_lissajous = not mode_lissajous

    if mode_lissajous:
        mode_button.label.set_text('Режим: Лиссажу')
        ax_lissajous.set_visible(True)
        ax_xt.set_visible(False)
        ax_yt.set_visible(False)
    else:
        mode_button.label.set_text('Режим: x(t), y(t)')
        ax_lissajous.set_visible(False)
        ax_xt.set_visible(True)
        ax_yt.set_visible(True)

    plt.draw()

mode_button.on_clicked(toggle_mode)

# Кнопка полноэкранного режима
fullscreen_ax = plt.axes([0.4, 0.01, 0.15, 0.04])
fullscreen_button = Button(fullscreen_ax, 'На весь экран', color='lightgray')

def toggle_fullscreen(event):
    fig.canvas.manager.full_screen_toggle()

fullscreen_button.on_clicked(toggle_fullscreen)

# Кнопка блокировки
lock_ax = plt.axes([0.6, 0.01, 0.15, 0.04])
lock_button = Button(lock_ax, 'Заблокировать', color='salmon')

interface_locked = False
PASSWORD = "1234"

def set_sliders_active(state):
    for slider in sliders.values():
        slider.eventson = state
        slider.active = state

def set_buttons_active(state):
    audio_button.eventson = state
    mode_button.eventson = state
    fullscreen_button.eventson = state

def lock_interface(event):
    global interface_locked

    if not interface_locked:
        # Блокируем интерфейс
        set_sliders_active(False)
        set_buttons_active(False)
        interface_locked = True
        lock_button.label.set_text("Разблокировать")
        lock_button.color = 'lightgreen'
    else:
        root = tk.Tk()
        root.withdraw()
        password = simpledialog.askstring("Разблокировка", "Введите пароль:", show='*')
        root.destroy()

        if password == PASSWORD:
            set_sliders_active(True)
            set_buttons_active(True)
            interface_locked = False
            lock_button.label.set_text("Заблокировать")
            lock_button.color = 'salmon'
        else:
            print("Неверный пароль!")

lock_button.on_clicked(lock_interface)

# Текущий активный слайдер
current_active_slider = None
def get_active_slider(event):
    global current_active_slider
    for name, slider in sliders.items():
        if slider.ax == event.inaxes:
            current_active_slider = slider
            return slider
    return None

# Обработчик событий колеса мыши
def on_scroll(event):
    if interface_locked:
        return
    
    slider = get_active_slider(event)
    if slider is None:
        return
    
    # Определяем шаг изменения в зависимости от слайдера
    if slider == sliders['a'] or slider == sliders['b']:
        step = 1  # Шаг 1 для частот
        current_val = round(slider.val)  # Округляем текущее значение
    else:
        step = (slider.valmax - slider.valmin) / 100  # 1% от диапазона для остальных
        current_val = slider.val
    
    if event.button == 'up':
        new_val = min(current_val + step, slider.valmax)
    else:
        new_val = max(current_val - step, slider.valmin)
    if slider == sliders['a'] or slider == sliders['b']:
        new_val = round(new_val)
    
    slider.set_val(new_val)
    update_params(new_val)

# Обработчик событий клавиатуры (стрелки)
def on_key(event):
    if interface_locked:
        return
    
    slider = current_active_slider
    if slider is None:
        return

    if slider == sliders['a'] or slider == sliders['b']:
        step = 1 
        current_val = round(slider.val) 
    else:
        step = (slider.valmax - slider.valmin) / 100  
        current_val = slider.val
    
    if event.key == 'up' or event.key == 'right':
        new_val = min(current_val + step, slider.valmax)
    elif event.key == 'down' or event.key == 'left':
        new_val = max(current_val - step, slider.valmin)
    else:
        return
    
    if slider == sliders['a'] or slider == sliders['b']:
        new_val = round(new_val)
    
    slider.set_val(new_val)
    update_params(new_val)


# Глобальные переменные для ввода с клавиатуры
current_input = ""
current_active_slider = None
last_active_slider = None

def on_motion(event):
    global current_input, current_active_slider, last_active_slider
    
    if event.inaxes:
        # Проверяем, находится ли курсор над слайдером
        for name, slider in sliders.items():
            if slider.ax == event.inaxes:
                # Если перешли на новый слайдер - сбрасываем ввод
                if slider != last_active_slider:
                    current_input = ""
                    last_active_slider = slider
                current_active_slider = slider
                return
        
    # Если курсор не над слайдером - сбрасываем активный слайдер
    if current_active_slider is not None:
        current_active_slider = None
        current_input = ""
        update_slider_labels()

def on_key_press(event):
    global current_input
    
    if interface_locked or current_active_slider is None:
        return
    
    # Цифры добавляем к текущему вводу
    if event.key in '0123456789':
        current_input += event.key
        update_slider_from_input()
    
    # Точка/запятая для десятичных дробей
    elif event.key in ['.', ','] and '.' not in current_input:
        current_input += '.'
        update_slider_from_input()
    
    # Backspace - удаляем последний символ
    elif event.key == 'backspace' and len(current_input) > 0:
        current_input = current_input[:-1]
        update_slider_from_input()
    
    # Escape или Enter - сбрасываем ввод
    elif event.key in ['escape', 'enter']:
        current_input = ""
        update_slider_labels()
    
    # Стрелки - стандартная обработка
    elif event.key in ['up', 'down', 'left', 'right']:
        on_key(event)  # Вызываем существующий обработчик стрелок
    
    # Обновляем текст на слайдере
    update_slider_labels()

def update_slider_from_input():
    global current_input
    
    if current_active_slider is None or not current_input:
        return
    
    try:
        new_value = float(current_input)
        
        # Для частот округляем до целого
        if current_active_slider in [sliders['a'], sliders['b']]:
            new_value = round(new_value)
        
        # Проверяем границы
        new_value = max(current_active_slider.valmin, 
                       min(current_active_slider.valmax, new_value))
        
        current_active_slider.set_val(new_value)
        update_params(new_value)
        
    except ValueError:
        pass  # Игнорируем некорректный ввод

def update_slider_labels():
    for name, slider in sliders.items():
        if slider == current_active_slider and current_input:
            # Временное отображение вводимого значения
            slider.label.set_text(f"{params_descriptions[name]}: {current_input}")
        else:
            # Стандартное отображение
            slider.label.set_text(f"{params_descriptions[name]}: {slider.val:.2f}")
    plt.draw()

# Описания параметров для отображения
params_descriptions = {
    'A': 'Громкость X',
    'B': 'Громкость Y',
    'a': 'Частота X (Гц)',
    'b': 'Частота Y (Гц)',
    'delta': 'Смещение δ'
}

# Подключаем обработчики
fig.canvas.mpl_connect('key_press_event', on_key_press)
fig.canvas.mpl_connect('motion_notify_event', on_motion)
fig.canvas.mpl_connect('scroll_event', on_scroll)

# Анимация
def init():
    line_lissajous.set_data([], [])
    point_lissajous.set_data([], [])
    time_text.set_text('')

    line_xt.set_data([], [])
    point_xt.set_data([], [])
    line_yt.set_data([], [])
    point_yt.set_data([], [])

    return line_lissajous, point_lissajous, time_text, line_xt, point_xt, line_yt, point_yt

def animate(i):
    t = np.linspace(0, 2*np.pi, 1000)
    current_t = 2*np.pi * i / 100

    x = params['A'] * np.sin(params['a']/50 * t + params['delta'])
    y = params['B'] * np.sin(params['b']/50 * t)
    x_point = params['A'] * np.sin(params['a']/50 * current_t + params['delta'])
    y_point = params['B'] * np.sin(params['b']/50 * current_t)

    if mode_lissajous:
        line_lissajous.set_data(x, y)
        point_lissajous.set_data(x_point, y_point)
        time_text.set_text(f'Частоты: {params["a"]:.1f} Гц (X) и {params["b"]:.1f} Гц (Y)\n'
                           f'Громкость: X={params["A"]:.1f}, Y={params["B"]:.1f}')
        return line_lissajous, point_lissajous, time_text
    else:
        line_xt.set_data(t, x)
        point_xt.set_data(current_t, x_point)
        ax_xt.set_xlim(t[0], t[-1])
        ax_xt.set_ylim(-1.2, 1.2)

        line_yt.set_data(t, y)
        point_yt.set_data(current_t, y_point)
        ax_yt.set_xlim(t[0], t[-1])
        ax_yt.set_ylim(-1.2, 1.2)

        return line_xt, point_xt, line_yt, point_yt

ani = FuncAnimation(fig, animate, frames=100, init_func=init, interval=50, blit=True)

def on_close(event):
    global audio_active
    audio_active = False
    stop_audio_stream()

fig.canvas.mpl_connect('close_event', on_close)
plt.tight_layout()
plt.show()