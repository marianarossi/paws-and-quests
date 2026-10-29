# Paws & Quests

Jogo de plataforma 2D de precisão feito em Godot. Projeto Final da Licenciatura em Engenharia Informática da Universidade Politécnica de Bragança, 2025/2026.

Autora: Mariana Rossi (a67709). Orientação: Rui Pedro Lopes e Júlio César Leal de Faria.

## Jogar

- **Executável (Windows):** descarregar `PawsAndQuests_v1.0.9.zip` em [Releases](https://github.com/marianarossi/paws-and-quests/releases/latest), extrair e abrir `PawsAndQuests.exe`. Não precisa de instalação nem do Godot.
- **A partir do código:** abrir o [Godot 4.6.3](https://godotengine.org/download/archive/4.6.3-stable/), importar este diretório (`project.godot`) e premir F5.

O jogo abre em inglês; o português escolhe-se em Options > Language.

| Ação | Teclado | Comando |
|---|---|---|
| Andar | Setas ou WASD | Direcional / analógico |
| Pular (segurar para mais alto) | Espaço ou Z | A |
| *Dash* (8 direções) | Shift, X ou K | B |
| Agarrar a parede | C ou Ctrl (segurar) | RB |
| Atirar a bola (luta final) | C (segurar e soltar) | RB |
| Pausa | Esc | Start |
| Ecrã inteiro | F11 | |

## Organização

| Pasta | Conteúdo |
|---|---|
| `scripts/autoload/` | Serviços globais: sinais, estado do jogo, áudio, gravação, opções, transições |
| `scripts/core/` | Peças comuns: máquina de estados, folhas de sprites, luzes, balanço das plantas |
| `scripts/dev/` | Ferramentas de desenvolvimento (painel de depuração, capturas, sala de teste do movimento) |
| `scripts/player/` | Personagem: máquina de estados do movimento, animação, aparência |
| `scripts/world/`, `scripts/level/` | Mundo por salas, câmara, perigos, plataformas, fogueiras, leitura dos ficheiros `.room` |
| `scripts/combat/` | Projéteis, emissores, minas e avisos |
| `scripts/enemies/`, `scripts/boss/` | Inimigos e luta final |
| `scripts/ui/` | Menus, HUD, diário, ecrã final |
| `levels/ember/` | As salas do jogo, em texto (`.room`) |
| `assets/` | Sprites, fundos, temas das zonas, sons e música |
| `shaders/` | Shaders de água, balanço das plantas e paleta da personagem |
| `i18n/` | Textos do jogo em inglês e português |
| `tests/` | Testes automáticos com entrada simulada |
| `tools/` | Geradores da arte (Python), verificação das salas e scripts de validação |

## Comandos (PowerShell, na raiz do projeto)

| Comando | O que faz |
|---|---|
| `tools\validate.ps1` | Importa o projeto e corre os testes automáticos sem janela |
| `tools\build_assets.ps1` | Regenera a arte a partir dos geradores em `tools/art/` (requer Python 3 e Pillow) |
| `python tools/levels/check_reach.py levels/ember` | Confere que as fogueiras e as saídas de cada sala se alcançam |

Os scripts esperam o Godot em `..\Godot_v4.6.3-stable_win64\`.

Créditos e licenças de terceiros: [`CREDITS.md`](CREDITS.md).

## Licença

- **Código** (GDScript, shaders, programas em Python e PowerShell, testes e ficheiros das salas): licença MIT, no ficheiro [`LICENSE`](LICENSE).
- **Arte, história e personagens** (as imagens de `assets/backgrounds/`, `assets/sprites/`, `assets/tiles/` e `assets/fonts/`, os textos do jogo em `i18n/`, incluindo o diário, e as personagens Arthur, Rose, Sirius e Laelaps): [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.pt). Podem ser partilhadas e adaptadas com crédito à autora, mas não para fins comerciais.
- **Música** (`assets/audio/music/`): criada com o Suno no plano gratuito; pertence ao Suno e só pode ser usada sem fins comerciais e com crédito. Não está abrangida pelas licenças acima.
- **Efeitos sonoros** (`assets/audio/sfx/`): vêm de bancos livres, e cada um mantém a licença do seu autor, indicada em [`CREDITS.md`](CREDITS.md). Também não estão abrangidos pelas licenças acima.
