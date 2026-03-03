
# python -m venv venv
# source venv/Scripts/activate
# pip freeze
# pip install pygame
# RODAR python pygame1.py (ou qualquer nome do arquivo)

import pygame, sys, random

pygame.init()

largura, altura = 800, 600
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption('Janela')
clock = pygame.time.Clock()

fonte = pygame.font.SysFont(None, 70)

def nova_cor():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

def renderizar(p):
    p["surf"] = fonte.render(p["nome"], True, p["cor"])
    p["rect"] = p["surf"].get_rect(topleft=(p["rect"].x, p["rect"].y))

palavras = [
    {"nome": "EDUARDO", "cor": nova_cor(), "v": [2, 2]},
    {"nome": "RAFAEL",  "cor": nova_cor(), "v": [-2, -2]},
]


for i, p in enumerate(palavras):
    p["surf"] = fonte.render(p["nome"], True, p["cor"])
    p["rect"] = p["surf"].get_rect(topleft=(200 + i * 300, 400))

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


    for p in palavras:
        p["rect"].x += p["v"][0]
        p["rect"].y += p["v"][1]

        bateu = False
        if p["rect"].right >= largura or p["rect"].left <= 0:
            p["v"][0] *= -1
            p["rect"].x = max(0, min(p["rect"].x, largura - p["rect"].width)) 
            bateu = True
        if p["rect"].bottom >= altura or p["rect"].top <= 0:
            p["v"][1] *= -1
            p["rect"].y = max(0, min(p["rect"].y, altura - p["rect"].height))  
            bateu = True
        if bateu:
            p["cor"] = nova_cor()
            renderizar(p)


    p1, p2 = palavras[0], palavras[1]
    if p1["rect"].colliderect(p2["rect"]):
        p1["v"][0] *= -1
        p1["v"][1] *= -1
        p2["v"][0] *= -1
        p2["v"][1] *= -1


        while p1["rect"].colliderect(p2["rect"]):
            p1["rect"].x += p1["v"][0]
            p1["rect"].y += p1["v"][1]
            p2["rect"].x += p2["v"][0]
            p2["rect"].y += p2["v"][1]

        p1["cor"] = nova_cor()
        p2["cor"] = nova_cor()
        renderizar(p1)
        renderizar(p2)

    tela.fill((0, 0, 0))
    for p in palavras:
        tela.blit(p["surf"], p["rect"])

    clock.tick(144)
    pygame.display.flip()

