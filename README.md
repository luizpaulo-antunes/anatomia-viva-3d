# Anatomia Viva 3D

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença MIT](https://img.shields.io/badge/código-MIT-2ea44f)](LICENSE)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-f59e0b)](#próximos-passos)
[![Windows](https://img.shields.io/badge/Windows-instalador%20planejado-0078D4?logo=windows)](docs/INSTALADOR_WINDOWS.md)

Um atlas anatômico 3D, local e interativo, criado para tornar o estudo de anatomia mais visual, exploratório e acessível.

O **Anatomia Viva 3D** permite navegar pelo corpo humano, pesquisar estruturas, selecionar músculos e ossos diretamente no modelo e consultar informações didáticas. O projeto é escrito em Python e utiliza PySide6, PyVista e VTK.

> [!IMPORTANT]
> Este é um projeto educacional em desenvolvimento. A geometria e os textos são materiais didáticos resumidos e não devem ser usados para diagnóstico, planejamento clínico ou como única fonte de informação médica.

## Visão do projeto

Aprender anatomia exige entender relações espaciais que nem sempre ficam claras em imagens planas. A proposta deste projeto é oferecer um ambiente em que o estudante possa observar, girar, aproximar, ocultar e isolar estruturas enquanto estuda seus nomes e funções.

O aplicativo funciona localmente e foi pensado para evoluir gradualmente com conteúdos revisados, novos sistemas anatômicos, exercícios, acompanhamento de progresso e recursos de inteligência artificial voltados ao aprendizado.

## Recursos atuais

- visualização 3D com rotação, zoom e deslocamento;
- vistas anterior, posterior, lateral e superior;
- seleção pelo modelo ou pela árvore de estruturas;
- foco automático da câmera na estrutura selecionada;
- contexto anatômico translúcido para revelar estruturas encobertas;
- pesquisa por nome em português e termo anatômico internacional;
- fichas com descrição, função, inserção e inervação, quando disponíveis;
- isolamento, ocultação e controle de opacidade;
- filtros para exibir tudo, somente ossos ou somente músculos;
- organização dos músculos por região anatômica;
- mãos e pés dentro da cobertura fornecida pelo modelo de origem;
- cache VTP otimizado para inicialização e navegação mais rápidas;
- biblioteca anatômica atualizável pelo próprio aplicativo;
- modo demonstrativo que funciona sem baixar dados externos.

## Cobertura anatômica atual

A versão atual prepara **443 estruturas selecionáveis**:

- **422 malhas musculares**;
- **21 conjuntos ósseos**, incluindo mãos, pés, patelas e cintura escapular.

Os músculos abrangem cabeça, pescoço, dorso, tórax, abdome, pelve e períneo, ombro e braço, antebraço, mão, quadril e coxa, perna e pé. Cabeças, ventres e porções fornecidas separadamente pela base podem ser estudados de forma independente.

Neste projeto, “cobertura muscular completa” significa toda a cobertura classificada como muscular e disponibilizada pelo **BodyParts3D 3.0** utilizado nesta etapa. Isso não equivale a todos os músculos descritos por todas as convenções anatômicas. A granularidade e os identificadores FMA da fonte são preservados sempre que possível.

## Instalador do Windows

O projeto já possui um fluxo automatizado para gerar:

```text
AnatomiaViva3D-Windows-<versão>.zip
└── AnatomiaViva3D-Setup-<versão>.exe
```

O instalador inclui Python, a interface, o mecanismo 3D e as 443 estruturas otimizadas. Assim, o usuário pode estudar offline sem instalar dependências ou baixar as malhas brutas.

Após a instalação, o menu **Dados → Atualizar biblioteca anatômica…** pode receber revisões de conteúdo publicadas nas [Releases do projeto](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases). O download é informado previamente, validado com SHA-256 e armazenado no perfil do usuário, preservando o conteúdo original como fallback.

Consulte [Instalador do Windows](docs/INSTALADOR_WINDOWS.md) para detalhes do build e da publicação.

## Executar pelo código-fonte

### Requisitos

- Python 3.10 ou mais recente;
- computador com suporte a OpenGL;
- Windows, macOS ou Linux.

### macOS ou Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-3d
```

### Windows — PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-3d
```

Também é possível iniciar com:

```bash
python -m anatomia_app
```

## Preparar o modelo detalhado para desenvolvimento

As malhas grandes não fazem parte do histórico do Git. Para preparar localmente o modelo BodyParts3D detalhado:

```bash
anatomia-dados instalar
anatomia-dados otimizar
anatomia-dados status
```

O processo utiliza o arquivo oficial quando disponível ou baixa as malhas necessárias do espelho público da versão 3.0. As fontes ocupam aproximadamente 1,2 GB antes da otimização e permanecem em `data/bodyparts3d`, que está ignorado pelo Git.

Consulte [Dados e licenças de terceiros](THIRD_PARTY_LICENSES.md) antes de redistribuir qualquer pacote anatômico.

## Controles

| Ação | Controle |
| --- | --- |
| Girar o modelo | Arrastar com o botão esquerdo |
| Aproximar ou afastar | Roda do mouse |
| Deslocar a câmera | Arrastar com o botão direito |
| Estudar uma estrutura | Clicar no modelo ou na lista |
| Mostrar ou ocultar | Marcar a caixa ao lado da estrutura |
| Recuperar a visão completa | Clicar em **Exibir todas as estruturas** |

Ao selecionar uma estrutura, a câmera a centraliza e aproxima automaticamente. As demais partes ficam translúcidas para preservar o contexto sem esconder o item estudado.

## Testes

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

## Organização do código

```text
src/anatomia_app/
├── catalog.py          # catálogo e informações anatômicas
├── muscle_data.py      # manifesto das malhas musculares FMA
├── geometry.py         # modelo demonstrativo
├── bodyparts3d.py      # obtenção, cache e carregamento das malhas
├── content_updates.py  # atualização segura da biblioteca anatômica
└── main_window.py      # interface e interação 3D

packaging/windows/      # PyInstaller, Inno Setup e script de build
tools/                  # geração de catálogo e pacotes de conteúdo
tests/                  # testes automatizados
```

## Próximos passos

O projeto está só começando. Entre as evoluções planejadas estão:

- ampliar ossos e adicionar órgãos, vasos e sistema nervoso;
- revisar e aprofundar as fichas anatômicas;
- criar quizzes de identificação diretamente no modelo 3D;
- registrar progresso e oferecer revisão espaçada;
- adicionar um tutor de IA contextual, ancorado em conteúdo revisado;
- melhorar acessibilidade, desempenho e experiência de instalação;
- estudar uma versão mobile com uma pilha gráfica própria para Android.

As ideias de arquitetura para mobile e IA estão registradas no [roadmap](docs/ROADMAP_MOBILE_AI.md).

## Dados, atribuição e licença

O código-fonte é disponibilizado sob a [licença MIT](LICENSE). As malhas anatômicas possuem licenças e atribuições próprias e não são automaticamente relicenciadas pela licença do código.

O modelo detalhado utiliza dados do **BodyParts3D**, mantido pelo Database Center for Life Science, e o espelho STL mantido por Kevin Mattheus Moerman. As fontes, versões e atribuições completas estão em [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Contribuindo

Sugestões, correções anatômicas, melhorias de interface e contribuições de código serão bem-vindas conforme o projeto amadurecer. Ao relatar um problema, descreva o sistema operacional, a estrutura envolvida e, se possível, inclua uma captura de tela.

Se este projeto puder ajudar alguém a compreender melhor o corpo humano, ele já estará cumprindo sua missão.
