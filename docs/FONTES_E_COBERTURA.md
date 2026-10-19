# Fontes, atualidade e limites

## O que “atual” significa neste projeto

O Anatomia Viva 3D separa três coisas que frequentemente são confundidas:

1. **geometria** — a forma 3D e sua segmentação;
2. **terminologia** — o nome oficial e sua hierarquia;
3. **conteúdo didático** — descrição, função e relações.

Uma revisão recente do arquivo não prova que toda geometria foi produzida recentemente. Por isso o aplicativo registra tanto a revisão utilizada quanto a proveniência histórica da malha.

## Fontes adotadas

### Z-Anatomy

É o atlas local principal por reunir sete sistemas no mesmo espaço de coordenadas, estruturas bilaterais e nomes multilíngues. A exportação usada foi produzida em 21/09/2026 e está fixada pelo commit `8ca3b7421bcfbe88b85859eb1983d5cf79f21749`. A terminologia vem do commit `767f14e0a4dfc55aa7c3455685b62339a4faec99`, de 18/10/2026.

O próprio projeto Z-Anatomy declara que parte das malhas deriva do BodyParts3D, que as definições dependem fortemente da Wikipédia e que ainda há estruturas ausentes e validação final pendente. O Anatomia Viva 3D mantém essas ressalvas visíveis.

As definições textuais em inglês da fonte não são apresentadas ao estudante. A interface gera para cada item uma síntese em português baseada no sistema, na classe anatômica, na região, na lateralidade e, quando identificável pelo nome, na ação ou função específica. O texto informa sua natureza didática e não inventa origem, inserção ou inervação quando esses dados não estão disponíveis na fonte.

### Terminologia Anatomica 2 (TA2)

A TA2 é o padrão internacional da IFAA/FIPAT para anatomia humana adulta. Foi publicada em 2019 e é mantida continuamente. O CSV multilíngue é usado sem alterar os termos; o pareamento com nomes das malhas é auditado.

### NIH/HuBMAP Human Reference Atlas

O HRA é uma fonte complementar importante para órgãos de referência, ontologias e validação por especialistas. Seus órgãos masculinos e femininos não são sobrepostos automaticamente ao Z-Anatomy porque foram produzidos em outros espaços de coordenadas e para outras finalidades. Misturá-los sem registro anatômico criaria uma aparência convincente, porém cientificamente incorreta. A arquitetura `AtlasModel` permite acrescentá-los futuramente como atlas selecionável e versionado.

### BodyParts3D

Permanece disponível apenas como fallback legado. Não é mais o atlas padrão. Ele é útil para compatibilidade e comparação histórica, mas a própria documentação da fonte informa que nem todo conceito anatômico tem uma malha correspondente.

## Auditoria reproduzível

Execute:

```bash
anatomia-dados verificar
anatomia-dados relatorio
```

`verificar` recalcula SHA-256. `relatorio` lê os sete GLBs e a TA2 e informa:

- contagem por sistema;
- percentual de associação exata à TA2;
- disponibilidade de descrições;
- nomes não associados;
- rótulos questionáveis da fonte;
- limitações conhecidas.

## Limites desta revisão

- o modelo principal representa anatomia masculina;
- não representa variações anatômicas populacionais e individuais;
- “estrutura selecionável” não equivale a “órgão” ou “músculo único”;
- descrições da fonte estão majoritariamente em inglês, são usadas apenas na auditoria de cobertura e não constituem revisão clínica;
- parte da geometria possui origem histórica anterior à revisão do repositório;
- modelos de fontes diferentes não são combinados sem transformação e validação espacial.

O objetivo não é afirmar uma perfeição inexistente. É oferecer o atlas aberto mais amplo e recente compatível com o aplicativo, tornar cada decisão auditável e permitir substituir ou complementar fontes sem reescrever a interface.
