# Instalador do Windows

O pacote final é publicado como `AnatomiaViva3D-Windows.zip`, com uma cópia versionada `AnatomiaViva3D-Windows-<versão>.zip`. Dentro dele há um único instalador `AnatomiaViva3D-Setup-<versão>.exe`.

Download permanente da versão mais recente: [AnatomiaViva3D-Windows.zip](https://github.com/luizpaulo-antunes/anatomia-viva-3d/releases/latest/download/AnatomiaViva3D-Windows.zip).

O Setup instala por usuário, sem exigir privilégios de administrador, cria atalhos e registra um desinstalador. Python, PySide6, PyVista, VTK e DracoPy são incluídos pelo PyInstaller. Os sete sistemas do atlas Z-Anatomy, com 2.827 malhas, também são incluídos; o uso normal funciona offline.

## Atualizações após a instalação

O menu **Dados → Instalar/atualizar atlas moderno…** instala a revisão compatível fixada pela versão do aplicativo. O programa:

1. informa a revisão, o número de estruturas e o tamanho;
2. baixa os GLBs, a TA2, o léxico, as definições e a licença das revisões fixadas;
3. confere tamanho e SHA-256 de cada arquivo;
4. gera a auditoria de cobertura;
5. ativa os dados no perfil do usuário e preserva os dados embutidos como fallback.

No Windows, os pacotes ficam em `%LOCALAPPDATA%\AnatomiaViva3D\zanatomy`. Uma nova revisão de fonte é publicada com uma nova versão do aplicativo, permitindo testar nomes, contagem, hashes e compatibilidade antes da ativação.

## Build automático no GitHub

Depois que o código for enviado ao GitHub, abra **Actions → Build Windows installer → Run workflow**. O ZIP ficará disponível como Artifact.

Ao criar e enviar uma tag como `v0.4.0`, o mesmo workflow cria ou atualiza uma GitHub Release e anexa o ZIP automaticamente.

## Build em um computador Windows

Requisitos:

- Python 3.12 de 64 bits;
- Inno Setup 6 ou 7;
- PowerShell 5.1 ou mais recente;
- conexão à internet na primeira montagem do atlas.

No PowerShell, na raiz do projeto:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\packaging\windows\build.ps1
```

O script instala as dependências, executa os testes, baixa e valida o atlas, gera o aplicativo autocontido, compila o Setup e cria em `release\`:

- `AnatomiaViva3D-Windows-<versão>.zip`;
- `AnatomiaViva3D-Windows.zip`, usado pelo link permanente do README;
- `AnatomiaViva3D-Content-<versão>.zip`;
- `anatomia-content.json`.

## Publicação

Os ZIPs e o manifesto devem ser publicados em **GitHub Releases**, não commitados no histórico do Git. `dist/`, `build/` e `release/` são produtos reproduzíveis e permanecem ignorados.
