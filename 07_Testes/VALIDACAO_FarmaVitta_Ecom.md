# Validação: FarmaVitta E-commerce Intelligence (PBIP)

Projeto: `04_PBIP\FarmaVitta_Ecom.pbip` · Gerador: `10_Scripts\pbip\build_ecom.py` (estende os scripts da v2) · Dados: `01_Dados_Originais\base_complementar_ecommerce\` (seed 20261023, sem alterações)

## Resumo

| Item | Valor |
|---|---|
| Tabelas / relações | 24 / 37 (todas 1:*, direção única, sem relação fato–fato) |
| Medidas | 365 (124 da v2 foram podadas por dependerem de estoque, compras ou forecast) |
| Páginas / visuais / bookmarks | 7 + tooltip / 175 / 12 |
| Visuais personalizados | HTML Content (cards, narrativas, chips, alertas) e Deneb (7 specs em `04_PBIP\Deneb_Ecom`) |

## GATE A: auditoria da base (script `10_Scripts\04_auditoria_gate_a_ecom.py`)

| KPI de referência | Calculado | Status |
|---|---|---|
| Vendas digitais | 40.029 | PASS |
| Receita digital | R$ 9.774.295,05 | PASS |
| OTIF | 87,76% | PASS |
| Sessões / conversão | 1.274.133 / 3,14% | PASS |
| Nota média | 3,98 | PASS |
| NPS / CSAT | +5,93 / 4,405 | PASS |
| Custo digital | R$ 1.736.490,06 | PASS |
| Pedidos em sessões = vendas por dia × loja × canal | 0 divergências | PASS |
| Chaves únicas e integridade referencial (todas as fatos) | sim | PASS |

**Defeitos encontrados na fonte (FAIL, documentados e tratados, CSV não foi alterado):**

1. **Funil invertido:** add to cart (159.850) < checkout (249.757) em 69% das linhas e em todos os 24 meses. *Tratamento:* o funil usa Sessões → Checkout → Pedido. Add to cart aparece só como taxa isolada, com alerta na página. "Abandono de carrinho" foi substituído por "abandono de checkout".
2. **Notas só 3 e 4:** são 13.053 notas 4 e 271 notas 3, e **todas as notas 3 estão em Perfumaria**. *Tratamento:* o sinal relativo é o "% abaixo de 4", com alerta. Não dá para afirmar "baixa satisfação" absoluta.
3. **% do roadmap oscila entre meses** (ex.: I01 vai de 77% para 41%). *Tratamento:* o snapshot é o último mês do filtro, nunca a média de meses.
4. **Fulfillment mensal (R$ 406.686) ≠ soma por pedido (R$ 383.154), diferença de 6%.** *Tratamento:* o mensal é o custo oficial do resultado.
5. Testes A/B: `valor` vem arredondado a 2 casas (0,02 vs 0,03 com lift de 24%). *Tratamento:* usar a coluna `lift` informada.

## GATE C: Power BI Desktop (23/10/2026, PBI Desktop do usuário)

| # | Teste | Resultado |
|---|---|---|
| 1 | 201 JSON vs esquemas oficiais Microsoft | PASS, 0 erros |
| 2 | Abrir o .pbip no Desktop | PASS |
| 3 | Atualizar todas as queries (24 tabelas) | PASS |
| 4 | 18 medidas `Check *` (receita, pedidos, sessões, OTIF, NPS, CSAT, nota, conversão, custo, receita/CMV da rede) | PASS: todas = 0 |
| 5 | Pedidos do funil = pedidos de entrega = vendas, e cupom = itens, em 288 combinações loja × canal × mês | PASS: 0 divergências |
| 6 | Medidas vs Python: lucro bruto digital R$ 3.842.679, resultado R$ 2.106.189, clientes 13.594, recompra 60,5%, omnichannel 92,7%, YoY 11,7%, maturidade 81,9 | PASS |
| 7 | HTML Content: cards com sparkline, narrativas, chips, alertas | PASS (prints em `07_Testes\prints_ecom`) |
| 8 | Deneb: 7 specs renderizados | PASS após correção (o funil e o roadmap usavam `datum` sem tipo e quebravam ao combinar camadas) |
| 9 | Painel de filtros: abrir e "Aplicar e fechar" via bookmark | PASS |
| 10 | Custos ficam em branco com filtro de canal (custo é loja × mês) | PASS (comportamento intencional) |
| 11 | Performance Analyzer / Service / mobile | NÃO VALIDADO |

## Bugs encontrados na validação e corrigidos

- Spec Deneb do funil vazio (conflito de escala `datum` × `field`) → corrigido.
- `% Avaliações Abaixo de 4` devolvia vazio quando não havia nota 3 → as categorias sumiam do gráfico. Corrigido com `+ 0`.
- Matriz de oportunidade pintava de coral subcategorias com 0% → corrigido (exige % > mediana e > 0).

## Limitações

- Comparação com ano anterior só aparece com um ano filtrado de out/25 a set/26. No período completo, os cards mostram "sem base comparável".
- "Clientes novos" = 1ª compra digital observada desde out/2024. No período completo, todos são novos.
- O score de maturidade usa alvos-premissa (conversão de 4%, CSAT de 4,5) e alvos do roadmap (OTIF de 95%, NPS de +50), com pesos iguais. Não é benchmark de mercado.
- Resultado Digital Simplificado = lucro bruto digital − custos digitais diretos. Não rateia despesas da loja e não é EBITDA.
- Deneb e HTML Content não fazem filtro cruzado. No Service e no PDF, a animação CSS aparece estática.
- Tooltip de página único (receita digital por canal/loja). Tooltips específicos por KPI ficam no backlog.

## Backlog

1. Corrigir a base: gerar add to cart ≥ checkout, notas de 1 a 5 e roadmap monotônico.
2. Drillthrough de SKU e de cliente.
3. Medir no Performance Analyzer (cards HTML e Recompra/Omnichannel, que iteram clientes).
4. Publicar no Service e validar os visuais do AppSource no tenant.
