# Dicionário de dados — FarmaVitta E-commerce (base complementar)

**Versão 1.0 | Seed 20261023**

## dim_dispositivo
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_dispositivo | texto | Chave (D01–D04) |
| nome | texto | Mobile, Desktop, App Nativo, Tablet |
| tipo | texto | Mobile / Desktop / App |
| ordem | inteiro | Ordenação visual |

## dim_origem_trafego
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_origem | texto | Chave (O01–O09) |
| nome | texto | Nome da origem |
| grupo | texto | Orgânico / Pago / Owned / Outros |
| ordem | inteiro | Ordenação |

## dim_motivo_satisfacao
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_motivo | texto | Chave (M01–M20) |
| descricao | texto | Motivo textual |
| polaridade | texto | positivo / negativo |
| eixo | texto | entrega / produto / preço / atendimento / app / geral |

## dim_iniciativa
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_iniciativa | texto | Chave (I01–I15) |
| nome | texto | Nome da iniciativa do roadmap |
| pilar | texto | Conversão / CX / Produto / Operação / Estratégia |
| status | texto | Concluído / Em andamento / Planejado |
| trimestre_alvo | texto | Ex: 2025-Q2 |

## f_pedidos_digitais
Grão: 1 linha por venda digital (id_venda). 40.029 linhas. 1:1 com f_vendas digital.
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_venda | texto | FK → f_vendas |
| data_venda | data | |
| id_loja | texto | FK → dim_lojas |
| canal | texto | Site / Aplicativo / Delivery |
| frete_valor | decimal | Valor do frete (0 se grátis) |
| prazo_prometido_dias | inteiro | |
| prazo_real_dias | inteiro | |
| status_entrega | texto | Entregue no prazo / com atraso / Cancelado |
| custo_fulfillment | decimal | Custo operacional do pedido |
| otif | inteiro | 1 se prazo_real ≤ prometido |

## f_sessoes_digitais
Grão: data × loja × canal × dispositivo × origem (agregado diário).
| Campo | Tipo | Descrição |
|-------|------|-----------|
| data | data | |
| id_loja | texto | |
| canal | texto | |
| id_dispositivo | texto | FK |
| id_origem | texto | FK |
| sessoes | inteiro | |
| pageviews | inteiro | |
| add_to_cart | inteiro | |
| iniciou_checkout | inteiro | |
| pedidos | inteiro | Alocado para bater com vendas reais |

## f_avaliacoes_produto
Grão: 1 review por cliente × produto (amostra).
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_avaliacao | texto | |
| id_cliente | texto | FK |
| id_produto | texto | FK |
| id_venda | texto | FK |
| data_avaliacao | data | |
| nota | inteiro | 1 a 5 |
| comentario_curto | texto | Sintético |
| verificado | inteiro | 1 = compra verificada |
| canal_avaliacao | texto | |

## f_pesquisas_satisfacao
Grão: 1 resposta de pesquisa pós-compra.
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_pesquisa | texto | |
| id_cliente | texto | |
| id_venda | texto | |
| data_pesquisa | data | |
| canal | texto | |
| id_loja | texto | |
| nps_score | inteiro | 0 a 10 |
| csat_score | inteiro | 1 a 5 |
| id_motivo_principal | texto | FK → dim_motivo_satisfacao |
| canal_pesquisa | texto | E-mail / App / SMS |

## f_custos_digitais_mensais
Grão: loja × mês.
| Campo | Tipo | Descrição |
|-------|------|-----------|
| ano_mes | texto | YYYY-MM |
| id_loja | texto | |
| midia_paga | decimal | |
| plataforma | decimal | SaaS / gateway |
| fulfillment | decimal | |
| outros_digitais | decimal | |
| custo_digital_total | decimal | |
| receita_digital_ref | decimal | Referência (não usar como fato de receita) |
| pedidos_ref | inteiro | |

## f_experimentos_ab
Grão: experimento × variante.
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_experimento | texto | |
| nome_experimento | texto | |
| variante | texto | A - Controle / B - ... |
| data_inicio | data | |
| data_fim | data | |
| metrica | texto | conversao, ticket_medio, etc. |
| valor | decimal | |
| lift | decimal | Lift vs controle |
| resultado | texto | vencedor / baseline / empatado |

## f_roadmap_iniciativas
Grão: iniciativa × mês.
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id_iniciativa | texto | FK |
| ano_mes | texto | |
| pct_conclusao | inteiro | 0–100 |
| impacto_estimado_receita_pct | decimal | Proxy de impacto |
| status_mes | texto | |

## Regras de modelagem
1. Receita e CMV oficiais: sempre f_vendas / f_itens_venda.
2. f_pedidos_digitais é extensão 1:1 (não some receita dela).
3. Conversão = pedidos / sessões (f_sessoes_digitais).
4. NPS = %Promotores(9-10) − %Detratores(0-6).
5. Custos digitais não entram no CMV; usam-se no Resultado Digital Simplificado.
6. Experimentos e roadmap são narrativos/estratégicos.
