# Anatomia Viva 3D

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licença MIT](https://img.shields.io/badge/código-MIT-2ea44f)](LICENSE)
[![Atlas](https://img.shields.io/badge/atlas-Z--Anatomy%202026.09-b3272d)](#cobertura-anatômica)
[![Windows](https://img.shields.io/badge/Windows-instalador-0078D4?logo=windows)](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases/latest/download/AnatomiaViva3D-Windows.zip)

Atlas anatômico 3D local e interativo para estudo. Permite explorar estruturas, pesquisar em português ou latim, selecionar diretamente no corpo, isolar sistemas e consultar informações e proveniência sem depender de uma conexão durante o uso.

> [!IMPORTANT]
> Este é um recurso educacional. Não deve ser usado para diagnóstico, planejamento clínico ou como única fonte de informação médica.

## Download para Windows

[**Baixar o instalador do Anatomia Viva 3D (.zip)**](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases/latest/download/AnatomiaViva3D-Windows.zip)

Extraia o ZIP e execute `AnatomiaViva3D-Setup-<versão>.exe`. Python e a biblioteca anatômica já acompanham o instalador.

## O que há no aplicativo

- rotação, zoom, deslocamento e vistas anatômicas predefinidas;
- **2.827 malhas selecionáveis**, renderizadas de forma otimizada em um único conjunto composto;
- ossos, articulações/ligamentos/fáscias, músculos, cardiovascular, linfático, nervoso e vísceras;
- seleção pelo modelo ou pela árvore, com foco automático na estrutura;
- contexto translúcido para revelar estruturas encobertas;
- pesquisa por nome em português, termo latino, sistema e região;
- isolamento, ocultação, opacidade e filtros por sistema;
- nomes em português associados à Terminologia Anatomica 2 quando disponíveis;
- descrições, funções, classificações, regiões e lateralidade sempre exibidas em português;
- fonte, revisão, licença e identificador TA2 exibidos por estrutura;
- relatório de cobertura e verificação SHA-256 de todos os arquivos baixados;
- funcionamento offline depois da instalação;
- modelo BodyParts3D anterior preservado somente como fallback de compatibilidade.

## Cobertura anatômica

A biblioteca atual reúne **2.827 estruturas selecionáveis**, com nomes em português e latim, sínteses didáticas em português e informações sobre a origem dos dados. As definições em inglês da fonte são preservadas somente para auditoria de cobertura e não são mostradas como conteúdo de estudo. Os arquivos são versionados e verificados antes da instalação para que todos os usuários recebam a mesma biblioteca estável.

| Sistema | Malhas selecionáveis |
| --- | ---: |
| Esquelético | 277 |
| Articulações, ligamentos e fáscias | 349 |
| Muscular | 669 |
| Cardiovascular | 676 |
| Linfático | 158 |
| Nervoso | 580 |
| Órgãos e vísceras | 118 |
| **Total** | **2.827** |

Consulte [fontes e versões dos dados](docs/FONTES_E_COBERTURA.md) e [licenças de terceiros](THIRD_PARTY_LICENSES.md).

## Atualização dos dados

O instalador inclui a revisão estável. No aplicativo, use **Dados → Instalar/atualizar atlas moderno…**. O download tem aproximadamente 20 MB, é salvo no perfil do usuário e cada arquivo é validado antes da ativação. Uma falha não substitui a biblioteca válida existente.

Pelo terminal:

```bash
anatomia-dados instalar
anatomia-dados verificar
anatomia-dados status
anatomia-dados relatorio
```

O relatório resume a biblioteca instalada e confirma a integridade dos arquivos.

## Executar pelo código-fonte

Requisitos: Python 3.10 ou superior e computador com suporte a OpenGL.

### macOS ou Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-dados instalar
anatomia-3d
```

### Windows — PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
anatomia-dados instalar
anatomia-3d
```

O primeiro comando de dados baixa a revisão fixada para `data/zanatomy`. Os arquivos grandes ficam fora do histórico do Git.

## Controles

| Ação | Controle |
| --- | --- |
| Girar | arrastar com o botão esquerdo |
| Zoom | roda do mouse |
| Deslocar câmera | arrastar com o botão direito |
| Selecionar | clicar no modelo ou na lista |
| Mostrar/ocultar | caixa ao lado da estrutura |
| Restaurar contexto | **Exibir todas as estruturas** |

Ao selecionar uma estrutura, a câmera a enquadra e as demais partes ficam translúcidas. A renderização usa blocos compostos para manter seleção individual sem criar milhares de atores gráficos separados.

### Desempenho em computadores básicos

No Windows com até 12 GB de RAM, o aplicativo ativa automaticamente o **modo leve**. Ele usa um cache 3D pré-otimizado, reduz o atlas de aproximadamente 10,4 para 3,7 milhões de triângulos e desliga a suavização de tela mais cara, sem remover estruturas ou informações. O destaque de uma seleção também é feito em uma única camada, sem recalcular os 2.827 itens a cada clique.

Para forçar um perfil ao executar pelo código-fonte, defina `ANATOMIA_3D_QUALIDADE=leve` ou `ANATOMIA_3D_QUALIDADE=detalhada`. O instalador para Windows já inclui o cache leve; para prepará-lo manualmente, execute `anatomia-dados otimizar`.

## Testes

```bash
python -m pip install -e '.[dev]'
python -m pytest
```

Os testes cobrem catálogo, conteúdo didático em português, perfil para PCs com pouca memória, redução geométrica, modelos legados, atualização segura, foco de câmera, parser GLB, descompressão Draco, transformações 3D e leitura da TA2.

## Organização

```text
src/anatomia_app/
├── atlas.py             # contrato de um atlas versionado
├── zanatomy.py          # download, hashes, TA2, GLB/Draco e cobertura
├── main_window.py       # interface, seleção e renderização composta
├── catalog.py           # catálogo didático e fallback legado
├── bodyparts3d.py       # importador legado, não usado como padrão
└── geometry.py          # modo demonstrativo sem downloads

packaging/windows/       # PyInstaller, Inno Setup e build do ZIP
tools/                   # pacote de conteúdo e utilitários
tests/                   # testes automatizados
```

## Instalador do Windows

O pipeline gera:

```text
AnatomiaViva3D-Windows.zip
└── AnatomiaViva3D-Setup-<versão>.exe
```

O build baixa somente a revisão fixada, verifica hashes, executa os testes e inclui o atlas no instalador. Consulte [Instalador do Windows](docs/INSTALADOR_WINDOWS.md).

## Licenças e contribuição

O código é MIT. As malhas, a terminologia e as descrições mantêm suas próprias licenças; algumas estruturas têm restrição não comercial. Veja [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) antes de redistribuir dados.

Correções anatômicas são bem-vindas. Ao abrir uma issue, informe a estrutura, o sistema operacional, a revisão exibida em **Dados → Fonte, cobertura e licenças** e, se possível, uma captura de tela.
