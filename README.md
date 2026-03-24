# 🏓 Pong — Refatorado com SOLID

> Projeto acadêmico da disciplina **Computação Gráfica e Tecnologias Imersivas**  
> Jogo Pong clássico em Python/Pygame, refatorado com os princípios SOLID de design orientado a objetos.

---

## 📋 Sobre o Projeto

Este repositório contém dois marcos do desenvolvimento:

| Arquivo | Descrição |
|---|---|
| `pong.py` | Versão original — funcional, porém sem separação de responsabilidades |
| `pong_SOLID.py` | Versão refatorada — aplicação completa dos princípios SOLID |

O objetivo **não foi alterar o jogo**, mas demonstrar como os mesmos comportamentos podem ser organizados de forma mais legível, extensível e manutenível.

---

## 🎮 Como Jogar

### Pré-requisitos
```bash
pip install pygame
```

### Executar
```bash
python pong_SOLID.py
```

### Controles

| Tecla | Ação |
|---|---|
| `↑` | Mover raquete para cima |
| `↓` | Mover raquete para baixo |
| `ESPAÇO` | Iniciar partida (no menu) |

> O jogador controla a raquete da **esquerda**. A raquete da direita é controlada por IA.  
> Primeiro a marcar **10 pontos** vence.

---

## 🏗️ Arquitetura — Princípios SOLID

### S — Single Responsibility
Cada classe tem **uma única razão para mudar**.

```
Settings    → centraliza todas as constantes do jogo
Ball        → estado e física da bola
Paddle      → posição base e clamp de raquete
Scoreboard  → pontuação e condição de vitória
MenuScene   → loop e renderização do menu
GameScene   → orquestração do loop de jogo
```

### O — Open/Closed
`Paddle` está **fechada para modificação**, mas **aberta para extensão**.  
Adicionar uma nova IA ou um segundo jogador humano não exige alterar nenhuma classe existente.

```python
class Paddle(ABC):          # base fechada para modificação
    ...

class HumanPaddle(Paddle):  # extensão sem alterar a base
    ...

class AIPaddle(Paddle):     # extensão sem alterar a base
    ...
```

### L — Liskov Substitution
`HumanPaddle` e `AIPaddle` são **completamente intercambiáveis** onde `Paddle` é esperado.  
`GameScene` chama `.update()` e `.draw()` sem saber qual tipo está usando.

### I — Interface Segregation
O protocolo `Drawable` define o contrato mínimo de renderização.  
Nenhuma classe é forçada a implementar métodos que não usa.

```python
class Drawable(ABC):
    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None: ...
```

### D — Dependency Inversion
`GameScene` depende da **abstração** `Paddle`, não das implementações concretas.  
O loop de renderização itera sobre `Drawable` — não importa o que está na lista.

```python
self._p1: Paddle = HumanPaddle(...)   # tipo declarado é a abstração
self._p2: Paddle = AIPaddle(...)      # concretude injetada na construção
self._drawables: list[Drawable] = [self._p1, self._p2, self._ball, self._board]
```

---

## 🗂️ Estrutura de Classes

```
main()
 ├── MenuScene       → SRP: gerencia apenas o menu
 └── GameScene       → SRP + DIP: orquestra via abstrações
      ├── Ball            → SRP: física da bola
      ├── HumanPaddle     → OCP + LSP: extensão de Paddle
      ├── AIPaddle        → OCP + LSP: extensão de Paddle
      └── Scoreboard      → SRP: pontuação
           └── todos implementam Drawable (ISP)
```

---

## 🛠️ Tecnologias

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.x-00B140?style=flat)

---

## 👤 Autor

**Eduardo Giordani**  
Disciplina: Computação Gráfica e Tecnologias Imersivas  
[![GitHub](https://img.shields.io/badge/GitHub-eduardogiordani-181717?style=flat&logo=github)](https://github.com/eduardogiordani/Pygames)
