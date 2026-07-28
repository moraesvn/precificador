# Briefing — Promoções no Mercado Livre

## Objetivo

Automatizar a criação de promoções tradicionais no Mercado Livre para produtos recebidos do Tiny, usando o SKU para localizar a publicação correspondente.

## Resumo da solução

O fluxo recomendado é:

```text
SKU do Tiny → SELLER_SKU do Mercado Livre → ITEM_ID (MLB...) → promoção
```

O SKU é utilizado somente para cruzar os produtos. A API de promoções exige o `ITEM_ID` da publicação do Mercado Livre.

Na promoção tradicional, a API recebe o preço promocional final em reais (`deal_price`), e não o percentual de desconto. Caso o usuário informe uma porcentagem, o sistema deverá calcular o preço antes do envio.

## Etapas para aplicar uma promoção

### 1. Autenticar no Mercado Livre

Obter um `ACCESS_TOKEN` válido da conta vendedora e identificar o `SELLER_ID`.

### 2. Listar as publicações do vendedor

Consultar os anúncios ativos:

```http
GET /users/{SELLER_ID}/items/search?status=active
```

Para contas com mais de 1.000 anúncios, utilizar a paginação por Scan recomendada pelo Mercado Livre.

### 3. Relacionar os SKUs

Consultar os detalhes de cada publicação:

```http
GET /items/{ITEM_ID}?include_attributes=all
```

Localizar o atributo `SELLER_SKU`:

- Em `attributes`, para anúncios sem variações.
- Em `variations[].attributes`, para anúncios com variações.

Criar e manter um relacionamento local:

```text
SELLER_ID + SKU + ITEM_ID + VARIATION_ID (quando existir)
```

Antes de prosseguir, validar:

- SKUs ausentes;
- SKUs duplicados;
- diferenças de espaços, letras maiúsculas e zeros à esquerda;
- produtos do Tiny sem publicação correspondente;
- anúncios com vários SKUs dentro do mesmo `ITEM_ID`.

### 4. Criar a campanha

Criar uma campanha do vendedor:

```http
POST /seller-promotions/promotions?app_version=v2
```

Exemplo:

```json
{
  "promotion_type": "SELLER_CAMPAIGN",
  "name": "Promoção de produtos",
  "sub_type": "FLEXIBLE_PERCENTAGE",
  "start_date": "2026-07-29T00:00:00",
  "finish_date": "2026-08-05T00:00:00"
}
```

A campanha pode durar no máximo 14 dias.

### 5. Consultar os produtos elegíveis

Consultar os itens candidatos:

```http
GET /seller-promotions/promotions/{PROMOTION_ID}/items?promotion_type=SELLER_CAMPAIGN&app_version=v2
```

Somente produtos com status `candidate` devem ser adicionados.

Para ser elegível, o vendedor e o anúncio devem atender aos seguintes requisitos:

- reputação verde;
- anúncio ativo;
- produto novo;
- exposição não gratuita.

### 6. Calcular o preço promocional

A API recebe o preço final em reais:

```text
preço promocional = preço original × (1 - percentual / 100)
```

Exemplo:

```text
Preço original: R$ 100,00
Desconto: 10%
Preço enviado em deal_price: R$ 90,00
```

O sistema deve aplicar o arredondamento monetário antes do envio.

### 7. Adicionar o produto à campanha

Enviar o `ITEM_ID` e o preço promocional:

```http
POST /seller-promotions/items/{ITEM_ID}?app_version=v2
```

Exemplo:

```json
{
  "promotion_id": "C-MLB123",
  "promotion_type": "SELLER_CAMPAIGN",
  "deal_price": 90.00
}
```

O campo opcional `top_deal_price` pode definir um preço adicional para compradores elegíveis do Mercado Pontos.

### 8. Confirmar o resultado

Consultar o preço efetivamente exibido:

```http
GET /items/{ITEM_ID}/sale_price?context=channel_marketplace
```

Validar:

- `amount`: preço atual exibido;
- `regular_amount`: preço original;
- identificador e tipo da promoção.

Também é necessário registrar erros, itens rejeitados e o resultado individual de cada produto.

## Atualização e remoção

Para alterar o preço promocional:

```http
PUT /seller-promotions/items/{ITEM_ID}?app_version=v2
```

Em uma promoção ativa, o preço somente pode ser reduzido. Enquanto estiver pendente, há maior flexibilidade para alterações.

Para retirar um produto:

```http
DELETE /seller-promotions/items/{ITEM_ID}?promotion_type=SELLER_CAMPAIGN&promotion_id={PROMOTION_ID}&app_version=v2
```

## Limitação importante

A promoção é aplicada ao `ITEM_ID`, não ao `VARIATION_ID`.

Se vários SKUs do Tiny forem variações da mesma publicação, eles apontarão para o mesmo anúncio, e a promoção será aplicada à publicação inteira. A API documentada não permite promover isoladamente apenas uma variação.

## Recomendação para implantação

Realizar primeiro uma prova de conceito com poucos produtos:

1. Selecionar anúncios com e sem variações.
2. Confirmar o cruzamento por `SELLER_SKU`.
3. Criar uma campanha curta.
4. Consultar os itens candidatos.
5. Aplicar preços promocionais em poucos anúncios.
6. Confirmar os preços na API e na página do produto.
7. Validar limites de desconto e mensagens de erro.
8. Somente depois liberar o processamento em lote.

## Referências oficiais

- [Campanhas do vendedor](https://developers.mercadolivre.com.br/pt_br/realizacao-de-testes/campanhas-do-vendedor)
- [Variações e SELLER_SKU](https://developers.mercadolivre.com.br/pt_br/variacoes/variacoes)
- [Preços de produtos](https://developers.mercadolivre.com.br/en_us/price-apl)
