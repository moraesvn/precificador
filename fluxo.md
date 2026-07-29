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

### Informações sugeridas para a tabela

```text
company_code
seller_id
seller_sku
item_id
variation_id (opcional)
title
status
last_synced_at
```

O valor original do SKU deve ser preservado para auditoria. O sistema também poderá manter uma versão normalizada para facilitar o cruzamento, removendo espaços nas extremidades e tratando diferenças de letras maiúsculas e minúsculas.

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