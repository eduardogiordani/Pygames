# 🏓 Pong — Refatorado com SOLID

> Projeto acadêmico da disciplina **Computação Gráfica e Tecnologias Imersivas**  
> Jogo Pong clássico em Python/Pygame, refatorado com princípios SOLID e expandido com novas mecânicas.

---

## 📋 Sobre o Projeto

| Arquivo | Descrição |
|---|---|
| `pong.py` | Versão original — funcional, porém sem separação de responsabilidades |
| `pong_SOLID.py` | Versão refatorada — aplicação completa dos princípios SOLID |
| `pong_audio.py` | Versão final — SOLID + áudio imersivo + física variável + power-up |

---

## 🎮 Como Jogar

### Pré-requisitos
```bash
pip install pygame
```

### Executar
```bash
python pong_audio.py
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

## ✨ Mecânicas Implementadas

### 🔊 Task 1 — Feedback Sonoro e Áudio Imersivo

Todos os sons são **sintetizados proceduralmente** — nenhum arquivo externo necessário.

| Evento | Som |
|---|---|
| Bola toca raquete | Beep agudo (480Hz, onda quadrada) |
| Bola toca borda | Beep grave (220Hz, onda quadrada) |
| Ponto marcado | Jingle de 3 notas ascendentes (Mi → Lá → Dó#) |
| Durante o jogo | Trilha de arpejo retro em loop |

A classe `SoundManager` centraliza toda a lógica de áudio e é injetada no `GameScene` via **Dependency Inversion**.

---

### ⚙️ Task 2 — Dinâmica de Rebote Variável

A classe `PhysicsEngine` é responsável exclusivamente pelo cálculo de física.

- **Colisão com raquete**: o ângulo de saída varia conforme o ponto de impacto na raquete (ponta vs. centro) mais um fator aleatório controlado por `BOUNCE_ANGLE_VARIANCE`.
- **Colisão com borda**: perturbação aleatória aplicada ao componente vertical da velocidade.
- **Salvaguardas**: `BALL_MIN_VY` evita que a bola viaje perfeitamente na horizontal; `BALL_MAX_SPEED` limita a velocidade total após rebotes encadeados.

---

### 🎱 Task 3 — Power-up de Fragmentação

A cada **5 segundos**, se houver colisão com uma raquete, a bola se fragmenta em **4 unidades**.

- Apenas a bola **branca** é a verdadeira — as demais são distração.
- Cada bola falsa recebe uma **cor RGB aleatória** e uma trajetória ligeiramente diferente.
- Bolinhas falsas são descartadas ao sair dos limites da tela.
- Ao marcar ponto, todas as falsas são removidas e o timer reinicia.

A classe `PowerUpManager` gerencia o timer e o spawn dos fragmentos com responsabilidade única.

---

## 🏗️ Arquitetura — Princípios SOLID

### S — Single Responsibility
Cada classe tem **uma única razão para mudar**.

```
Settings        → centraliza todas as constantes do jogo
Ball            → estado, física e identidade da bola
Paddle          → posição base e clamp de raquete
PhysicsEngine   → cálculo de rebotes e variação de ângulo
SoundManager    → síntese e reprodução de todos os sons
PowerUpManager  → timer e spawn de fragmentos
Scoreboard      → pontuação e condição de vitória
MenuScene       → loop e renderização do menu
GameScene       → orquestração do loop de jogo
```

### O — Open/Closed
`Paddle` está **fechada para modificação**, mas **aberta para extensão**.  
Adicionar uma nova IA ou um segundo jogador humano não exige alterar nenhuma classe existente.

```python
class Paddle(ABC):          
class HumanPaddle(Paddle):  
class AIPaddle(Paddle):     
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
`GameScene` depende de **abstrações**, não de implementações concretas.  
`SoundManager`, `PhysicsEngine` e `PowerUpManager` são todos injetados no construtor.

```python
game = GameScene(surface, settings, sound, physics, powerup)
```

---

## 🗂️ Estrutura de Classes

```
main()
 ├── MenuScene         → SRP: gerencia apenas o menu
 └── GameScene         → SRP + DIP: orquestra via abstrações injetadas
      ├── Ball              → SRP: estado, física e identidade
      ├── HumanPaddle       → OCP + LSP: extensão de Paddle
      ├── AIPaddle          → OCP + LSP: extensão de Paddle
      ├── PhysicsEngine     → SRP + DIP: física de rebotes injetada
      ├── SoundManager      → SRP + DIP: áudio injetado
      ├── PowerUpManager    → SRP + DIP: power-up injetado
      └── Scoreboard        → SRP: pontuação
           └── Ball, Paddle, Scoreboard implementam Drawable (ISP)
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