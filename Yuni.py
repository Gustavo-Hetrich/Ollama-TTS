import pygame
import pygame.freetype
import win32api
import win32con
import win32gui
import os
import speech_recognition as sr
import openai
import threading
import time
import edge_tts
import asyncio
import python_weather
import json

# Catálogo OpenWeather
WEATHER_DIR = "weather.txt"
# Nome do arquivo de histórico de mensagens
HISTORY_FILE = "message_history.txt"

# Inicializar Pygame e pygame.freetype
pygame.init()
pygame.freetype.init()

# Configurar a chave da API da OpenAI
openai.api_key = 'key'

# Obter as dimensões da tela
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
print(f"Screen width: {screen_width}, Screen height: {screen_height}")

# Calcular a posição no canto inferior direito
window_width = 300
window_height = 300
x_pos = screen_width - window_width
y_pos = screen_height - window_height

# Definir a posição da janela
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x_pos},{y_pos}"
print(f"Window position: x={x_pos}, y={y_pos}")

# Criar uma janela sem bordas no canto inferior direito
flags = pygame.NOFRAME
screen = pygame.display.set_mode((window_width, window_height), flags)

# Configurar a fonte com o tamanho desejado (por exemplo, 70)
font_size = 70
font = pygame.freetype.SysFont(None, font_size)

# Cor do texto
text_color = (255, 75, 255)
# Cor transparente
fuchsia = (0, 75, 0)

# Criar janela em camadas com transparência
hwnd = pygame.display.get_wm_info()['window']
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*fuchsia), 0, win32con.LWA_COLORKEY)

# Definir janela sempre no topo
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

rosto = '(O^O)'

# Configurar o reconhecimento de fala e TTS
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Lista para armazenar o histórico das mensagens
message_history = []

# Variável para controlar a calibração do microfone
microphone_calibrated = False

def save_history_to_file():
    with open(HISTORY_FILE, 'w', encoding='utf-8') as file:
        for message in message_history:
            file.write(json.dumps(message) + '\n')

def load_history_from_file():
    global message_history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as file:
            message_history = [json.loads(line) for line in file]

def recognize_speech():
    global user_text, rosto, default_text_surface, default_text_rect, message_history, microphone_calibrated

    print('Escutando...')
    rosto = '(O^O)?'
    update_face()

    with microphone as source:
        if not microphone_calibrated:
            rosto = '(@^@)'
            update_face()
            recognizer.adjust_for_ambient_noise(source, duration=5)
            microphone_calibrated = True
            print('Microfone calibrado')
            rosto = '(O^O)?'
            update_face()
        audio = recognizer.listen(source)

    try:
        user_text = recognizer.recognize_google(audio, language='pt-BR')
        print('Você disse: ' + user_text)
        response_text, rosto_update = process_text()
        if response_text:
            rosto = rosto_update
            update_face()
            speak_thread = threading.Thread(target=speak_text, args=(response_text,))
            speak_thread.start()
            speak_thread.join()
            rosto = '(O^O)'
            update_face()
    except sr.UnknownValueError:
        print('Não entendi o que você disse')
        rosto = '(?^?)'
        update_face()
        time.sleep(5)
        rosto = '(O^O)'
        update_face()
    except sr.RequestError as e:
        print(f'Erro ao solicitar resultados do serviço de reconhecimento de fala; {e}')

def process_text():
    global message_history
    message_history.append({'role': 'user', 'content': user_text})

    if len(message_history) > 8:
        message_history.pop(0)

    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': 'Seu nome é Yuni, fale com uma linguagem simples, tente soar o mais humano e natural possível, seja casual e amigável, NÃO USE EMOJIS NÃO USE EMOJIS, caso alguém chame você por um nome levemente errado apenas ignore, como ione yumi e yuri. O nome do seu criador é Gustavo, lembre-se disso'},
            *message_history
        ]
    )

    response_text = response['choices'][0]['message']['content'].strip()
    print('Yuni: ' + response_text)

    message_history.append({'role': 'assistant', 'content': response_text})
    save_history_to_file()

    if len(message_history) > 8:
        message_history.pop(0)

    response_keywords = [
        (['triste', 'tristeza', 'deprimido', 'infeliz', 'melancólico'], '(T^T)'),
        (['bravo', 'irritado', 'zangado', 'furioso', 'raiva'], '(°□°)'),
        (['morto', 'exausto', 'cansado', 'fatigado'], '(X^X)'),
        (['confuso', 'perdido', 'desorientado', 'não sei'], r'¯\_("^")_/¯'),
        (['oi', 'olá', 'eae', 'Oi', 'olá!'], '(^-^)')
    ]

    for keywords, face in response_keywords:
        if any(word in response_text for word in keywords):
            rosto_update = face
            break
    else:
        rosto_update = '(O^O)'

    return response_text, rosto_update

