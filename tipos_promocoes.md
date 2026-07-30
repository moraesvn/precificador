# Tipos de promoções — API Mercado Livre (Brasil / MLB)

Documento de referência para avaliar quais tipos de promoção o precificador deve suportar.

## Fontes oficiais

**Fonte hub (Brasil):** [Gerenciar promoções](https://developers.mercadolivre.com.br/pt_br/gerenciar-ofertas)  

No menu da Central de promoções do portal BR aparecem também as páginas filhas por tipo (tradicionais, co-participação, DOD, LIGHTNING, cupons, PIX, etc.).

### Docs Brasil (por tipo)

| Tipo | Documentação BR |
|------|-----------------|
| Hub / visão geral | [Gerenciar promoções](https://developers.mercadolivre.com.br/pt_br/gerenciar-ofertas) |
| `DEAL` | [Campanhas tradicionais](https://developers.mercadolivre.com.br/pt_br/campanhas-tradicionais) |
| `SMART` / `PRICE_MATCHING` / `PRICE_MATCHING_MELI_ALL` | [Co-participação e preços competitivos](https://developers.mercadolivre.com.br/pt_br/gerenciamento-perguntas-respostas/campanhas-smart-price-matching) |
| `DOD` | [Ofertas do dia](https://developers.mercadolivre.com.br/pt_br/ofertas-do-dia) |
| `LIGHTNING` | [Ofertas relâmpago](https://developers.mercadolivre.com.br/pt_br/ofertas-relampago) |
| `VOLUME` | [Desconto por quantidade](https://developers.mercadolivre.com.br/pt_br/campanhas-de-desconto-por-quantidade) |
| `PRE_NEGOTIATED` / `UNHEALTHY_STOCK` | [Pré-acordado e liquidação Full](https://developers.mercadolivre.com.br/desconto-pre-acordado-por-item) |
| `SELLER_CAMPAIGN` | [Campanhas do vendedor](https://developers.mercadolivre.com.br/pt_br/realizacao-de-testes/campanhas-do-vendedor) |
| `SELLER_COUPON_CAMPAIGN` | [Cupons do vendedor](https://developers.mercadolivre.com.br/pt_br/descricao-de-produtos/cupons-do-vendedor) |
| `BANK` (`COFINANCED` / PIX) | [Campanha co-participação para PIX](https://developers.mercadolivre.com.br/pt_br/campanha-co-participacao-para-pix) |

`MARKETPLACE_CAMPAIGN` e `PRICE_DISCOUNT` estão listados no hub e nos valores possíveis da API; no menu BR aparecem como “Campanha com co-participação” e “Desconto individual”.

**Observação:** a tabela “Características das promoções” do hub lista 10 linhas e **não** inclui `PRICE_DISCOUNT`, `SELLER_COUPON_CAMPAIGN`, `PRICE_MATCHING_MELI_ALL` nem `BANK` (PIX) — esses tipos aparecem no texto introdutório, nas enums da API ou em páginas filhas.

---

## 1. Visão geral

Todos os tipos passam pelo mesmo recurso da API:

```text
/seller-promotions
```

Há **14 tipos** relevantes (incluindo `PRICE_MATCHING_MELI_ALL` e `BANK` / PIX, documentados no BR). A diferença principal entre eles é:

1. **Quem cria** a campanha (você ou o Mercado Livre)
2. **Quem paga** o desconto (só você, ou você + ML)
3. **Como se define o preço** (você escolhe, ou você só aceita)
4. **Regras extras** (estoque, prazo, aprovação, país)

---

## 2. Comparativo completo

| Nome | Código API | Quem cria | Preço | Bônus MELI | Estoque | Deadline | Aprovação |
|------|------------|-----------|-------|------------|---------|----------|-----------|
| Tradicional | `DEAL` | ML (convite) | Você define | Não | Não | Sim | Sim |
| Co-financiada | `MARKETPLACE_CAMPAIGN` | ML (convite) | Você aceita | Sim | Não | Sim | Não |
| Co-financiada automática | `SMART` | ML (automático) | Você aceita | Sim | Não | Sim | Não |
| Preço competitivo | `PRICE_MATCHING` | ML | Você aceita | Sim | Não | Sim | Não |
| Preço competitivo 100% ML | `PRICE_MATCHING_MELI_ALL` | ML (automático) | Automático | Sim (100% ML) | Não | Sim | Não |
| Desconto individual | `PRICE_DISCOUNT` | ML / por item | Você define | Varia | Não | — | Não |
| Oferta do dia | `DOD` | ML (convite) | Você define | Não | Informativo | Não | Não |
| Oferta relâmpago | `LIGHTNING` | ML (convite) | Você define | Não | **Obrigatório** | Não | Não |
| Desconto por volume | `VOLUME` | ML ou seller | Aceita / regras | Sim (convite) | Não | Sim | Não |
| Pré-acordado | `PRE_NEGOTIATED` | Comercial ML | Acordo + aceita | Sim | Sim | Sim | Não |
| Liquidação Full | `UNHEALTHY_STOCK` | ML | Acordo + aceita | Sim | Sim | Sim | Não |
| Campanha do vendedor | `SELLER_CAMPAIGN` | **Você** | Você define | Não | Não | Sim | Não |
| Cupom do vendedor | `SELLER_COUPON_CAMPAIGN` | **Você** | % ou valor fixo | Não | Não | — | Não |
| Co-participação PIX | `BANK` (`sub_type`: `COFINANCED`) | ML (convite) | Você aceita | Sim | Não | Sim | Não |

---

## 3. Quem controla a campanha?

### Você cria sozinho

| Tipo | Quando faz sentido |
|------|--------------------|
| `SELLER_CAMPAIGN` | Quer criar promoção própria com datas e preço por item |
| `SELLER_COUPON_CAMPAIGN` | Quer cupom (% ou R$) no carrinho (só Brasil / MLB) |
| `VOLUME` (criação pelo seller) | Quer “leve 3 pague 2”, % na 2ª unidade, etc. |

### Mercado Livre convida / você adere

| Tipo | Quando faz sentido |
|------|--------------------|
| `DEAL` | Campanhas grandes (ex.: Hot Sale); você define o preço promocional |
| `MARKETPLACE_CAMPAIGN` | ML banca parte do desconto; você aceita a oferta |
| `SMART` | Igual co-financiada, mas seleção automática de itens |
| `PRICE_MATCHING` | Alinhar preço com a concorrência (ML ajuda no desconto) |
| `PRICE_MATCHING_MELI_ALL` | Mesmo objetivo; ML paga 100% e ativa sozinho |
| `PRICE_DISCOUNT` | Desconto individual sugerido/elegível no item |
| `DOD` | Destaque por ~24 horas |
| `LIGHTNING` | Oferta curta com estoque reservado |
| `PRE_NEGOTIATED` | Desconto já negociado com o comercial do ML |
| `UNHEALTHY_STOCK` | Liquidar estoque Full parado |
| `VOLUME` (convite) | Campanha de quantidade organizada pelo ML |
| `BANK` (PIX) | Desconto no pagamento via PIX; ML + seller cofinanciam |

```text
Controle total do seller
  └── SELLER_CAMPAIGN
  └── SELLER_COUPON_CAMPAIGN

Convite do ML → adesão
  └── DEAL
  └── MARKETPLACE_CAMPAIGN / SMART / PRICE_MATCHING / PRICE_MATCHING_MELI_ALL
  └── DOD / LIGHTNING / PRICE_DISCOUNT
  └── PRE_NEGOTIATED / UNHEALTHY_STOCK / VOLUME
  └── BANK (PIX / COFINANCED)
```

---

## 4. Quem paga o desconto?

### Sem bônus do Mercado Livre (custo do seller)

- `DEAL`
- `DOD`
- `LIGHTNING`
- `SELLER_CAMPAIGN`
- `SELLER_COUPON_CAMPAIGN`

### Com bônus / co-funding do Mercado Livre

- `MARKETPLACE_CAMPAIGN`
- `SMART`
- `PRICE_MATCHING`
- `PRICE_MATCHING_MELI_ALL` (100% ML; `seller_percentage` = 0)
- `VOLUME` (quando for convite)
- `PRE_NEGOTIATED`
- `UNHEALTHY_STOCK`
- `BANK` (PIX — cofinanciado; campos `meli_percentage` / `seller_percentage`)

Na co-financiada, a API costuma trazer algo como:

- `meli_percent` — parte do desconto paga pelo ML
- `seller_percent` — parte do desconto paga pelo seller

**Boost automático:** em alguns tipos o ML pode aplicar desconto extra (`boosted_offer`), compensado em custo de venda. Documentado para: `DEAL`, `PRICE_DISCOUNT`, `PRE_NEGOTIATED`, `SMART`, `PRICE_MATCHING`, `LIGHTNING`.

---

## 5. Como entra o item na API?

### A) Você define o preço (`deal_price`)

| Tipo | Payload típico |
|------|----------------|
| `DEAL` | `deal_price` + `promotion_id` + `promotion_type` (+ `top_deal_price` opcional) |
| `DOD` | `deal_price` + `promotion_type` |
| `SELLER_CAMPAIGN` | `deal_price` + `promotion_id` + `promotion_type` (+ `top_deal_price` opcional) |
| `PRICE_DISCOUNT` | `deal_price` + datas / regras do tipo |

### B) Você define preço **e** estoque

| Tipo | Payload típico |
|------|----------------|
| `LIGHTNING` | `deal_price` + `stock` + `promotion_type` |

Quando o estoque reservado acaba, a oferta encerra sozinha.

### C) Você aceita uma oferta pronta

| Tipo | Payload típico |
|------|----------------|
| `MARKETPLACE_CAMPAIGN` | `promotion_id` + `offer_id` + `promotion_type` |
| `SMART` | idem |
| `PRICE_MATCHING` | idem |
| `VOLUME` (convite) | idem |
| `BANK` (PIX) | `promotion_id` + `offer_id` + `promotion_type: BANK` |

`PRICE_MATCHING_MELI_ALL` **não exige adesão**: o ML ativa sozinho (não há status `candidate`).

### D) Você aceita um acordo comercial

| Tipo | Payload típico |
|------|----------------|
| `PRE_NEGOTIATED` | `offer_id` + `promotion_id` + `promotion_type` |
| `UNHEALTHY_STOCK` | idem (só itens Full) |

---

## 6. Detalhe por tipo (didático)

### `DEAL` — Campanha tradicional

- Campanha organizada pelo ML (convite).
- Você **define** o preço promocional.
- Existe faixa de preço crível: `min_discounted_price`, `max_discounted_price`, `suggested_discounted_price`.
- Fora da faixa → erro `ERROR_CREDIBILITY_DISCOUNTED_PRICE`.
- Tem deadline e aprovação.
- Opcional: `top_deal_price` (Mercado Pontos 3–6).

Doc BR: [Campanhas tradicionais](https://developers.mercadolivre.com.br/pt_br/campanhas-tradicionais).

**Endpoint de candidatos:**

```http
GET /seller-promotions/promotions/{PROMOTION_ID}/items?promotion_type=DEAL&app_version=v2
```

Status do item: `candidate` | `pending` | `started` | `finished`.

---

### `MARKETPLACE_CAMPAIGN` — Co-financiada

- ML convida e **paga parte** do desconto.
- Você **aceita** a condição (não inventa o preço livremente).
- Bom para melhorar margem do desconto com ajuda do marketplace.

---

### `SMART` — Co-financiada automática

- Parecida com `MARKETPLACE_CAMPAIGN`.
- Seleção de itens mais automatizada.
- Também tem co-funding.
- Duração máxima típica: até **30 dias**.
- Adesão com `offer_id`.
- Dá para colocar seller/item em **lista de exclusão** de campanhas automáticas.

Doc BR: [Co-participação e preços competitivos](https://developers.mercadolivre.com.br/pt_br/gerenciamento-perguntas-respostas/campanhas-smart-price-matching).

---

### `PRICE_MATCHING` — Preço competitivo

- Objetivo: ficar competitivo frente a outros sites/marketplaces.
- ML ajuda no desconto (cofinanciado com o seller).
- Candidatos podem mudar **diariamente**.
- Duração máxima típica: até **10 dias**.
- Adesão com `offer_id`.

Doc BR: [Co-participação e preços competitivos](https://developers.mercadolivre.com.br/pt_br/gerenciamento-perguntas-respostas/campanhas-smart-price-matching).

---

### `PRICE_MATCHING_MELI_ALL` — Preço competitivo 100% Mercado Livre

- Mesmo objetivo do `PRICE_MATCHING`.
- Desconto **100% financiado pelo ML** (`seller_percentage` = 0).
- Participação **automática** — sem ação do seller para aderir.
- **Não** aparece status `candidate`; quando a campanha é listada, os itens já tendem a estar `started`.
- Ainda é possível **remover** via DELETE (com `offer_id`), se quiser sair.

Doc BR: mesma página de SMART / PRICE_MATCHING.

---

### `PRICE_DISCOUNT` — Desconto individual

- Desconto por item (não necessariamente dentro de uma “campanha nomeada” grande).
- Você define preço; há sugestão de faixa.
- Pode ter boost.

---

### `DOD` — Oferta do dia

- Destaque por cerca de 24 horas.
- Você define `deal_price`.
- Stock é **informativo** (não reserva).
- Depois de ativada, em geral **não remove** — só pausar o anúncio.

---

### `LIGHTNING` — Oferta relâmpago

- Curta duração.
- Você define `deal_price` **e** `stock` reservado (**obrigatório**).
- Acabou o stock → promoção encerra.
- Depois de ativada, regra similar à DOD: compromisso de manter; senão, pausar item.

---

### `VOLUME` — Desconto por quantidade

Subtipos comuns:

| Subtipo | Significado | Exemplo |
|---------|-------------|---------|
| `BNGM` | Buy N Get M | Leve 9, pague 3 |
| `BNSP` | Buy N Save P% | 50% off comprando 2 |
| `SPONTH` | Save P% on the Nth | 50% na 2ª unidade |

Pode permitir combinação de itens (`allow_combination`).

---

### `PRE_NEGOTIATED` — Pré-acordado

- Negociado com o comercial do ML.
- Preço, desconto e benefício já definidos.
- Adesão via `offer_id`.

---

### `UNHEALTHY_STOCK` — Liquidação Full

- Mesma lógica do pré-acordado.
- Exclusivo para itens em **Full** (estoque parado / liquidação).

---

### `SELLER_CAMPAIGN` — Campanha do vendedor

- **Você cria** a campanha.
- Duração máxima: **14 dias**.
- Subtipo atual: `FLEXIBLE_PERCENTAGE` (percentual por item).
- Requisitos típicos do item:
  - reputação verde (conta)
  - item **ativo**
  - condição **novo**
  - exposição **não gratuita** (`listing_type` free não entra)
- Você define `deal_price` por item.

Útil como primeiro tipo a implementar no precificador (controle total).

---

### `SELLER_COUPON_CAMPAIGN` — Cupom do vendedor

- Você cria cupom.
- Desconto no **valor da venda**, acumulativo com promoção ativa.
- Só **1 cupom por venda**.
- Disponível **somente em MLB** (Brasil).
- Subtipos: `FIXED_PERCENTAGE` ou `FIXED_AMOUNT`.
- Pode ter código (`partial_coupon_code`) ou ser aberto a quem vê o anúncio.
- Duração máxima típica: **31 dias**.

---

### `BANK` — Co-participação para PIX

- Desconto aplicado a pagamentos com **PIX**.
- Cofinanciado entre MELI e o vendedor (convite).
- Disponível **somente em MLB**.
- Na API: `type: BANK`, `sub_type: COFINANCED`, `payment_method: PIX`.
- Você **aceita** a oferta candidata (`offer_id`); não define `deal_price` livremente.
- Resposta de itens traz `meli_percentage` e `seller_percentage`.
- **Não dá para alterar o preço do item enquanto ele está na campanha.** Fluxo: remover → alterar preço → incluir de novo.
- Remoção de oferta pendente ou ativa via DELETE com `promotion_type=BANK`, `promotion_id` e `offer_id`.

Doc BR: [Campanha co-participação para PIX](https://developers.mercadolivre.com.br/pt_br/campanha-co-participacao-para-pix).

---

## 7. Endpoints úteis (todos os tipos)

### Listar promoções do vendedor

```http
GET /seller-promotions/users/{USER_ID}?app_version=v2
```

### Detalhe de uma promoção

```http
GET /seller-promotions/promotions/{PROMOTION_ID}?promotion_type={TIPO}&app_version=v2
```

### Itens de uma promoção (candidatos / ativos)

```http
GET /seller-promotions/promotions/{PROMOTION_ID}/items?promotion_type={TIPO}&app_version=v2
```

Filtros úteis:

- `status=candidate|pending|started`
- `item_id=MLB...`
- `status_item=active|paused`

### Promoções de um item específico

```http
GET /seller-promotions/items/{ITEM_ID}?app_version=v2
```

### Incluir item

```http
POST /seller-promotions/items/{ITEM_ID}?app_version=v2
```

### Remover item / oferta

```http
DELETE /seller-promotions/items/{ITEM_ID}?promotion_type={TIPO}&promotion_id={ID}&app_version=v2
```

---

## 8. Status comuns do item na campanha

| Status | Significado |
|--------|-------------|
| `candidate` | Elegível; ainda não aderiu |
| `pending` | Já incluído; campanha ainda não começou |
| `started` | Ativo na promoção |
| `finished` | Removido / encerrado |

Regra prática: **só promocione o que estiver `candidate`** (ou já em `pending`/`started`, se for gestão).

Exceção: em `PRICE_MATCHING_MELI_ALL` não há `candidate` — o ML ativa automaticamente.

A promoção aplica-se ao **`ITEM_ID`**, não ao SKU e não à variação isolada.

---

## 9. Disponibilidade (MLB / Brasil)

Para o site Brasil (`MLB`), a documentação indica disponibilidade ampla dos tipos principais.

Destaques:

- `SELLER_COUPON_CAMPAIGN` → **somente MLB**
- `BANK` (PIX / `COFINANCED`) → **somente MLB**
- `PRICE_MATCHING_MELI_ALL` → documentado no portal BR com exemplos `P-MLB...`
- Endpoints usam sempre `https://api.mercadolibre.com` (não há API “.com.br” separada para promoções)

A tabela hub (UY e outros) lista MLB no grupo com MLA, MLM, MCO, MLC, MLU, MPE para a maioria dos tipos.

---

## 10. Sugestão de prioridade para o precificador

Ordem sugerida para avaliar e implementar depois:

| Prioridade | Tipo | Motivo |
|------------|------|--------|
| 1 | `SELLER_CAMPAIGN` | Controle total: criar, definir preço, datas |
| 2 | `DEAL` | Adesão a campanhas ML com preço definido por você |
| 3 | `MARKETPLACE_CAMPAIGN` / `SMART` | Aproveitar co-funding (aceitar oferta) |
| 4 | `DOD` / `LIGHTNING` | Pontuais; regras de stock e duração curta |
| 5 | `SELLER_COUPON_CAMPAIGN` | Cupom no carrinho (MLB) |
| 6 | Demais | Conforme necessidade comercial |

---

## 11. Checklist de avaliação

Use este checklist ao decidir o que entra no produto:

- [ ] Precisamos **criar** promoção (`SELLER_CAMPAIGN`) ou só **aderir** a convites (`DEAL`, etc.)?
- [ ] Queremos usar **co-funding** do ML?
- [ ] Vamos promocionar **Premium, Clássico e Catálogo** (cada um = `ITEM_ID` separado)?
- [ ] Precisamos de oferta com **estoque reservado** (`LIGHTNING`)?
- [ ] Cupom de carrinho faz sentido (`SELLER_COUPON_CAMPAIGN`)?
- [ ] Desconto no PIX (`BANK`) entra no escopo?
- [ ] Como validar elegibilidade: lista de `candidate` da campanha?
- [ ] Como calcular / validar `deal_price` dentro de min/max/suggested?

---

## 12. Resumo em uma frase

| Tipo | Em uma frase |
|------|--------------|
| `DEAL` | Campanha do ML; você escolhe o preço dentro da faixa |
| `MARKETPLACE_CAMPAIGN` | ML ajuda a pagar o desconto; você aceita |
| `SMART` | Co-financiada automática |
| `PRICE_MATCHING` | Desconto para ficar competitivo; ML ajuda |
| `PRICE_MATCHING_MELI_ALL` | Competitivo 100% pago pelo ML; adesão automática |
| `PRICE_DISCOUNT` | Desconto individual no item |
| `DOD` | Oferta do dia (~24h) |
| `LIGHTNING` | Oferta relâmpago com estoque reservado |
| `VOLUME` | Desconto por quantidade (3x2, % na 2ª, etc.) |
| `PRE_NEGOTIATED` | Desconto negociado com o comercial |
| `UNHEALTHY_STOCK` | Liquidação de estoque Full |
| `SELLER_CAMPAIGN` | Você cria a campanha e define o preço |
| `SELLER_COUPON_CAMPAIGN` | Você cria cupom (só Brasil) |
| `BANK` | Desconto no PIX cofinanciado (só Brasil) |
