import os
import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import random
import time
import pygame

# Define o caminho absoluto para o diretório do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_PATH = os.path.join(BASE_DIR, 'sounds')

# Inicializa o pygame
pygame.init()

# Carrega os sons
score_sound = pygame.mixer.Sound(os.path.join(AUDIO_PATH, 'score_sound.wav'))
match_music = pygame.mixer.Sound(os.path.join(AUDIO_PATH, 'match_music.mp3'))
game_over_sound = pygame.mixer.Sound(os.path.join(AUDIO_PATH, 'game_over_sound.mp3'))
rank_music = pygame.mixer.Sound(os.path.join(AUDIO_PATH, 'rank_music.wav'))
start_sound = pygame.mixer.Sound(os.path.join(AUDIO_PATH, 'start_sound.mp3'))  # Som de início

# Define o volume dos sons
match_music.set_volume(0.2)  # Volume mais baixo para música de fundo
rank_music.set_volume(0.4)   # Volume mais alto para o som do ranking
start_sound.set_volume(0.5)  # Volume do som de início

# Webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Largura
cap.set(4, 720)   # Altura

# Hand Detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# Find Function (Distância para cm)
x = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x, y, 2)  # y = Ax^2 + Bx + C

# Variáveis do Jogo
cx, cy = 250, 250
color = (255, 0, 255)
counter = 0
score = 0
totalTime = 20  # Tempo total do jogo (em segundos)
game_started = False  # Variável para verificar se o jogo começou
game_over = False  # Variável para rastrear se o jogo terminou
timeStart = 0  # Variável para registrar o início do jogo
rank_screen = False  # Controla se a tela de ranking deve ser exibida

# Coordenadas e cor do botão "START"
start_button_color = (0, 255, 0)
start_button_pos = (640, 360)  # Centro da tela
start_button_radius = 50

# Ranking
rankings = []  # Lista para armazenar os 10 melhores resultados
name_input = ''  # Nome do jogador para o ranking
input_active = False  # Controla quando o usuário pode digitar o nome

# Nome do jogo
game_name = "Hand Target Master"

# Inicia a música de fundo, mas pausada, já que o jogo ainda não começou
pygame.mixer.Channel(0).play(match_music, loops=-1)
pygame.mixer.Channel(0).pause()

# Função para desenhar o ranking na tela
def display_ranking(img, rankings):
    cvzone.putTextRect(img, 'Ranking', (500, 150), scale=3, offset=20, thickness=5)
    for idx, (name, score) in enumerate(rankings[:10]):
        cvzone.putTextRect(img, f'{idx + 1}. {name}: {score}', (500, 200 + idx * 50), scale=2, offset=10)

# Função para atualizar o ranking
def update_ranking(name, score):
    global rankings
    rankings.append((name, score))
    rankings = sorted(rankings, key=lambda x: x[1], reverse=True)[:10]  # Mantém os 10 melhores