def speak_text(text):
    asyncio.run(communicate_and_play_tts(text))

async def communicate_and_play_tts(text):
    try:
        communicate = edge_tts.Communicate(text, voice='pt-BR-FranciscaNeural')
        output_file = 'output.mp3'
        await communicate.save(output_file)

        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f'Error in TTS synthesis or playback: {str(e)}')
    finally:
        time.sleep(0.5)
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            if os.path.exists(output_file):
                os.remove(output_file)
        except Exception as e:
            print(f'Error removing file: {str(e)}')

def blink():
    global rosto, default_text_surface, default_text_rect, is_running
    while is_running:
        if rosto == '(O^O)':
            rosto = '(=^=)'
            update_face()
            time.sleep(0.5)
            rosto = '(O^O)'
            update_face()
        time.sleep(10)

def update_face():
    global default_text_surface, default_text_rect
    default_text_surface, default_text_rect = font.render(rosto, text_color)
    pygame.display.update()

def play_startup_sound():
    startup_sound = 'startup.mp3'
    pygame.mixer.init()
    pygame.mixer.music.load(startup_sound)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# Adicionar função para gerar mensagem do tempo
async def generate_weather_message():
    try:
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            weather = await client.get("Curitiba")

            # Obter a temperatura atual e descrição do clima atual
            current_temp = weather.temperature
            current_weather_description = weather.description if weather.description else 'desconhecido'

            # Obter a descrição do clima para hoje e amanhã
            forecast_today = weather.description
            forecast_tomorrow = weather.description

        # Montar mensagem de tempo
        weather_message = (f'bom dia ou boa noite. '
                           f'A temperatura atual em Curitiba é de {current_temp}°C. '
                           f'Agora, o clima está {current_weather_description}. '
                           f'Hoje, o clima está {forecast_today}. '
                           f'E amanhã, o clima será {forecast_tomorrow}.')

        # Enviar mensagem para o GPT
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': 'Gere uma resposta amigável com base na previsão de tempo fornecida. SEM EMOJIS'},
                {'role': 'user', 'content': weather_message}
            ]
        )

        gpt_response = response['choices'][0]['message']['content'].strip()
        print('Yuni (Tempo): ' + gpt_response)
        return gpt_response

    except Exception as e:
        print(f'Error fetching or processing weather data: {str(e)}')
        return 'Desculpe, não consegui obter a previsão do tempo agora.'

def run_weather_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    weather_message = loop.run_until_complete(generate_weather_message())
    speak_text(weather_message)

def startup_sequence():
    play_startup_sound()  # Play startup sound first

    # Carregar histórico do arquivo
    load_history_from_file()
    
    # Inicializar rosto
    global is_running
    is_running = True
    blink_thread = threading.Thread(target=blink)
    blink_thread.start()

    # Executar geração de mensagem do tempo em uma thread separada
    weather_thread = threading.Thread(target=run_weather_thread)
    weather_thread.start()

is_running = True
user_text = ''
default_text_surface, default_text_rect = font.render(rosto, text_color)

blink_thread = threading.Thread(target=blink)
blink_thread.start()

song_thread = threading.Thread(target=play_startup_sound)
song_thread.start()

# Inicializar a sequência
startup_thread = threading.Thread(target=startup_sequence)
startup_thread.start()

while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                is_running = False
            elif event.key == pygame.K_HOME:  # Use the Home key to initiate listening
                threading.Thread(target=recognize_speech).start()
            elif event.key == pygame.K_BACKSPACE:
                user_text = user_text[:-1]
            else:
                user_text += event.unicode

    screen.fill(fuchsia)
    default_text_rect.center = (window_width // 2, window_height // 2)
    screen.blit(default_text_surface, default_text_rect.topleft)
    pygame.display.update()

pygame.quit()
is_running = False
blink_thread.join()
