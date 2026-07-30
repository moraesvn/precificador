# Briefing — Catálogo de anúncios e promocionador

## Objetivo

Receber SKUs do Tiny, localizar todas as ofertas correspondentes no Mercado Livre e aplicar promoções nos anúncios ativos e elegíveis.

```text
SKUs do Tiny
     ↓
Catálogo local de anúncios do ML
     ↓
Validação e escolha das ofertas
     ↓
Criação da promoção
```

A origem dos SKUs no Tiny ainda será definida. O trabalho atual está concentrado na construção de um catálogo local completo e confiável do Mercado Livre.

## O que já foi validado

- O OAuth do Mercado Livre está funcionando.
- Todos os anúncios encontrados possuem `SELLER_SKU`.
- Um SKU pode estar associado a vários `ITEM_ID`s.
- O mesmo SKU pode possuir anúncios Premium, Clássicos e de catálogo.
- Anúncios de catálogo podem não aparecer no scan principal.
- O campo `item_relations` conecta o anúncio tradicional ao anúncio de catálogo.
- A relação é bidirecional e pode gerar ciclos.

Exemplo:

```text
SKU 4063
├── Tradicional Premium
│   └── Catálogo Premium relacionado
├── Outro tradicional Premium
│   └── Outro catálogo relacionado
└── Tradicional Clássico
```

## Como classificar um anúncio

### Tipo de exposição

Usar `listing_type_id` como fonte:

```text
gold_pro     → Premium
gold_special → Clássico
free         → Grátis
```

Valores desconhecidos devem ser preservados e exibidos sem conversão incorreta.

### Catálogo

Usar `catalog_listing` como fonte principal:

```text
catalog_listing = true  → anúncio de catálogo
catalog_listing = false → anúncio tradicional
```

O campo `catalog_product_id` apenas informa a associação ao produto oficial. Ele não determina sozinho que a publicação seja de catálogo.

A tag `catalog_boost` identifica anúncios de catálogo criados automaticamente pelo Mercado Livre.

## Estrutura de dados planejada

### `ml_listings`

Uma linha por `ITEM_ID`, contendo:

- identificação da empresa, vendedor e anúncio;
- título, permalink e situação;
- `listing_type_id`;
- `catalog_listing`, `catalog_product_id` e `catalog_boost`;
- `user_product_id`, `family_id` e `parent_item_id`;
- preços, moeda, estoque e vendas;
- condição, canais, tags e logística;
- datas do anúncio e da sincronização;
- origem da descoberta: scan, catálogo ou relação.

### `ml_listing_skus`

Relacionamento entre anúncio, variação e SKU:

```text
listing_id
variation_id
seller_sku
normalized_sku
```

Um anúncio poderá possuir vários SKUs quando tiver variações. Um SKU também poderá apontar para vários anúncios.

### `ml_listing_relations`

Relacionamentos encontrados em `item_relations`:

```text
source_item_id
related_item_id
related_variation_id
stock_relation
```

### `ml_sync_runs`

Histórico de cada sincronização:

- início, fim e status;
- anúncios encontrados e processados;
- quantidade por tipo;
- anúncios sem SKU;
- relações encontradas;
- erros.

## Fluxo completo da sincronização

1. Iniciar uma execução em segundo plano.
2. Buscar todos os anúncios ativos com `search_type=scan`.
3. Buscar também anúncios ativos com tag `catalog_boost`.
4. Unir e remover IDs duplicados.
5. Consultar detalhes em lotes.
6. Extrair classificação, preços, SKU e relações.
7. Adicionar à fila os IDs de `item_relations` ainda não visitados.
8. Repetir até não existirem novos IDs.
9. Persistir anúncios, SKUs e relações no PostgreSQL.
10. Inativar registros ausentes somente se a execução terminar sem erros.

O sincronizador deverá manter um conjunto de IDs visitados para impedir ciclos:

```text
Tradicional → Catálogo → Tradicional
```

## Plano de execução

### Etapa 1 — Migrações

- Adicionar Alembic ao projeto.
- Criar uma revisão-base do esquema atual.
- Marcar a revisão no PostgreSQL existente.

Status: concluída (`stamp 20260729_01`).

### Etapa 2 — Modelo normalizado

- Criar `ml_listings`.
- Criar `ml_listing_relations`.
- Adaptar `ml_listing_skus` para referenciar `ml_listings` (`listing_id` nullable).
- Ampliar os contadores de `ml_sync_runs`.

Status: models e revisão `20260729_02` criados. Aplicar com `alembic upgrade head` na VPS.

### Etapa 3 — Migração dos dados atuais

Pulada: o catálogo será preenchido do zero pela sincronização completa.

### Etapa 4 — Sincronizador completo

- Incluir busca de `catalog_boost`.
- Seguir `item_relations`.
- Classificar Premium, Clássico, catálogo e tradicional.
- Persistir todas as relações.

Status: implementado no `POST /ml/catalog-sync` (pipeline único em segundo plano).

### Etapa 5 — Consulta e conferência

- Consultar anúncios agrupados por SKU.
- Exibir tipo, catálogo, preço, estoque e relação.
- Mostrar divergências e anúncios duplicados.

Status: endpoints `GET /ml/sku-offers`, `/ml/listings`, `/ml/listing-relations` e aba Streamlit **Explorar catálogo**.

### Etapa 6 — Promocionador

- Receber SKUs do Tiny.
- Encontrar todos os MLBs ativos.
- Consultar itens candidatos à campanha.
- Calcular o preço promocional.
- Exibir prévia e solicitar confirmação.
- Aplicar a promoção em cada `ITEM_ID` elegível.
- Registrar resultados e erros individualmente.

## Operação do Alembic

Definir `DATABASE_URL` antes dos comandos.

Para o PostgreSQL existente, que já possui as tabelas atuais:

```bash
alembic stamp 20260729_01
```

Esse comando apenas registra a revisão; ele não recria nem apaga tabelas.

Para aplicar a revisão do modelo normalizado (e as próximas):

```bash
alembic upgrade head
```

Para um banco vazio do zero:

```bash
alembic upgrade head
```

Não executar `upgrade` da revisão-base sozinha no banco existente sem `stamp` prévio, pois as tabelas já foram criadas pelo sistema anterior.

## Critérios para liberar o promocionador

- Todos os anúncios ativos e de catálogo estão persistidos.
- Cada MLB possui classificação confiável.
- Relações tradicional ↔ catálogo estão completas.
- O agrupamento por SKU retorna todas as ofertas.
- Sincronizações incompletas não inativam dados válidos.
- A elegibilidade promocional é confirmada pela API antes do envio.

## Referências

- [Campanhas do vendedor](https://developers.mercadolivre.com.br/pt_br/realizacao-de-testes/campanhas-do-vendedor)
- [Tipos de publicação](https://developers.mercadolivre.com.br/pt_br/publicacao-de-produtos/tutorial-tipos-de-publicacao-y-atualizacao-de-artigos)
- [Publicar no catálogo](https://developers.mercadolivre.com.br/pt_br/busca-de-produtos-por-vendedor/publicacao-no-catalogo)
- [Variações e SELLER_SKU](https://developers.mercadolivre.com.br/pt_br/variacoes/variacoes)
