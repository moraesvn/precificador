É um desenho inicial de como o produto vai funcionar. Podendo ser testado no próprio streamlit, e depois que for criado um design system ideal, desenvolver um frontend definitivo. Caso alguma funcionalidade do desenho não fique ideal para usar no streamlit, não tem problema pois o streamlit é apenas o ambiente de teste local. O foco é o produto ser consistente para o ambiente de produção.

Para promoção, anuncio precisa estar ativo. Estoque Tiny > 0 reativa no ML automaticamente; o sistema não reativa no POST da promoção — só avisa se estiver inativo.

Decisões do MVP:
- Streamlit de produto: `tools/streamlit/promocionar_app.py` (separado do `app.py` de exploração).
- Persistência de configs no Postgres.
- Tipos usáveis no fluxo: `SELLER_CAMPAIGN` e `DEAL` (demais listados/desligados).
- Preço-base configurável: Tiny (padrão) ou ML; + ajuste global; % por exposição/catálogo.

**Sidebar:**
- Um seletor SP/SC

- Aba Dashboard - A definir

- Aba Promocionar:
Seletor de marketplace:
Mercado livre: A partir daqui, começaria o fluxo de promocionar:
- Selecionar o tipo de promoção (que estiverem ativas nas configurações)
- itens vindo do tiny (exibir preço base do tiny)
- encontrar os MLBs (exibir preços, exposição, catálogo, status)
- Dependendo do tipo de promoção, consultar se é candidato.
- Calculo do preço promocional (com as regras de % definidas nas configs)
- Exibir prévia e solicitar confirmação.
- Aplicar a promoção em cada `ITEM_ID` elegível.
- Registrar resultados e erros individualmente.

- Aba configurações:
Promoções: lista resumida dos tipos (`tipos_promocoes.md`), ativar/desativar, % por eixo.
Marketplaces: Mercado Livre (futuro: cadastrar/autenticar outro).
Regras gerais (por marketplace): fonte preço-base Tiny/ML + ajuste global (% ou R$).
