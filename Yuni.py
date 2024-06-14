import pygame
import pygame.freetype
import win32api
import win32con
import win32gui
import os
import speech_recognition as sr
import pyttsx3
import openai
import threading
import time

# Inicializar Pygame
pygame.init()

# Inicializar pygame.freetype
pygame.freetype.init()

# Configurar a chave da API da OpenAI
openai.api_key = 'APIKEY'

# Obter as dimensões da tela após a inicialização do Pygame
screen_width, screen_height = pygame.display.list_modes()[0]

# Calcular a posição no canto inferior direito
window_width = 300
window_height = 300
x_pos = screen_width - window_width
y_pos = screen_height - window_height

# Definir a posição da janela
os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x_pos},{y_pos}"

# Criar uma janela sem bordas no canto inferior direito
flags = pygame.NOFRAME
screen = pygame.display.set_mode((window_width, window_height), flags)

# Configurar a fonte com o tamanho desejado (por exemplo, 70)
font_size = 70
font = pygame.freetype.SysFont(None, font_size)  # Usar a fonte padrão do sistema

# Cor do texto
text_color = (255, 75, 255)

# Cor transparente
fuchsia = (0, 75, 0)

# Criar janela em camadas com transparência
hwnd = pygame.display.get_wm_info()["window"]
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*fuchsia), 0, win32con.LWA_COLORKEY)

# Definir janela sempre no topo
win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

rosto = "(O^O)"

# Configurar o reconhecimento de fala e TTS
recognizer = sr.Recognizer()
microphone = sr.Microphone()
engine = pyttsx3.init()

# Lista para armazenar o histórico das mensagens
message_history = []

# Função para reconhecer fala e atualizar user_text
def recognize_speech():
    global user_text, rosto, default_text_surface, default_text_rect, message_history
    
    print("Escutando...")
    rosto = "(@w@--)"
    default_text_surface, default_text_rect = font.render(rosto, text_color)
    pygame.display.update()  # Atualiza a tela imediatamente com o rosto de escuta

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        user_text = recognizer.recognize_google(audio, language="pt-BR")
        print("Você disse: " + user_text)
        response_text, rosto_update = process_text()
        if response_text:
            rosto = rosto_update
            default_text_surface, default_text_rect = font.render(rosto, text_color)
            pygame.display.update()  # Atualiza a tela imediatamente com o novo rosto
            threading.Thread(target=speak_text, args=(response_text,)).start()  # Spawn a new thread to handle TTS
    except sr.UnknownValueError:
        print("Não entendi o que você disse")
        rosto = "(?^?)"
        default_text_surface, default_text_rect = font.render(rosto, text_color)
        pygame.display.update()  # Atualiza a tela imediatamente com o rosto de não entendimento
        time.sleep(5)  # Mantém o rosto por 5 segundos
        rosto = "(O^O)"
        default_text_surface, default_text_rect = font.render(rosto, text_color)
        pygame.display.update()  # Volta ao rosto padrão
    except sr.RequestError as e:
        print("Erro ao solicitar resultados do serviço de reconhecimento de fala; {0}".format(e))

# Função para processar o texto usando a API da OpenAI
def process_text():
    global message_history
    # Adicionar a mensagem do usuário ao histórico
    message_history.append({"role": "user", "content": user_text})

    # Manter apenas as últimas 8 mensagens
    if len(message_history) > 8:
        message_history.pop(0)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Seu nome é Yuni, fale com uma linguagem simples, tente soar o mais humano e natural possível, seja casual e amigável"},
            *message_history
        ]
    )

    response_text = response['choices'][0]['message']['content'].strip()
    print("ChatGPT: " + response_text)

    # Adicionar a resposta do ChatGPT ao histórico
    message_history.append({"role": "assistant", "content": response_text})

    # Manter apenas as últimas 8 mensagens
    if len(message_history) > 8:
        message_history.pop(0)

    # Analisar o response_text para determinar a expressão do rosto
    if any(word in response_text for word in ['triste', 'tristeza', 'deprimido', 'infeliz', 'melancólico']):
        rosto_update = '(T^T)'
    elif any(word in response_text for word in ['bravo', 'irritado', 'zangado', 'furioso', 'raiva']):
        rosto_update = '(°□°)'
    elif any(word in response_text for word in ['morto', 'exausto', 'cansado', 'fatigado']):
        rosto_update = '(X^X)'
    elif any(word in response_text for word in ['confuso', 'perdido', 'desorientado', 'não sei']):
        rosto_update = r'¯\_("^")_/¯'
    elif any(word in response_text for word in ['oi', 'olá', 'eae', 'Oi', 'olá!']):
        rosto_update = '(^-^)'    
    else:
        rosto_update = "(O^O)"
    
    return response_text, rosto_update

# Função para falar o texto
def speak_text(text):
    engine.say(text)
    engine.runAndWait()

# Função para piscar
def blink():
    global rosto, default_text_surface, default_text_rect, is_running
    while is_running:
        if rosto == "(O^O)":
            # Fechar os olhos
            rosto = "(=^=)"
            default_text_surface, default_text_rect = font.render(rosto, text_color)
            pygame.display.update()  # Atualiza a tela imediatamente
            time.sleep(0.5)
            # Abrir os olhos
            rosto = "(O^O)"
            default_text_surface, default_text_rect = font.render(rosto, text_color)
            pygame.display.update()  # Atualiza a tela imediatamente
        time.sleep(10)  # Piscar a cada 10 segundos

# Loop principal do jogo
is_running = True
user_text = ''  # Inicializar uma string vazia para entrada do usuário

# Renderizar o texto inicial para rosto
default_text_surface, default_text_rect = font.render(rosto, text_color)

# Iniciar o thread de piscar
blink_thread = threading.Thread(target=blink)
blink_thread.start()

while is_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                is_running = False
            elif event.key == pygame.K_RETURN:
                threading.Thread(target=recognize_speech).start()
            elif event.key == pygame.K_BACKSPACE:
                user_text = user_text[:-1]
            else:
                user_text += event.unicode

    # Preencher a tela com a cor transparente
    screen.fill(fuchsia)

    # Posicionar os retângulos de texto
    default_text_rect.center = (window_width // 2, window_height // 2)

    # Blitar o texto padrão na tela
    screen.blit(default_text_surface, default_text_rect.topleft)

    pygame.display.update()

# Sair do Pygame
pygame.quit()
is_running = False
blink_thread.join()