# Loop principal
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)  # Espelha a imagem

    # Detecta as mãos
    hands, img = detector.findHands(img, draw=False)  # Certifique-se de capturar a imagem processada também

    if not game_started:
        # Exibe o nome do jogo centralizado no topo da tela
        text_size = cv2.getTextSize(game_name, cv2.FONT_HERSHEY_COMPLEX, 2, 2)[0]
        text_x = (1280 - text_size[0]) // 2  # Centraliza o texto horizontalmente
        cvzone.putTextRect(img, game_name, (text_x, 100), scale=4, offset=20, colorR=(0, 0, 255), thickness=5)

        # Exibe o botão START centralizado
        cv2.circle(img, start_button_pos, start_button_radius, start_button_color, cv2.FILLED)
        cvzone.putTextRect(img, 'START', (start_button_pos[0] - 50, start_button_pos[1] + 10), scale=3, offset=20)

        # Verifica se a mão está "tocando" o botão START
        if hands:
            hand = hands[0]  # Acessa a primeira mão detectada
            lmList = hand['lmList']  # Lista de landmarks
            x, y, w, h = hand['bbox']  # Caixa delimitadora da mão
            x1, y1, _ = lmList[5]  # Ponto na mão que será usado para "tocar" no botão

            # Calcula a distância entre o dedo e o centro do botão START
            distance = math.sqrt((x1 - start_button_pos[0]) ** 2 + (y1 - start_button_pos[1]) ** 2)

            if distance < start_button_radius:  # Se o dedo está dentro do botão
                # Toca o som de início
                start_sound.play()

                # Inicia o jogo
                game_started = True
                timeStart = time.time()  # Marca o tempo de início do jogo

                # Retoma a música de fundo
                pygame.mixer.Channel(0).unpause()

    elif time.time() - timeStart < totalTime:
        # O jogo já começou, executa o jogo normal

        if hands:
            hand = hands[0]  # Acessa a primeira mão detectada
            lmList = hand['lmList']  # Lista de landmarks
            x, y, w, h = hand['bbox']  # Caixa delimitadora da mão
            x1, y1, _ = lmList[5]  # Ignora o valor 'z' da lista
            x2, y2, _ = lmList[17]  # Ignora o valor 'z' da lista

            # Calcula a distância entre os pontos da mão
            distance = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
            A, B, C = coff
            distanceCM = A * distance ** 2 + B * distance + C

            # Verifica se a mão está perto o suficiente do alvo
            if distanceCM < 40:
                if x < cx < x + w and y < cy < y + h:
                    counter = 1
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 3)
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (x + 5, y - 10))

        # Contador para reposicionar o círculo quando a mão tocar
        if counter:
            counter += 1
            color = (0, 255, 0)
            if counter == 3:
                cx = random.randint(100, 1100)  # Nova posição do círculo
                cy = random.randint(100, 600)
                color = (255, 0, 255)
                score += 1
                score_sound.play()  # Toca o som do ponto
                counter = 0

        # Desenha o círculo (alvo)
        cv2.circle(img, (cx, cy), 30, color, cv2.FILLED)
        cv2.circle(img, (cx, cy), 10, (255, 255, 255), cv2.FILLED)
        cv2.circle(img, (cx, cy), 20, (255, 255, 255), 2)
        cv2.circle(img, (cx, cy), 30, (50, 50, 50), 2)

        # HUD do jogo (tempo e pontuação)
        cvzone.putTextRect(img, f'Time: {int(totalTime - (time.time() - timeStart))}',
                           (1000, 75), scale=3, offset=20)
        cvzone.putTextRect(img, f'Score: {str(score).zfill(2)}', (60, 75), scale=3, offset=20)

    elif not rank_screen:  # Fim do jogo, entra na fase de inserção de nome e exibição de game over
        if not game_over:
            game_over = True
            input_active = True  # Permite que o jogador digite o nome
            # Para a música de fundo e toca o som de game over
            pygame.mixer.Channel(0).stop()  # Para o loop da música de fundo
            pygame.mixer.Channel(1).play(game_over_sound)  # Toca o som de game over
            pygame.mixer.Channel(2).play(rank_music, loops=-1)  # Toca a música de ranking em loop

        # Exibe "Game Over" e a pontuação
        cvzone.putTextRect(img, 'Game Over', (400, 200), scale=5, offset=30, thickness=7)
        cvzone.putTextRect(img, f'Your Score: {score}', (450, 300), scale=3, offset=20)

        # Entrada do nome para o ranking
        if input_active:
            cvzone.putTextRect(img, 'Enter Your Name (10 chars max):', (400, 400), scale=2, offset=10)
            cvzone.putTextRect(img, name_input, (460, 500), scale=3, offset=20)

    else:  # Exibe a tela do ranking após a inserção do nome
        # Exibe o ranking e a mensagem para reiniciar o jogo
        display_ranking(img, rankings)
        cvzone.putTextRect(img, 'Press R to Restart', (460, 650), scale=2, offset=10)

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)

    # Entrada de nome
    if input_active:
        if key == 13:  # Pressione Enter para confirmar o nome
            if len(name_input) > 0:
                update_ranking(name_input, score)
                input_active = False  # Desativa a entrada de nome após confirmação
                name_input = ''  # Limpa o campo de entrada
                rank_screen = True  # Muda para a tela de ranking
        elif key == 8:  # Pressione Backspace para apagar
            name_input = name_input[:-1]
        elif len(name_input) < 10 and 32 < key < 127:  # Limite de 10 caracteres
            name_input += chr(key)

    # Pressione 'r' para reiniciar o jogo
    if key == ord('r') and rank_screen:
        # Reinicializa o estado do jogo
        game_started = False
        game_over = False
        rank_screen = False
        score = 0
        pygame.mixer.Channel(1).stop()  # Para o som de game over
        pygame.mixer.Channel(2).stop()  # Para a música de ranking
        pygame.mixer.Channel(0).play(match_music, loops=-1)  # Reinicia a música de fundo, mas pausa até o jogo começar
        pygame.mixer.Channel(0).pause()

    # Pressione 'ESC' para sair
    if key == 27:  # 27 é o código da tecla ESC
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
