# Fluxo do sistema para criar promoções

## Objetivo

Usar os SKUs vindos do Tiny para localizar os anúncios correspondentes no Mercado Livre e aplicar promoções.

A origem exata dos itens no Tiny ainda será definida. Por enquanto, o desenvolvimento começará pela criação de uma tabela auxiliar com os anúncios do Mercado Livre.

## Etapa atual — catálogo auxiliar do Mercado Livre

O Mercado Livre aplica a promoção pelo `ITEM_ID` do anúncio, no formato `MLB...`, e não diretamente pelo SKU. Além disso, não existe uma busca direta de anúncios por `SELLER_SKU`.

Por isso, será mantido um relacionamento local:

```text
SELLER_SKU → ITEM_ID (MLB...) → VARIATION_ID (quando existir)
```

### Sincronização dos anúncios

1. Listar os anúncios ativos do vendedor no Mercado Livre.
2. Consultar o detalhe de cada anúncio com `include_attributes=all`.
3. Localizar o atributo `SELLER_SKU` no anúncio ou em suas variações.
4. Salvar ou atualizar o relacionamento na tabela auxiliar.
5. Identificar anúncios sem SKU, SKUs duplicados e anúncios inativos.

### Persistência

```text
ml_listings           → uma linha por ITEM_ID (classificação, preços, catálogo)
ml_listing_skus       → relacionamento SKU × anúncio/variação (listing_id → ml_listings)
ml_listing_relations  → relações tradicional ↔ catálogo (item_relations)
ml_sync_runs          → andamento, contagens por tipo, relações e erros
```

O sincronizador atual ainda grava só em `ml_listing_skus`. O preenchimento completo de `ml_listings` e `ml_listing_relations` entra na próxima etapa.

O valor original do SKU é preservado em `seller_sku`. Uma versão normalizada em `normalized_sku` remove espaços nas extremidades e trata diferenças entre letras maiúsculas e minúsculas.

### Execução da sincronização

1. `POST /ml/catalog-sync` inicia o processo em segundo plano.
2. O scan percorre todos os anúncios ativos, sem limite total.
3. Os detalhes são consultados em lotes de até 20 anúncios.
4. O `status` retornado no detalhe confirma se o anúncio continua ativo.
5. Os SKUs do anúncio e das variações são gravados no PostgreSQL.
6. Registros não encontrados são inativados somente quando a execução termina sem erros.
7. `GET /ml/catalog-sync/{run_id}` informa o andamento da execução.
8. `GET /ml/sku-map` permite consultar o relacionamento persistido.

Enquanto a sincronização estiver em andamento, a tabela é preenchida gradualmente. Uma falha parcial não inativa registros antigos, evitando perda incorreta do relacionamento.

## Fluxo futuro com o Tiny

Quando a origem dos itens no Tiny for definida:

1. Receber os SKUs selecionados ou obtidos no Tiny.
2. Consultar os SKUs na tabela auxiliar do Mercado Livre.
3. Caso algum SKU não seja encontrado, atualizar a sincronização do ML e tentar novamente.
4. Validar se o anúncio está ativo e elegível para promoção.
5. Consultar o preço atual.
6. Calcular e apresentar o preço promocional para confirmação.
7. Criar ou selecionar uma campanha.
8. Enviar a promoção utilizando o `ITEM_ID`.
9. Registrar o resultado individual de cada produto.

```text
Itens do Tiny
     ↓
SKUs
     ↓
Tabela auxiliar SKU × MLB
     ↓
Validação e cálculo do preço
     ↓
Confirmação
     ↓
Promoção no Mercado Livre
```

## Regra importante sobre variações

A promoção é aplicada ao `ITEM_ID`, e não ao `VARIATION_ID`.

Se dois ou mais SKUs forem variações do mesmo anúncio, eles apontarão para o mesmo `ITEM_ID` e deverão ser agrupados. O preço promocional será aplicado ao anúncio inteiro e deverá ser compatível entre suas variações.