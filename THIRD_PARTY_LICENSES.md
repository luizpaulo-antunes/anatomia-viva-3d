# Dados e licenças de terceiros

A licença MIT do código do Anatomia Viva 3D não relicencia dados anatômicos. Quem redistribuir um instalador ou pacote de conteúdo deve preservar os arquivos de licença e as atribuições abaixo.

## Z-Anatomy — atlas principal

- Projeto: https://github.com/Z-Anatomy/Models-of-human-anatomy
- Licença principal: Creative Commons Attribution-ShareAlike 4.0 International
- Revisão de terminologia: `767f14e0a4dfc55aa7c3455685b62339a4faec99`
- Exportação GLB reproduzível: https://github.com/nqwrc/3d-anatomy
- Revisão da exportação: `8ca3b7421bcfbe88b85859eb1983d5cf79f21749`

Atribuições solicitadas pela fonte:

- “BodyParts3D — The Database Center for Life Science — CC BY-SA 2.1 Japan”;
- “Z-Anatomy — The open source atlas of anatomy — CC BY-SA 4.0”.

Componentes incorporados pelo Z-Anatomy possuem termos adicionais:

- Brainder e White Matter — University of Washington;
- Cranial Nerves and Foramina — University of Dundee, CAHID — CC BY 4.0;
- Anatomy of the Inner Ear — University of Dundee School of Medicine — **CC BY-NC-SA 4.0**;
- Kidney — Lissie Cowley — **CC BY-NC 4.0**.

Consequentemente, o conjunto completo distribuído por este projeto deve ser tratado como não comercial. O aplicativo mostra a licença especial nas malhas de cóclea, vestíbulo e rim.

O texto original `License.txt` do exportador é incluído no pacote de dados e no instalador.

## Definições textuais

As definições fornecidas pelo Z-Anatomy vêm majoritariamente da Wikipédia, sob CC BY-SA 3.0 e GFDL. A URL do artigo é preservada quando consta no texto da fonte. A própria fonte alerta para possíveis erros de tradução automática. No aplicativo, esse material é identificado como descrição de referência em inglês, não como texto clínico revisado.

## Terminologia Anatomica 2

- Entidade: Federative International Programme for Anatomical Terminology (FIPAT), IFAA
- Fonte: https://ifaa.net/committees/anatomical-terminology-fipat/fipat-ifaa-terminologies/
- Edição: Terminologia Anatomica, segunda edição (TA2), publicada em 2019
- Licença declarada pela IFAA: Creative Commons Attribution-NoDerivatives 4.0

Os termos são lidos do CSV multilíngue distribuído pelo Z-Anatomy e não são alterados. A associação entre termo e malha é uma operação local do aplicativo e aparece no relatório de cobertura.

## BodyParts3D — fallback legado

### Versão 4.0

Atribuição: “BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International”.

- Fonte: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/
- Download: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Licença: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- DOI do conjunto IS-A 99%: `10.18908/lsdba.nbdc00837-007`

### Espelho da versão 3.0

- Fonte: https://github.com/Kevin-Mattheus-Moerman/BodyParts3D
- Licença: Creative Commons Attribution-ShareAlike 2.1 Japan
- Atribuição: “BodyParts3D, © The Database Center for Life Science licensed under CC Attribution-ShareAlike 2.1 Japan; STL mirror by Kevin Mattheus Moerman”.

## NIH/HuBMAP Human Reference Atlas

O HRA é documentado como fonte complementar e ainda não é empacotado nesta versão.

- Portal: https://humanatlas.io/3d-reference-library
- Repositório de releases históricas: https://github.com/hubmapconsortium/ccf-releases
- Licença dos objetos de referência: CC BY 4.0, conforme os metadados do HRA

Antes de integrar qualquer órgão do HRA, a versão futura deverá preservar o identificador da entidade, sexo do modelo, revisão, autoria, licença e espaço de coordenadas, sem sobreposição não validada com outro atlas.
