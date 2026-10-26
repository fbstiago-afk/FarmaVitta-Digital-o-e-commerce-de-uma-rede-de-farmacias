# FarmaVitta E-commerce — Base complementar sintética

**Versão 1.0 | Seed 20261023 | Dados 100% fictícios**

Não altera a base original de vendas. Formato: UTF-8 com BOM, separador `;`, decimal com ponto.

## Canais digitais (omnichannel)
Site · Aplicativo · Delivery

## KPIs de referência (reconciliados)
| KPI | Valor |
|-----|-------|
| Vendas digitais | 40.029 |
| Receita digital | R$ 9.774.295 |
| OTIF médio | 87,8% |
| Sessões totais | 1.274.133 |
| Conversão global | 3,14% |
| Avaliações de produto | 13.324 (nota média 3,98) |
| Pesquisas CSAT/NPS | 7.482 |
| NPS | +5,9 |
| CSAT médio | 4,41 |
| Custo digital total | R$ 1.736.490 |

## Tabelas geradas
| Arquivo | Linhas | Uso |
|---------|--------|-----|
| dim_dispositivo.csv | 4 | Dimensão |
| dim_origem_trafego.csv | 9 | Dimensão |
| dim_motivo_satisfacao.csv | 20 | Dimensão |
| dim_iniciativa.csv | 15 | Roadmap |
| f_pedidos_digitais.csv | 40.029 | Frete, prazo, OTIF (1:1 vendas digitais) |
| f_sessoes_digitais.csv | ~208k | Funil e conversão (agregado diário) |
| f_avaliacoes_produto.csv | 13.324 | Reviews 1–5 |
| f_pesquisas_satisfacao.csv | 7.482 | NPS / CSAT / motivos |
| f_custos_digitais_mensais.csv | 96 | Mídia, fulfillment, plataforma |
| f_experimentos_ab.csv | 14 | Testes A/B |
| f_roadmap_iniciativas.csv | 360 | Progresso do roadmap |

## Regras de uso no Power BI
1. **Receita e CMV oficiais** → sempre `f_vendas` / `f_itens_venda`.
2. `f_pedidos_digitais` é extensão 1:1 (não some receita dela).
3. Conversão = pedidos ÷ sessões (`f_sessoes_digitais`).
4. NPS = %Promotores(9–10) − %Detratores(0–6).
5. Custos digitais **não** entram no CMV → Resultado Digital Simplificado.
6. Experimentos e roadmap são narrativos/estratégicos.

Ver `DICIONARIO_DADOS_ECOM.md` e `RESUMO_ECOM.json` para detalhes.
