# -*- coding: utf-8 -*-
"""FarmaVitta E-commerce Intelligence — modelo semântico.
Reaproveita modelo.py (base oficial de vendas/itens/clientes/produtos) e os helpers HTML/SVG de modelo_v2.py,
remove as tabelas de suprimentos/forecast que não pertencem a este relatório e acrescenta as fatos digitais."""
import re
import modelo
import modelo_v2 as V2
from modelo import T, REL, MED, m, col, m_csv, mensal, BRL, BRL0, PCT, INT, DEC1, DEC2, PP, ORIG, TRAT

ECOM = "01_Dados_Originais\\base_complementar_ecommerce\\"
OK, ATN, BAD, NEU = V2.OK, V2.ATN, V2.BAD, V2.NEU
mi, fmt, html_cards, svg_bar = V2.mi, V2.fmt, V2.html_cards, V2.svg_bar

# ================================================================ 1. poda do modelo base
DROP_T = ["fEstoque", "fLotes", "fRecebimentos", "fOrcamentoCompras", "fForecast", "fBacktest", "dCenario", "dDRE"]
for t in DROP_T: T.pop(t)
REL[:] = [r for r in REL if r[0] not in DROP_T and r[2] not in DROP_T]
pat_t = re.compile(r"\b(" + "|".join(DROP_T) + r")\b")
drop = {x["n"] for x in MED if pat_t.search(x["dax"])}
drop |= {x["n"] for x in MED if x["n"].startswith("HTML ") or x["n"].startswith("_Spark ")}   # cards/narrativas da v2 são refeitos aqui
while True:
    novo = {x["n"] for x in MED if x["n"] not in drop and any(f"[{d}]" in x["dax"] for d in drop)}
    if not novo: break
    drop |= novo
MED[:] = [x for x in MED if x["n"] not in drop]
V2.SPARKED.clear()
N_PODADAS = len(drop)

# ================================================================ 2. ajustes em tabelas base
T["dCanal"] = dict(desc="Canais de venda. Grupo Canal separa Loja física de Digital (Site + Aplicativo + Delivery).",
    cols=[col("Canal", key=True, sort="Ordem Canal"), col("Ordem Canal", t="int64", hidden=True), col("Grupo Canal")],
    m='''let
    Fonte = #table(type table [Canal = text, Ordem Canal = Int64.Type, Grupo Canal = text], {{"Loja física", 1, "Físico"}, {"Aplicativo", 2, "Digital"}, {"Site", 3, "Digital"}, {"Delivery", 4, "Digital"}})
in
    Fonte''')

PRIMEIRA_DIG = f'''Dig = Table.Group(Table.SelectRows(Table.TransformColumnTypes(Table.SelectColumns(fnCsv("{ORIG}f_vendas.csv"), {{"id_cliente", "canal", "data_venda"}}), {{{{"data_venda", type date}}}}, "en-US"), each [id_cliente] <> "" and [canal] <> "Loja física"), {{"id_cliente"}}, {{{{"data_primeira_digital", each List.Min([data_venda]), type date}}}}),'''

# fVendas: flag de primeira compra digital observada
c = T["fVendas"]["cols"]
c.append(col("primeira_compra_digital", t="boolean", hidden=True, calc=True))
T["fVendas"]["m"] = T["fVendas"]["m"].replace("    Ultimo = Primeira,", f'''    {PRIMEIRA_DIG}
    JD = Table.NestedJoin(Primeira, "id_cliente", Dig, "id_cliente", "dg", JoinKind.LeftOuter),
    ED = Table.ExpandTableColumn(JD, "dg", {{"data_primeira_digital"}}),
    PrimDig = Table.AddColumn(ED, "primeira_compra_digital", each [canal] <> "Loja física" and [data_primeira_digital] <> null and [data_venda] = [data_primeira_digital], type logical),
    Ultimo = PrimDig,''')

# dCliente: coorte digital (mês da 1ª compra digital observada)
cc = T["dCliente"]["cols"]
cc += [col("Data Primeira Compra Digital", "data_primeira_digital", "dateTime", fmt="dd/MM/yyyy"),
       col("Coorte Digital", "coorte_digital", sort="Coorte Digital Num"), col("Coorte Digital Num", "coorte_digital_num", "int64", hidden=True)]
T["dCliente"]["desc"] += " Coorte Digital = mês da primeira compra digital observada (desde out/2024)."
T["dCliente"]["m"] = T["dCliente"]["m"].replace("    Final = Table.SelectColumns(Tipos, {", f'''    {PRIMEIRA_DIG}
    JD = Table.NestedJoin(Tipos, "id_cliente", Dig, "id_cliente", "dg", JoinKind.LeftOuter),
    ED = Table.ExpandTableColumn(JD, "dg", {{"data_primeira_digital"}}),
    Co = Table.AddColumn(ED, "coorte_digital", each if [data_primeira_digital] = null then null else Text.From(Date.Year([data_primeira_digital])) & "-" & Text.PadStart(Text.From(Date.Month([data_primeira_digital])), 2, "0"), type text),
    CoN = Table.AddColumn(Co, "coorte_digital_num", each if [data_primeira_digital] = null then null else Date.Year([data_primeira_digital]) * 100 + Date.Month([data_primeira_digital]), Int64.Type),
    Final = Table.SelectColumns(CoN, {{''')

def fix_select(nome):
    """Reescreve o Table.SelectColumns final com todas as colunas (inclusive as novas)."""
    t = T[nome]; lista = ", ".join('"%s"' % x["s"] for x in t["cols"])
    t["m"] = re.sub(r'(Final = Table\.SelectColumns\((\w+), )\{[^}]*\}\)', lambda mo: mo.group(1) + "{" + lista + "})", t["m"])
fix_select("fVendas"); fix_select("dCliente")

_fmt0 = V2.fmt
def _fmt(kind, v):
    if kind == "nps": return f'FORMAT ( {v}, "+0.0;-0.0;0.0", "pt-BR" )'
    if kind == "pct2": return f'FORMAT ( {v}, "0.00%", "pt-BR" )'
    return _fmt0(kind, v)
V2.fmt = _fmt; fmt = _fmt

# ================================================================ 3. dimensões digitais
def dim(nome, arq, cols, desc):
    T[nome] = dict(desc=desc, cols=cols, m=m_csv(ECOM + arq, cols, ''',
    Ultimo = Tipado,'''))
dim("dDispositivo", "dim_dispositivo.csv", [col("id_dispositivo", hidden=True, key=True), col("Dispositivo", "nome", sort="Ordem Dispositivo"),
    col("Tipo Dispositivo", "tipo"), col("Ordem Dispositivo", "ordem", "int64", hidden=True)], "Dispositivos de acesso (4).")
dim("dOrigemTrafego", "dim_origem_trafego.csv", [col("id_origem", hidden=True, key=True), col("Origem", "nome", sort="Ordem Origem"),
    col("Grupo Origem", "grupo"), col("Ordem Origem", "ordem", "int64", hidden=True)], "Origens de tráfego (9) em 4 grupos.")
dim("dMotivoSatisfacao", "dim_motivo_satisfacao.csv", [col("id_motivo", hidden=True, key=True), col("Motivo", "descricao"),
    col("Polaridade", "polaridade"), col("Eixo", "eixo")], "Motivo principal declarado na pesquisa (20).")
dim("dIniciativa", "dim_iniciativa.csv", [col("id_iniciativa", hidden=True, key=True), col("Iniciativa", "nome"), col("Pilar", "pilar"),
    col("Status Iniciativa", "status"), col("Trimestre Alvo", "trimestre_alvo")], "Iniciativas do roadmap digital (15). Status = situação final informada no cadastro.")

T["dEtapaFunil"] = dict(desc="Etapas do funil (desconectada). Add to cart fica fora: na base, checkouts > add to cart em todos os meses (ver GATE A).",
    cols=[col("Ordem Etapa", t="int64", hidden=True), col("Etapa", sort="Ordem Etapa")],
    m='''let
    Fonte = #table(type table [Ordem Etapa = Int64.Type, Etapa = text], {{1, "Sessões"}, {2, "Checkout iniciado"}, {3, "Pedido"}})
in
    Fonte''')
T["dMaturidade"] = dict(desc="Componentes do score de maturidade digital (desconectada). Alvos são premissas documentadas.",
    cols=[col("Ordem Componente", t="int64", hidden=True), col("Componente", sort="Ordem Componente"), col("Alvo", "Alvo"), col("Fonte Alvo", "Fonte Alvo")],
    m='''let
    Fonte = #table(type table [Ordem Componente = Int64.Type, Componente = text, Alvo = text, Fonte Alvo = text], {
        {1, "Conversão", "4,0%", "premissa do projeto (≈ App atual)"},
        {2, "OTIF", "95%", "iniciativa I08 do roadmap"},
        {3, "NPS", "+50", "iniciativa I09 do roadmap"},
        {4, "CSAT", "4,5", "premissa do projeto"},
        {5, "Roadmap", "100%", "conclusão média das 15 iniciativas"}})
in
    Fonte''')

# ================================================================ 4. fatos digitais
c = [col("id_venda", hidden=True), col("data_venda", t="dateTime", hidden=True, fmt="dd/MM/yyyy"), col("id_loja", hidden=True), col("canal", hidden=True),
     col("frete_valor", t="double", hidden=True), col("prazo_prometido_dias", t="int64", hidden=True), col("prazo_real_dias", t="int64", hidden=True),
     col("Status Entrega", "status_entrega"), col("custo_fulfillment", t="double", hidden=True), col("otif", t="int64", hidden=True),
     col("id_cliente", hidden=True, calc=True), col("atraso_dias", t="int64", hidden=True, calc=True), col("frete_gratis", t="int64", hidden=True, calc=True)]
T["fPedidosDigitais"] = dict(desc="Extensão 1:1 das vendas digitais (frete, prazo, OTIF). NÃO contém receita: receita vem de fVendas. Cliente herdado do cupom no Power Query.",
    cols=c, m=m_csv(ECOM + "f_pedidos_digitais.csv", c, f''',
    Cupom = Table.Buffer(Table.SelectColumns(fnCsv("{ORIG}f_vendas.csv"), {{"id_venda", "id_cliente"}})),
    J = Table.NestedJoin(Tipado, "id_venda", Cupom, "id_venda", "v", JoinKind.LeftOuter),
    E = Table.ExpandTableColumn(J, "v", {{"id_cliente"}}),
    Anon = Table.ReplaceValue(E, "", "NI", Replacer.ReplaceValue, {{"id_cliente"}}),
    Atraso = Table.AddColumn(Anon, "atraso_dias", each List.Max({{0, [prazo_real_dias] - [prazo_prometido_dias]}}), Int64.Type),
    Gratis = Table.AddColumn(Atraso, "frete_gratis", each if [frete_valor] = 0 then 1 else 0, Int64.Type),
    Ultimo = Gratis,'''))

c = [col("data", t="dateTime", hidden=True, fmt="dd/MM/yyyy"), col("id_loja", hidden=True), col("canal", hidden=True), col("id_dispositivo", hidden=True),
     col("id_origem", hidden=True), col("sessoes", t="int64", hidden=True), col("pageviews", t="int64", hidden=True), col("add_to_cart", t="int64", hidden=True),
     col("iniciou_checkout", t="int64", hidden=True), col("pedidos", t="int64", hidden=True)]
T["fSessoesDigitais"] = dict(desc="Funil agregado diário (data × loja × canal × dispositivo × origem). pedidos fecha com fVendas por dia × loja × canal.",
    cols=c, m=m_csv(ECOM + "f_sessoes_digitais.csv", c, ''',
    Ultimo = Tipado,'''))

c = [col("id_avaliacao", hidden=True), col("id_cliente", hidden=True), col("id_produto", hidden=True), col("id_venda", hidden=True),
     col("data_avaliacao", t="dateTime", hidden=True, fmt="dd/MM/yyyy"), col("Nota", "nota", "int64"), col("Comentário", "comentario_curto"),
     col("verificado", t="int64", hidden=True), col("canal_avaliacao", hidden=True), col("id_loja", hidden=True, calc=True)]
T["fAvaliacoesProduto"] = dict(desc="Reviews de produto (1 por cliente × produto, amostra). ATENÇÃO: a base só tem notas 3 e 4 (ver GATE A). Loja herdada do cupom.",
    cols=c, m=m_csv(ECOM + "f_avaliacoes_produto.csv", c, f''',
    Cupom = Table.Buffer(Table.SelectColumns(fnCsv("{ORIG}f_vendas.csv"), {{"id_venda", "id_loja"}})),
    J = Table.NestedJoin(Tipado, "id_venda", Cupom, "id_venda", "v", JoinKind.LeftOuter),
    E = Table.ExpandTableColumn(J, "v", {{"id_loja"}}),
    Ultimo = E,'''))

c = [col("id_pesquisa", hidden=True), col("id_cliente", hidden=True), col("id_venda", hidden=True), col("data_pesquisa", t="dateTime", hidden=True, fmt="dd/MM/yyyy"),
     col("canal", hidden=True), col("id_loja", hidden=True), col("nps_score", t="int64", hidden=True), col("CSAT", "csat_score", "int64"),
     col("id_motivo_principal", hidden=True), col("Canal Pesquisa", "canal_pesquisa"),
     col("Classe NPS", sort="Ordem Classe NPS", calc=True), col("Ordem Classe NPS", t="int64", hidden=True, calc=True)]
T["fPesquisasSatisfacao"] = dict(desc="Pesquisas pós-compra (NPS 0–10, CSAT 1–5, motivo principal).",
    cols=c, m=m_csv(ECOM + "f_pesquisas_satisfacao.csv", c, ''',
    Classe = Table.AddColumn(Tipado, "Classe NPS", each if [nps_score] >= 9 then "Promotor" else if [nps_score] >= 7 then "Neutro" else "Detrator", type text),
    Ordem = Table.AddColumn(Classe, "Ordem Classe NPS", each if [nps_score] >= 9 then 1 else if [nps_score] >= 7 then 2 else 3, Int64.Type),
    Ultimo = Ordem,'''))

c = [col("ano_mes", hidden=True), col("data_mes", t="dateTime", hidden=True, calc=True, fmt="dd/MM/yyyy"), col("id_loja", hidden=True),
     col("midia_paga", t="double", hidden=True), col("plataforma", t="double", hidden=True), col("fulfillment", t="double", hidden=True),
     col("outros_digitais", t="double", hidden=True), col("custo_digital_total", t="double", hidden=True)]
T["fCustosDigitais"] = dict(desc="Custos digitais por loja × mês (não entram no CMV). receita_digital_ref/pedidos_ref da fonte não são carregados: receita vem de fVendas.",
    cols=c, m=mensal(ECOM + "f_custos_digitais_mensais.csv", c))

c = [col("id_experimento", hidden=True), col("Experimento", "nome_experimento"), col("Variante", "variante"),
     col("Inicio Teste", "data_inicio", "dateTime", fmt="dd/MM/yyyy"), col("Fim Teste", "data_fim", "dateTime", fmt="dd/MM/yyyy"),
     col("Métrica Teste", "metrica"), col("valor", t="double", hidden=True), col("lift", t="double", hidden=True), col("Resultado Teste", "resultado")]
T["fExperimentosAB"] = dict(desc="Testes A/B (7 experimentos × 2 variantes). Desconectada: narrativa estratégica, não fato de receita. 'valor' vem arredondado a 2 casas; usar 'lift' informado.",
    cols=c, m=m_csv(ECOM + "f_experimentos_ab.csv", c, ''',
    Ultimo = Tipado,'''))

c = [col("id_iniciativa", hidden=True), col("ano_mes", hidden=True), col("data_mes", t="dateTime", hidden=True, calc=True, fmt="dd/MM/yyyy"),
     col("pct_conclusao", t="double", hidden=True), col("impacto_estimado_receita_pct", t="double", hidden=True), col("Status Mês", "status_mes")]
T["fRoadmapIniciativas"] = dict(desc="Progresso mensal das iniciativas. O % não é monotônico na fonte: as medidas usam o último mês do filtro (snapshot), nunca média de meses.",
    cols=c, m=mensal(ECOM + "f_roadmap_iniciativas.csv", c))

# _Medidas sempre por último
med = T.pop("_Medidas"); T["_Medidas"] = med

REL += [
    ("fPedidosDigitais", "data_venda", "dCalendario", "Data"), ("fPedidosDigitais", "id_loja", "dLoja", "id_loja"),
    ("fPedidosDigitais", "canal", "dCanal", "Canal"), ("fPedidosDigitais", "id_cliente", "dCliente", "id_cliente"),
    ("fSessoesDigitais", "data", "dCalendario", "Data"), ("fSessoesDigitais", "id_loja", "dLoja", "id_loja"),
    ("fSessoesDigitais", "canal", "dCanal", "Canal"), ("fSessoesDigitais", "id_dispositivo", "dDispositivo", "id_dispositivo"),
    ("fSessoesDigitais", "id_origem", "dOrigemTrafego", "id_origem"),
    ("fAvaliacoesProduto", "data_avaliacao", "dCalendario", "Data"), ("fAvaliacoesProduto", "id_produto", "dProduto", "id_produto"),
    ("fAvaliacoesProduto", "id_cliente", "dCliente", "id_cliente"), ("fAvaliacoesProduto", "canal_avaliacao", "dCanal", "Canal"),
    ("fAvaliacoesProduto", "id_loja", "dLoja", "id_loja"),
    ("fPesquisasSatisfacao", "data_pesquisa", "dCalendario", "Data"), ("fPesquisasSatisfacao", "id_cliente", "dCliente", "id_cliente"),
    ("fPesquisasSatisfacao", "canal", "dCanal", "Canal"), ("fPesquisasSatisfacao", "id_loja", "dLoja", "id_loja"),
    ("fPesquisasSatisfacao", "id_motivo_principal", "dMotivoSatisfacao", "id_motivo"),
    ("fCustosDigitais", "data_mes", "dCalendario", "Data"), ("fCustosDigitais", "id_loja", "dLoja", "id_loja"),
    ("fRoadmapIniciativas", "data_mes", "dCalendario", "Data"), ("fRoadmapIniciativas", "id_iniciativa", "dIniciativa", "id_iniciativa"),
]

# ================================================================ 5. medidas
DIG = 'KEEPFILTERS ( dCanal[Grupo Canal] = "Digital" )'
LYW = "SAMEPERIODLASTYEAR ( VAR _db = [_Data Base] RETURN CALCULATETABLE ( VALUES ( dCalendario[Data] ), KEEPFILTERS ( dCalendario[Data] <= _db ) ) )"
def ly(nome, base, pasta, f):
    m(nome, pasta, f, f"IF ( [_Periodo Comparavel LY], CALCULATE ( [{base}], {LYW} ) )", f"[{base}] no mesmo período do ano anterior (só com período comparável completo).")
NPSF = '+0.0;-0.0;0.0'

# 00 Base digital
B = "00 Base Digital"
m("Receita Digital", B, BRL, f"CALCULATE ( [Receita Líquida], {DIG} )", "Receita líquida (f_vendas) dos canais Site, Aplicativo e Delivery. Nunca vem de f_pedidos_digitais.")
m("CMV Digital", B, BRL, f"CALCULATE ( [CMV], {DIG} )")
m("Descontos Digitais", B, BRL, f"CALCULATE ( [Descontos], {DIG} )")
m("Receita Bruta Digital", B, BRL, f"CALCULATE ( [Receita Bruta], {DIG} )")
m("Pedidos Digitais", B, INT, f"CALCULATE ( [Cupons], {DIG} )", "Cupons dos canais digitais (f_vendas). = linhas de f_pedidos_digitais (GATE A).")
m("Unidades Digitais", B, INT, f"CALCULATE ( [Unidades Vendidas], {DIG} )")
m("Receita Rede (todos os canais)", B, BRL, "CALCULATE ( [Receita Líquida], REMOVEFILTERS ( dCanal ) )", "Denominador do share digital: ignora o filtro de canal.")

# 01 Tempo digital
Tm = "01 Tempo Digital"
ly("Receita Digital LY", "Receita Digital", Tm, BRL)
m("Receita Digital YoY %", Tm, PCT, "DIVIDE ( [Receita Digital] - [Receita Digital LY], [Receita Digital LY] )")
ly("Lucro Bruto Digital LY", "Lucro Bruto Digital", Tm, BRL)
m("Lucro Bruto Digital YoY %", Tm, PCT, "DIVIDE ( [Lucro Bruto Digital] - [Lucro Bruto Digital LY], [Lucro Bruto Digital LY] )")
m("Margem Digital LY", Tm, PCT, "DIVIDE ( [Lucro Bruto Digital LY], [Receita Digital LY] )")
m("Margem Digital Var pp", Tm, PP, "IF ( NOT ISBLANK ( [Margem Digital LY] ), ( [Margem Bruta Digital %] - [Margem Digital LY] ) * 100 )")
ly("Pedidos Digitais LY", "Pedidos Digitais", Tm, INT)
m("Pedidos Digitais YoY %", Tm, PCT, "DIVIDE ( [Pedidos Digitais] - [Pedidos Digitais LY], [Pedidos Digitais LY] )")
m("Ticket Digital LY", Tm, BRL, "DIVIDE ( [Receita Digital LY], [Pedidos Digitais LY] )")
m("Ticket Digital YoY %", Tm, PCT, "DIVIDE ( [Ticket Médio Digital] - [Ticket Digital LY], [Ticket Digital LY] )")
m("Share Digital LY", Tm, PCT, "IF ( [_Periodo Comparavel LY], CALCULATE ( [Share Digital %], " + LYW + " ) )")
m("Share Digital Var pp", Tm, PP, "IF ( NOT ISBLANK ( [Share Digital LY] ), ( [Share Digital %] - [Share Digital LY] ) * 100 )")
ly("Sessões LY", "Sessões", Tm, INT)
m("Sessões YoY %", Tm, PCT, "DIVIDE ( [Sessões] - [Sessões LY], [Sessões LY] )")
ly("Conversão LY", "Taxa Conversão %", Tm, PCT)
m("Conversão Var pp", Tm, PP, "IF ( NOT ISBLANK ( [Conversão LY] ), ( [Taxa Conversão %] - [Conversão LY] ) * 100 )")
ly("NPS LY", "NPS", Tm, NPSF)
m("NPS Var", Tm, NPSF, "IF ( NOT ISBLANK ( [NPS LY] ), [NPS] - [NPS LY] )", "Variação do NPS em pontos.")
ly("OTIF LY", "OTIF %", Tm, PCT)
m("OTIF Var pp", Tm, PP, "IF ( NOT ISBLANK ( [OTIF LY] ), ( [OTIF %] - [OTIF LY] ) * 100 )")
ly("Clientes Digitais LY", "Clientes Digitais", Tm, INT)
m("Clientes Digitais YoY %", Tm, PCT, "DIVIDE ( [Clientes Digitais] - [Clientes Digitais LY], [Clientes Digitais LY] )")
m("Receita Digital Mês Anterior", Tm, BRL, "CALCULATE ( [Receita Digital], DATEADD ( dCalendario[Data], -1, MONTH ) )")
m("Receita Digital MoM %", Tm, PCT, "DIVIDE ( [Receita Digital] - [Receita Digital Mês Anterior], [Receita Digital Mês Anterior] )")
m("Receita Digital YTD", Tm, BRL, "TOTALYTD ( [Receita Digital], dCalendario[Data] )")

# 02 Comercial digital
Cm = "02 Comercial Digital"
m("Lucro Bruto Digital", Cm, BRL, "[Receita Digital] - [CMV Digital]")
m("Margem Bruta Digital %", Cm, PCT, "DIVIDE ( [Lucro Bruto Digital], [Receita Digital] )")
m("Ticket Médio Digital", Cm, BRL, "DIVIDE ( [Receita Digital], [Pedidos Digitais] )")
m("Itens por Pedido Digital", Cm, DEC2, "DIVIDE ( [Unidades Digitais], [Pedidos Digitais] )")
m("Desconto Digital %", Cm, PCT, "DIVIDE ( [Descontos Digitais], [Receita Bruta Digital] )")
m("Share Digital %", Cm, PCT, "DIVIDE ( [Receita Digital], [Receita Rede (todos os canais)] )", "Receita digital / receita líquida da rede no mesmo filtro de loja, data e produto.")
m("Share Canal no Digital %", Cm, PCT, "DIVIDE ( [Receita Digital], CALCULATE ( [Receita Digital], ALLSELECTED ( dCanal ) ) )")

# 03 Funil
F = "03 Funil & Conversão"
m("Sessões", F, INT, "SUM ( fSessoesDigitais[sessoes] )")
m("Pageviews", F, INT, "SUM ( fSessoesDigitais[pageviews] )")
m("Add to Cart", F, INT, "SUM ( fSessoesDigitais[add_to_cart] )", "ATENÇÃO: menor que Checkouts na base (defeito de origem). Não usar como etapa do funil.")
m("Checkouts Iniciados", F, INT, "SUM ( fSessoesDigitais[iniciou_checkout] )")
m("Pedidos (Funil)", F, INT, "SUM ( fSessoesDigitais[pedidos] )", "Pedidos alocados nas sessões. Fecha com Pedidos Digitais por dia × loja × canal.")
m("Taxa Conversão %", F, '0.00%;-0.00%;0.00%', "DIVIDE ( [Pedidos (Funil)], [Sessões] )", "Pedidos ÷ sessões (f_sessoes_digitais).")
m("Taxa Add to Cart %", F, PCT, "DIVIDE ( [Add to Cart], [Sessões] )", "Sessões com add to cart ÷ sessões. Indicador isolado (não é etapa do funil).")
m("Taxa Checkout %", F, PCT, "DIVIDE ( [Checkouts Iniciados], [Sessões] )")
m("Checkout → Pedido %", F, PCT, "DIVIDE ( [Pedidos (Funil)], [Checkouts Iniciados] )", "Pedidos ÷ checkouts iniciados.")
m("Abandono Checkout %", F, PCT, "1 - [Checkout → Pedido %]", "Checkouts que não viraram pedido. Substitui 'abandono de carrinho', que a base não sustenta.")
m("Pageviews por Sessão", F, DEC2, "DIVIDE ( [Pageviews], [Sessões] )")
m("Receita por Sessão", F, BRL, "DIVIDE ( CALCULATE ( [Receita Digital], REMOVEFILTERS ( dDispositivo ), REMOVEFILTERS ( dOrigemTrafego ) ), [Sessões] )",
  "Receita digital ÷ sessões. Sem filtro de dispositivo/origem (a receita não tem essas dimensões).")
m("Valor Etapa Funil", F, INT, "SWITCH ( SELECTEDVALUE ( dEtapaFunil[Ordem Etapa] ), 1, [Sessões], 2, [Checkouts Iniciados], 3, [Pedidos (Funil)] )")
m("Alerta Funil", F, "", 'IF ( [Add to Cart] < [Checkouts Iniciados], "Add to cart < checkout na fonte: etapa removida do funil", "" )')
m("Share Sessões %", F, PCT, "DIVIDE ( [Sessões], CALCULATE ( [Sessões], ALLSELECTED ( dDispositivo ), ALLSELECTED ( dOrigemTrafego ), ALLSELECTED ( dCanal ) ) )")

# 04 CX
X = "04 CX"
m("Pedidos Entrega", X, INT, "COUNTROWS ( fPedidosDigitais )")
m("OTIF %", X, PCT, "DIVIDE ( SUM ( fPedidosDigitais[otif] ), [Pedidos Entrega] )", "Pedidos com prazo real ≤ prometido ÷ pedidos digitais. Não mede quantidade completa (in full): a base não tem quantidade prometida.")
m("% Entregas com Atraso", X, PCT, 'DIVIDE ( CALCULATE ( [Pedidos Entrega], fPedidosDigitais[Status Entrega] = "Entregue com atraso" ), [Pedidos Entrega] )')
m("% Cancelado ou Problema", X, PCT, 'DIVIDE ( CALCULATE ( [Pedidos Entrega], fPedidosDigitais[Status Entrega] = "Cancelado / Problema" ), [Pedidos Entrega] )')
m("Frete Médio", X, BRL, "AVERAGE ( fPedidosDigitais[frete_valor] )", "Frete médio por pedido (inclui fretes grátis = 0).")
m("Frete Médio Pago", X, BRL, "CALCULATE ( AVERAGE ( fPedidosDigitais[frete_valor] ), fPedidosDigitais[frete_gratis] = 0 )")
m("% Frete Grátis", X, PCT, "DIVIDE ( SUM ( fPedidosDigitais[frete_gratis] ), [Pedidos Entrega] )")
m("Prazo Prometido Médio", X, '#,0.0 "dias"', "AVERAGE ( fPedidosDigitais[prazo_prometido_dias] )")
m("Prazo Real Médio", X, '#,0.0 "dias"', "AVERAGE ( fPedidosDigitais[prazo_real_dias] )")
m("Atraso Médio Entrega", X, '#,0.0 "dias"', "AVERAGEX ( FILTER ( fPedidosDigitais, fPedidosDigitais[atraso_dias] > 0 ), fPedidosDigitais[atraso_dias] )", "Média de dias de atraso só entre os pedidos atrasados.")
m("Custo Fulfillment Pedidos", X, BRL, "SUM ( fPedidosDigitais[custo_fulfillment] )", "Soma por pedido. Difere ~6% do fulfillment mensal (fonte oficial de custo).")
m("Respostas Pesquisa", X, INT, "COUNTROWS ( fPesquisasSatisfacao )")
m("Taxa de Resposta %", X, PCT, "DIVIDE ( [Respostas Pesquisa], [Pedidos Entrega] )")
m("Promotores", X, INT, "CALCULATE ( [Respostas Pesquisa], fPesquisasSatisfacao[nps_score] >= 9 )")
m("Detratores", X, INT, "CALCULATE ( [Respostas Pesquisa], fPesquisasSatisfacao[nps_score] <= 6 )")
m("Neutros", X, INT, "[Respostas Pesquisa] - [Promotores] - [Detratores]")
m("% Promotores", X, PCT, "DIVIDE ( [Promotores], [Respostas Pesquisa] )")
m("% Neutros", X, PCT, "DIVIDE ( [Neutros], [Respostas Pesquisa] )")
m("% Detratores", X, PCT, "DIVIDE ( [Detratores], [Respostas Pesquisa] )")
m("NPS", X, NPSF, "IF ( [Respostas Pesquisa] > 0, ( [% Promotores] - [% Detratores] ) * 100 )", "% promotores (9–10) − % detratores (0–6), em pontos (−100 a +100).")
m("CSAT Médio", X, DEC2, "AVERAGE ( fPesquisasSatisfacao[CSAT] )", "Média da nota CSAT (1–5).")
m("% CSAT Satisfeito", X, PCT, "DIVIDE ( CALCULATE ( [Respostas Pesquisa], fPesquisasSatisfacao[CSAT] >= 4 ), [Respostas Pesquisa] )", "Respostas com CSAT 4 ou 5.")
m("% Motivo Negativo", X, PCT, 'DIVIDE ( CALCULATE ( [Respostas Pesquisa], dMotivoSatisfacao[Polaridade] = "negativo" ), [Respostas Pesquisa] )')
m("Share Respostas %", X, PCT, "DIVIDE ( [Respostas Pesquisa], CALCULATE ( [Respostas Pesquisa], ALLSELECTED ( dMotivoSatisfacao ) ) )")

# 05 Produtos
Pd = "05 Produtos Digital"
m("Avaliações", Pd, INT, "COUNTROWS ( fAvaliacoesProduto )")
m("Nota Média Produto", Pd, DEC2, "AVERAGE ( fAvaliacoesProduto[Nota] )", "Média das notas 1–5. Na base só existem notas 3 e 4: use a comparação relativa.")
m("% Avaliações Abaixo de 4", Pd, PCT, "DIVIDE ( CALCULATE ( [Avaliações], fAvaliacoesProduto[Nota] < 4 ) + 0, [Avaliações] )", "Sinal relativo de insatisfação (única variação disponível na base).")
m("% Avaliações Verificadas", Pd, PCT, "DIVIDE ( CALCULATE ( [Avaliações], fAvaliacoesProduto[verificado] = 1 ), [Avaliações] )")
m("Share Avaliações %", Pd, PCT, "DIVIDE ( [Avaliações], CALCULATE ( [Avaliações], ALLSELECTED ( fAvaliacoesProduto[Nota] ) ) )")
m("Receita Digital Itens", Pd, BRL, f"CALCULATE ( [Receita Líquida Itens], {DIG} )", "Receita líquida de itens nos canais digitais (f_itens_venda).")
m("Lucro Bruto Digital Itens", Pd, BRL, f"CALCULATE ( [Lucro Bruto Itens], {DIG} )")
m("Margem Digital Itens %", Pd, PCT, "DIVIDE ( [Lucro Bruto Digital Itens], [Receita Digital Itens] )")
m("Unidades Digitais Itens", Pd, INT, f"CALCULATE ( SUM ( fItensVenda[quantidade] ), {DIG} )")
m("SKUs Digitais Vendidos", Pd, INT, f"CALCULATE ( DISTINCTCOUNT ( fItensVenda[id_produto] ), {DIG} )")
m("Avaliações por 100 Unidades", Pd, DEC1, "DIVIDE ( [Avaliações], [Unidades Digitais Itens] ) * 100")
m("Score Oportunidade", Pd, INT, "IF ( [Avaliações] >= 5, [Unidades Digitais Itens] * [% Avaliações Abaixo de 4] )",
  "Unidades digitais × % de avaliações abaixo de 4 (mín. 5 avaliações). Prioriza volume com insatisfação relativa. Premissa, não causalidade.")
m("Ranking Oportunidade", Pd, INT, "IF ( NOT ISBLANK ( [Score Oportunidade] ), RANKX ( ALLSELECTED ( dProduto ), [Score Oportunidade],, DESC, DENSE ) )")
m("Share Receita Digital Categoria %", Pd, PCT, "DIVIDE ( [Receita Digital Itens], CALCULATE ( [Receita Digital Itens], ALLSELECTED ( dProduto ) ) )")

# 06 Clientes
Cl = "06 Clientes Digitais"
m("Clientes Digitais", Cl, INT, f"CALCULATE ( DISTINCTCOUNT ( fVendas[id_cliente] ), {DIG}, fVendas[cliente_identificado] = TRUE () )", "Clientes identificados com ao menos 1 pedido digital no período.")
m("Pedidos Digitais Identificados", Cl, INT, f"CALCULATE ( [Cupons], {DIG}, fVendas[cliente_identificado] = TRUE () )")
m("% Pedidos Digitais Identificados", Cl, PCT, "DIVIDE ( [Pedidos Digitais Identificados], [Pedidos Digitais] )")
m("Clientes Digitais Novos", Cl, INT, f"CALCULATE ( DISTINCTCOUNT ( fVendas[id_cliente] ), {DIG}, fVendas[primeira_compra_digital] = TRUE () )",
  "Clientes cuja 1ª compra digital observada (desde out/2024) caiu no período. Nos primeiros meses, quase todos aparecem como novos.")
m("Clientes Digitais Recorrentes", Cl, INT, "[Clientes Digitais] - [Clientes Digitais Novos]")
m("% Novos Digitais", Cl, PCT, "DIVIDE ( [Clientes Digitais Novos], [Clientes Digitais] )")
m("Frequência Digital", Cl, DEC2, "DIVIDE ( [Pedidos Digitais Identificados], [Clientes Digitais] )", "Pedidos digitais por cliente identificado no período.")
m("Recompra Digital %", Cl, PCT, f"""
VAR _c = CALCULATETABLE ( VALUES ( fVendas[id_cliente] ), {DIG}, fVendas[cliente_identificado] = TRUE () )
VAR _r = COUNTROWS ( FILTER ( _c, CALCULATE ( COUNTROWS ( fVendas ), {DIG} ) >= 2 ) )
RETURN DIVIDE ( _r, COUNTROWS ( _c ) )""", "% dos clientes digitais com 2+ pedidos digitais no período.")
m("Ticket Digital Identificado", Cl, BRL, f"CALCULATE ( [Ticket Médio], {DIG}, fVendas[cliente_identificado] = TRUE () )")
m("Receita Digital por Cliente", Cl, BRL, f"DIVIDE ( CALCULATE ( [Receita Líquida], {DIG}, fVendas[cliente_identificado] = TRUE () ), [Clientes Digitais] )")
m("% Clientes Omnichannel", Cl, PCT, f"""
VAR _c = CALCULATETABLE ( VALUES ( fVendas[id_cliente] ), {DIG}, fVendas[cliente_identificado] = TRUE () )
VAR _o = FILTER ( _c, CALCULATE ( COUNTROWS ( fVendas ), REMOVEFILTERS ( dCanal ), dCanal[Grupo Canal] = "Físico" ) > 0 )
RETURN DIVIDE ( COUNTROWS ( _o ), COUNTROWS ( _c ) )""", "% dos clientes digitais que também compraram na loja física no mesmo período.")
m("Tamanho Coorte", Cl, INT, "CALCULATE ( COUNTROWS ( dCliente ), REMOVEFILTERS ( dCalendario ), NOT ISBLANK ( dCliente[Coorte Digital Num] ) )", "Clientes cuja 1ª compra digital caiu no mês da coorte.")
m("Retenção Coorte %", Cl, PCT, "DIVIDE ( [Clientes Digitais], [Tamanho Coorte] )", "Clientes da coorte com pedido digital no mês ÷ tamanho da coorte. Coorte simples (1ª compra observada).")
m("Share Clientes Digitais %", Cl, PCT, "DIVIDE ( [Clientes Digitais], CALCULATE ( [Clientes Digitais], ALLSELECTED ( dCliente ) ) )")

# 07 Financeiro digital
Fi = "07 Financeiro Digital"
m("_Filtro Sem Custo Digital", "99 Auditoria", "", "ISFILTERED ( dProduto ) || ISFILTERED ( dCliente ) || ISFILTERED ( dCanal[Canal] ) || ISFILTERED ( dDispositivo ) || ISFILTERED ( dOrigemTrafego ) || ISFILTERED ( dMotivoSatisfacao ) || ISFILTERED ( dFornecedor )",
  "Verdadeiro quando há filtro em dimensão que não existe nos custos digitais (loja × mês): custos e resultado ficam em branco.")
for n_, c_, d_ in [("Custo Digital Total", "custo_digital_total", "Mídia + plataforma + fulfillment + outros (loja × mês)."), ("Custo Mídia Paga", "midia_paga", ""),
                   ("Custo Plataforma", "plataforma", "SaaS / gateway."), ("Custo Fulfillment", "fulfillment", "Fonte oficial de fulfillment (mensal)."), ("Outros Custos Digitais", "outros_digitais", "")]:
    m(n_, Fi, BRL, f"IF ( NOT [_Filtro Sem Custo Digital], SUM ( fCustosDigitais[{c_}] ) )", d_ + " Em branco com filtro de canal, produto, cliente, dispositivo ou origem.")
m("Resultado Digital Simplificado", Fi, BRL, "IF ( NOT [_Filtro Sem Custo Digital], [Lucro Bruto Digital] - [Custo Digital Total] )",
  "Lucro bruto digital − custos digitais diretos. Não rateia despesas da loja. NÃO é EBITDA nem lucro.")
m("Margem Resultado Digital %", Fi, PCT, "DIVIDE ( [Resultado Digital Simplificado], [Receita Digital] )")
m("Custo Digital % Receita", Fi, PCT, "DIVIDE ( [Custo Digital Total], [Receita Digital] )")
m("Mídia % Receita Digital", Fi, PCT, "DIVIDE ( [Custo Mídia Paga], [Receita Digital] )")
m("ROAS Proxy", Fi, '0.0"x"', "DIVIDE ( [Receita Digital], [Custo Mídia Paga] )", "Receita digital total ÷ mídia paga. Proxy: a receita não é atribuída por campanha.")
m("Custo por Pedido Digital", Fi, BRL, "DIVIDE ( [Custo Digital Total], [Pedidos Digitais] )")
m("Mídia por Cliente Novo (proxy CAC)", Fi, BRL, "DIVIDE ( [Custo Mídia Paga], [Clientes Digitais Novos] )", "Mídia paga ÷ clientes digitais novos. Proxy de CAC: sem atribuição por canal de aquisição.")
ly("Resultado Digital LY", "Resultado Digital Simplificado", Tm, BRL)
m("Resultado Digital YoY %", Tm, PCT, "DIVIDE ( [Resultado Digital Simplificado] - [Resultado Digital LY], ABS ( [Resultado Digital LY] ) )")

# 08 Estratégia
E = "08 Estratégia"
m("_Mes Roadmap", E, "dd/MM/yyyy", "CALCULATE ( MAX ( fRoadmapIniciativas[data_mes] ) )", "Último mês do roadmap dentro do filtro de datas.")
m("% Conclusão Roadmap", E, PCT, """
VAR _m = [_Mes Roadmap]
RETURN DIVIDE ( CALCULATE ( AVERAGE ( fRoadmapIniciativas[pct_conclusao] ), REMOVEFILTERS ( dCalendario ), fRoadmapIniciativas[data_mes] = _m ), 100 )""",
  "Média do % de conclusão das iniciativas no último mês do período (snapshot). Nunca média de meses: o % oscila na fonte.")
m("Impacto Estimado (índice)", E, "0.00", """
VAR _m = [_Mes Roadmap]
RETURN CALCULATE ( SUM ( fRoadmapIniciativas[impacto_estimado_receita_pct] ), REMOVEFILTERS ( dCalendario ), fRoadmapIniciativas[data_mes] = _m )""",
  "Soma do proxy de impacto no último mês. Unidade não documentada na fonte: tratar como índice relativo, não como % de receita.")
m("Iniciativas", E, INT, "COUNTROWS ( dIniciativa )")
m("Iniciativas Concluídas", E, INT, """
VAR _m = [_Mes Roadmap]
RETURN CALCULATE ( COUNTROWS ( fRoadmapIniciativas ), REMOVEFILTERS ( dCalendario ), fRoadmapIniciativas[data_mes] = _m, fRoadmapIniciativas[Status Mês] = "Concluído" ) + 0""")
m("Iniciativas Em Andamento", E, INT, """
VAR _m = [_Mes Roadmap]
RETURN CALCULATE ( COUNTROWS ( fRoadmapIniciativas ), REMOVEFILTERS ( dCalendario ), fRoadmapIniciativas[data_mes] = _m, fRoadmapIniciativas[Status Mês] = "Em andamento" ) + 0""")
m("Status Roadmap Atual", E, "", """
VAR _m = [_Mes Roadmap]
RETURN CALCULATE ( MAX ( fRoadmapIniciativas[Status Mês] ), REMOVEFILTERS ( dCalendario ), fRoadmapIniciativas[data_mes] = _m )""")
m("Experimentos", E, INT, "DISTINCTCOUNT ( fExperimentosAB[id_experimento] )")
m("Experimentos Vencedores", E, INT, 'CALCULATE ( DISTINCTCOUNT ( fExperimentosAB[id_experimento] ), fExperimentosAB[Resultado Teste] = "vencedor" ) + 0')
m("Lift Experimento", E, '+0%;-0%;0%', 'CALCULATE ( MAX ( fExperimentosAB[lift] ), fExperimentosAB[Resultado Teste] <> "baseline" )', "Lift informado da variante B vs controle (coluna lift da fonte).")
m("Lift Médio Vencedores", E, '+0%;-0%;0%', 'CALCULATE ( AVERAGE ( fExperimentosAB[lift] ), fExperimentosAB[Resultado Teste] = "vencedor" )')
m("Taxa de Vitória Testes %", E, PCT, "DIVIDE ( [Experimentos Vencedores], [Experimentos] )")
m("Cor Resultado Teste", E, "", f'SWITCH ( CALCULATE ( MAX ( fExperimentosAB[Resultado Teste] ), fExperimentosAB[Resultado Teste] <> "baseline" ), "vencedor", "{OK}", "empatado", "{ATN}", "{BAD}" )')
SC = {1: "MIN ( 1, DIVIDE ( [Taxa Conversão %], 0.04 ) )", 2: "MIN ( 1, DIVIDE ( [OTIF %], 0.95 ) )",
      3: "MAX ( 0, MIN ( 1, DIVIDE ( [NPS] + 100, 150 ) ) )", 4: "MAX ( 0, MIN ( 1, DIVIDE ( [CSAT Médio] - 1, 3.5 ) ) )", 5: "MIN ( 1, [% Conclusão Roadmap] )"}
m("Score Componente", E, "0", "SWITCH ( SELECTEDVALUE ( dMaturidade[Ordem Componente] ), " + ", ".join(f"{k}, {v} * 100" for k, v in SC.items()) + " )",
  "Atingimento do alvo do componente (0–100). NPS normalizado de −100..+50; CSAT de 1..4,5.")
m("Valor Componente", E, "", """SWITCH ( SELECTEDVALUE ( dMaturidade[Ordem Componente] ),
    1, FORMAT ( [Taxa Conversão %], "0.00%", "pt-BR" ), 2, FORMAT ( [OTIF %], "0.0%", "pt-BR" ), 3, FORMAT ( [NPS], "+0.0;-0.0", "pt-BR" ),
    4, FORMAT ( [CSAT Médio], "0.00", "pt-BR" ), 5, FORMAT ( [% Conclusão Roadmap], "0%", "pt-BR" ) )""")
m("Score Maturidade Digital", E, "0", "AVERAGEX ( ALL ( dMaturidade[Ordem Componente] ), [Score Componente] )",
  "Média simples dos 5 componentes (0–100). Score de gestão com pesos iguais e alvos-premissa: não é benchmark de mercado.")
m("Cor Score", E, "", f'VAR _s = COALESCE ( [Score Componente], [Score Maturidade Digital] ) RETURN IF ( ISBLANK ( _s ), "{NEU}", IF ( _s >= 90, "{OK}", IF ( _s >= 70, "{ATN}", "{BAD}" ) ) )')

# 10 UI — cores e textos
U = "10 UI & Formatação"
m("Cor NPS", U, "", f'VAR _v = [NPS] RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v >= 30, "{OK}", IF ( _v >= 0, "{ATN}", "{BAD}" ) ) )')
m("Cor OTIF", U, "", f'VAR _v = [OTIF %] RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v >= 0.95, "{OK}", IF ( _v >= 0.85, "{ATN}", "{BAD}" ) ) )')
m("Cor CSAT", U, "", f'VAR _v = [CSAT Médio] RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v >= 4.5, "{OK}", IF ( _v >= 4, "{ATN}", "{BAD}" ) ) )')
m("Cor Conversão", U, "", f'VAR _v = [Taxa Conversão %] RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v >= 0.04, "{OK}", IF ( _v >= 0.025, "{ATN}", "{BAD}" ) ) )')
m("Cor Nota", U, "", f'VAR _v = [% Avaliações Abaixo de 4] VAR _r = CALCULATE ( [% Avaliações Abaixo de 4], ALLSELECTED ( dProduto ) ) RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v <= _r, "{OK}", IF ( _v <= _r * 1.5, "{ATN}", "{BAD}" ) ) )',
  "Relativa à seleção: verde ≤ média, âmbar até 1,5× a média, coral acima.")
m("Cor Polaridade", U, "", f'IF ( SELECTEDVALUE ( dMotivoSatisfacao[Polaridade] ) = "negativo", "{BAD}", "{OK}" )')
m("Cor Resultado Digital", U, "", f'VAR _v = [Margem Resultado Digital %] RETURN IF ( ISBLANK ( _v ), "{NEU}", IF ( _v >= 0.2, "{OK}", IF ( _v >= 0.1, "{ATN}", "{BAD}" ) ) )')
m("Cor Destaque Receita Digital Mes", U, "", f"""
VAR _mx = CALCULATE ( MAXX ( VALUES ( dCalendario[AnoMes Num] ), [Receita Digital] ), ALLSELECTED ( dCalendario ) )
RETURN IF ( NOT ISBLANK ( [Receita Digital] ), IF ( [Receita Digital] = _mx, "{OK}", "#2E7F78" ) )""")
m("Cor Pilar", U, "", f'SWITCH ( SELECTEDVALUE ( dIniciativa[Pilar] ), "Conversão", "{OK}", "CX", "#DDF5EB", "Produto", "{ATN}", "Operação", "{BAD}", "#5FA8A0" )')
m("Txt Resultado Digital", U, "", 'IF ( ISBLANK ( [Custo Digital % Receita] ), "indisponível com filtro de canal/produto", "custos digitais = " & FORMAT ( [Custo Digital % Receita], "0.0%", "pt-BR" ) & " da receita · não é EBITDA" )')
m("Txt OTIF Meta", U, "", 'IF ( ISBLANK ( [OTIF Var pp] ), "alvo 95% (I08)", IF ( [OTIF Var pp] >= 0, "▲ +", "▼ −" ) & FORMAT ( ABS ( [OTIF Var pp] ), "0.0", "pt-BR" ) & " p.p. vs LY · alvo 95%" )')
m("Txt NPS", U, "", 'IF ( ISBLANK ( [NPS Var] ), "alvo +50 (I09)", IF ( [NPS Var] >= 0, "▲ +", "▼ −" ) & FORMAT ( ABS ( [NPS Var] ), "0.0", "pt-BR" ) & " pts vs LY · alvo +50" )')
m("Txt Prazo", U, "", '"prometido " & FORMAT ( [Prazo Prometido Médio], "0.0", "pt-BR" ) & " dias · atraso médio " & FORMAT ( [Atraso Médio Entrega], "0.0", "pt-BR" ) & " d"')
m("Txt Frete", U, "", 'FORMAT ( [% Frete Grátis], "0%", "pt-BR" ) & " dos pedidos com frete grátis"')
m("Txt Nota", U, "", 'FORMAT ( [% Avaliações Abaixo de 4], "0.0%", "pt-BR" ) & " abaixo de 4 · escala só 3–4 na base"')
m("Txt Novos Digitais", U, "", 'FORMAT ( [% Novos Digitais], "0%", "pt-BR" ) & " dos clientes digitais (1ª compra observada)"')
m("Txt Omni", U, "", '"também compram na loja física"')
m("Txt Conversão", U, "", 'IF ( ISBLANK ( [Conversão Var pp] ), "alvo-premissa 4,0%", IF ( [Conversão Var pp] >= 0, "▲ +", "▼ −" ) & FORMAT ( ABS ( [Conversão Var pp] ), "0.00", "pt-BR" ) & " p.p. vs LY" )')
m("Txt Checkout", U, "", 'FORMAT ( [Abandono Checkout %], "0%", "pt-BR" ) & " dos checkouts não fecham"')
m("Txt ATC", U, "", '"indicador isolado · base inconsistente"')
m("Txt Roadmap", U, "", 'FORMAT ( [Iniciativas Concluídas], "0" ) & " de " & FORMAT ( [Iniciativas], "0" ) & " concluídas em " & FORMAT ( [_Mes Roadmap], "mm/yyyy" )')
m("Txt Maturidade", U, "", '"média de 5 componentes vs alvo"')
m("Txt Lift", U, "", 'FORMAT ( [Experimentos Vencedores], "0" ) & " vencedores de " & FORMAT ( [Experimentos], "0" ) & " testes"')
m("Txt Custo Mídia", U, "", 'IF ( ISBLANK ( [Mídia % Receita Digital] ), "indisponível p/ este filtro", "mídia = " & FORMAT ( [Mídia % Receita Digital], "0.0%", "pt-BR" ) & " da receita digital" )')
m("Txt Share Digital", U, "", 'IF ( ISBLANK ( [Share Digital Var pp] ), "da receita da rede", IF ( [Share Digital Var pp] >= 0, "▲ +", "▼ −" ) & FORMAT ( ABS ( [Share Digital Var pp] ), "0.0", "pt-BR" ) & " p.p. vs ano anterior" )')
m("Cor Share Digital", U, "", f'IF ( ISBLANK ( [Share Digital Var pp] ), "{OK}", IF ( [Share Digital Var pp] >= 0, "{OK}", "{ATN}" ) )')

# Barras SVG (tabelas)
svg_bar("SVG Barra Receita Canal", "Receita Digital", "dCanal[Canal]")
svg_bar("SVG Barra Oportunidade SKU", "Score Oportunidade", "dProduto[Produto]", BAD)
svg_bar("SVG Barra Score Componente", "Score Componente", "dMaturidade[Componente]")
svg_bar("SVG Barra Sessões Origem", "Sessões", "dOrigemTrafego[Origem]")

# 09 Narrativas (texto puro + HTML)
N_ = "09 Narrativas"
m("Narrativa Digital Executiva", N_, "", """
VAR _r = [Receita Digital]
VAR _y = [Receita Digital YoY %]
VAR _s = [Share Digital %]
VAR _t = ADDCOLUMNS ( CALCULATETABLE ( VALUES ( dCanal[Canal] ), dCanal[Grupo Canal] = "Digital" ), "@r", [Receita Digital] )
VAR _top = TOPN ( 1, _t, [@r], DESC )
VAR _f1 = "Receita digital de R$ " & FORMAT ( _r / 1000000, "#,0.00", "pt-BR" ) & " mi (" & FORMAT ( _s, "0.0%", "pt-BR" ) & " da rede)"
    & IF ( ISBLANK ( _y ), ", sem período comparável completo no ano anterior.", ", " & IF ( _y >= 0, "alta", "queda" ) & " de " & FORMAT ( ABS ( _y ), "0.0%", "pt-BR" ) & " vs mesmo período do ano anterior." )
VAR _f2 = IF ( COUNTROWS ( _t ) > 1, " " & MAXX ( _top, dCanal[Canal] ) & " lidera com " & FORMAT ( DIVIDE ( MAXX ( _top, [@r] ), _r ), "0%", "pt-BR" ) & " do digital.", "" )
VAR _f3 = IF ( ISBLANK ( [Resultado Digital Simplificado] ), "", " Depois dos custos digitais diretos (" & FORMAT ( [Custo Digital % Receita], "0.0%", "pt-BR" ) & " da receita), sobra resultado simplificado de R$ " & FORMAT ( [Resultado Digital Simplificado] / 1000000, "#,0.00", "pt-BR" ) & " mi." )
RETURN IF ( ISBLANK ( _r ), "Sem vendas digitais para os filtros selecionados.", _f1 & _f2 & _f3 )""", "Fato derivado dos filtros. Não atribui causa.")
m("Narrativa Funil", N_, "", """
VAR _t = ADDCOLUMNS ( VALUES ( dDispositivo[Dispositivo] ), "@c", [Taxa Conversão %], "@s", [Sessões] )
VAR _pior = TOPN ( 1, FILTER ( _t, [@s] >= 0.03 * [Sessões] ), [@c], ASC )
VAR _melhor = TOPN ( 1, FILTER ( _t, [@s] >= 0.03 * [Sessões] ), [@c], DESC )
RETURN IF ( ISBLANK ( [Sessões] ), "Sem sessões para os filtros selecionados.",
    FORMAT ( [Sessões], "#,0", "pt-BR" ) & " sessões geraram " & FORMAT ( [Pedidos (Funil)], "#,0", "pt-BR" ) & " pedidos: conversão de " & FORMAT ( [Taxa Conversão %], "0.00%", "pt-BR" )
    & "; " & FORMAT ( [Abandono Checkout %], "0%", "pt-BR" ) & " dos checkouts não fecham."
    & IF ( COUNTROWS ( _t ) > 1, " Maior conversão: " & MAXX ( _melhor, dDispositivo[Dispositivo] ) & " (" & FORMAT ( MAXX ( _melhor, [@c] ), "0.00%", "pt-BR" ) & "); menor: "
        & MAXX ( _pior, dDispositivo[Dispositivo] ) & " (" & FORMAT ( MAXX ( _pior, [@c] ), "0.00%", "pt-BR" ) & ") — hipótese a testar: experiência no dispositivo.", "" ) )""")
m("Narrativa CX", N_, "", """
VAR _t = ADDCOLUMNS ( VALUES ( dMotivoSatisfacao[Motivo] ), "@n", CALCULATE ( [Respostas Pesquisa], dMotivoSatisfacao[Polaridade] = "negativo" ) )
VAR _top = TOPN ( 1, FILTER ( _t, [@n] > 0 ), [@n], DESC )
RETURN IF ( ISBLANK ( [Respostas Pesquisa] ), "Sem pesquisas para os filtros selecionados.",
    "NPS de " & FORMAT ( [NPS], "+0.0;-0.0", "pt-BR" ) & " (" & FORMAT ( [% Promotores], "0%", "pt-BR" ) & " promotores, " & FORMAT ( [% Detratores], "0%", "pt-BR" ) & " detratores) e CSAT de "
    & FORMAT ( [CSAT Médio], "0.00", "pt-BR" ) & ". OTIF de " & FORMAT ( [OTIF %], "0.0%", "pt-BR" ) & ", a " & FORMAT ( ( 0.95 - [OTIF %] ) * 100, "0.0", "pt-BR" ) & " p.p. do alvo de 95%."
    & IF ( COUNTROWS ( _top ) = 1, " Motivo negativo mais citado: " & MAXX ( _top, dMotivoSatisfacao[Motivo] ) & " (" & FORMAT ( DIVIDE ( MAXX ( _top, [@n] ), [Respostas Pesquisa] ), "0%", "pt-BR" ) & " das respostas).", "" ) )""")
m("Narrativa Produtos Digital", N_, "", """
VAR _c = ADDCOLUMNS ( VALUES ( dProduto[Categoria] ), "@p", [% Avaliações Abaixo de 4], "@a", [Avaliações] )
VAR _pior = TOPN ( 1, FILTER ( _c, [@a] >= 30 ), [@p], DESC )
VAR _sku = TOPN ( 1, ADDCOLUMNS ( VALUES ( dProduto[Produto] ), "@s", [Score Oportunidade] ), [@s], DESC )
RETURN IF ( ISBLANK ( [Avaliações] ), "Sem avaliações para os filtros selecionados.",
    FORMAT ( [Avaliações], "#,0", "pt-BR" ) & " avaliações, nota média " & FORMAT ( [Nota Média Produto], "0.00", "pt-BR" ) & " — a base só tem notas 3 e 4, então o sinal útil é o % abaixo de 4 ("
    & FORMAT ( [% Avaliações Abaixo de 4], "0.0%", "pt-BR" ) & ")."
    & IF ( COUNTROWS ( _pior ) = 1 && COUNTROWS ( _c ) > 1, " Maior insatisfação relativa: " & MAXX ( _pior, dProduto[Categoria] ) & " (" & FORMAT ( MAXX ( _pior, [@p] ), "0.0%", "pt-BR" ) & ").", "" )
    & IF ( NOT ISBLANK ( MAXX ( _sku, [@s] ) ) && MAXX ( _sku, [@s] ) > 0, " Primeiro SKU a investigar: " & MAXX ( _sku, dProduto[Produto] ) & ".", "" ) )""")
m("Narrativa Clientes Digitais", N_, "", """
IF ( ISBLANK ( [Clientes Digitais] ), "Sem clientes digitais identificados para os filtros selecionados.",
    FORMAT ( [Clientes Digitais], "#,0", "pt-BR" ) & " clientes compraram no digital (" & FORMAT ( [% Pedidos Digitais Identificados], "0%", "pt-BR" ) & " dos pedidos identificados), com "
    & FORMAT ( [Frequência Digital], "0.0", "pt-BR" ) & " pedidos por cliente e " & FORMAT ( [Recompra Digital %], "0%", "pt-BR" ) & " de recompra. "
    & FORMAT ( [% Clientes Omnichannel], "0%", "pt-BR" ) & " também compram na loja física: o cliente é omnichannel, não exclusivo do digital." )""")
m("Recomendações Priorizadas", N_, "", f"""
VAR _t = ADDCOLUMNS ( ALL ( dMaturidade[Ordem Componente], dMaturidade[Componente] ), "@g", 100 - [Score Componente] )
VAR _r = ADDCOLUMNS ( FILTER ( _t, [@g] > 0.5 ), "@k", RANKX ( FILTER ( _t, [@g] > 0.5 ), [@g],, DESC, DENSE ) )
VAR _txt = CONCATENATEX ( _r,
    "<li><b>" & dMaturidade[Componente] & "</b> · gap " & FORMAT ( [@g], "0", "pt-BR" ) & " pts — " &
    SWITCH ( dMaturidade[Ordem Componente],
        1, "conversão " & FORMAT ( [Taxa Conversão %], "0.00%", "pt-BR" ) & " vs 4%: atacar o pior dispositivo e o abandono de checkout (" & FORMAT ( [Abandono Checkout %], "0%", "pt-BR" ) & ").",
        2, "OTIF " & FORMAT ( [OTIF %], "0.0%", "pt-BR" ) & " vs 95%: revisar prazo prometido (I08), " & FORMAT ( [% Entregas com Atraso], "0.0%", "pt-BR" ) & " dos pedidos atrasam.",
        3, "NPS " & FORMAT ( [NPS], "+0;-0", "pt-BR" ) & " vs +50: tratar os motivos negativos mais citados antes de ampliar mídia.",
        4, "CSAT " & FORMAT ( [CSAT Médio], "0.00", "pt-BR" ) & " vs 4,5: atendimento e app (I02, I05).",
        5, "roadmap em " & FORMAT ( [% Conclusão Roadmap], "0%", "pt-BR" ) & ": destravar iniciativas planejadas (I06, I07, I10)." ) & "</li>",
    "", [@k], ASC )
RETURN "{V2.CSS_N.replace('"', '""')}<div class='n'><div class='h'>Recomendações priorizadas (maior gap primeiro)</div><ol style='margin:0;padding-left:18px;font-size:12.5px;line-height:1.5'>" & _txt & "</ol><div class='ft'>Gap = 100 − atingimento do alvo · alvos são premissas · priorização, não causalidade</div></div>" """)
m("Narrativa Estratégia", N_, "", """
"Maturidade digital " & FORMAT ( [Score Maturidade Digital], "0", "pt-BR" ) & "/100. Roadmap com " & FORMAT ( [% Conclusão Roadmap], "0%", "pt-BR" ) & " de conclusão média e "
    & FORMAT ( [Iniciativas Concluídas], "0" ) & " de " & FORMAT ( [Iniciativas], "0" ) & " iniciativas concluídas; " & FORMAT ( [Experimentos Vencedores], "0" ) & " de " & FORMAT ( [Experimentos], "0" )
    & " testes A/B venceram (lift médio " & FORMAT ( [Lift Médio Vencedores], "+0%", "pt-BR" ) & "). Lift de teste não soma: são métricas e períodos diferentes." """)
for p in ["Digital Executiva", "Funil", "CX", "Produtos Digital", "Clientes Digitais", "Estratégia"]:
    mi(f"HTML Narrativa {p}", N_, f'"{V2.CSS_N}<div class=\'n\'><div class=\'h\'>Leitura automática</div><div class=\'p\'>" & [Narrativa {p}] & "</div><div class=\'ft\'>Fato derivado dos filtros atuais · hipótese e ação a validar · não indica causa</div></div>"')

# Alerta de qualidade de dados (HTML)
CSS_A = ("<style>.a{font-family:Segoe UI,sans-serif;color:#E8F3F1;background:rgba(242,196,109,.10);border:1px solid rgba(242,196,109,.5);border-radius:12px;padding:10px 14px;height:100%;box-sizing:border-box}"
         ".a b{color:#F2C46D}.a p{margin:4px 0 0;font-size:11.5px;line-height:1.45}</style>")
mi("HTML Alerta Funil", N_, f'"{CSS_A}<div class=\'a\'><b>⚠ Qualidade da base</b><p>Add to cart (" & FORMAT ( [Add to Cart], "#,0", "pt-BR" ) & ") é menor que checkouts (" & FORMAT ( [Checkouts Iniciados], "#,0", "pt-BR" ) & ") em todos os meses. O funil usa Sessões → Checkout → Pedido; add to cart aparece só como taxa isolada.</p></div>"')
mi("HTML Alerta Reviews", N_, f'"{CSS_A}<div class=\'a\'><b>⚠ Qualidade da base</b><p>As avaliações só têm notas 3 e 4. A nota média quase não varia; use o % abaixo de 4 como sinal relativo. Não há base para afirmar baixa satisfação absoluta.</p></div>"')

# Tooltip HTML digital
mi("HTML Tooltip Digital", "11 SVG & HTML", f"""
VAR _r = [Receita Digital]
VAR _y = [Receita Digital YoY %]
VAR _c = IF ( ISBLANK ( _y ), "{NEU}", IF ( _y >= 0, "{OK}", "{BAD}" ) )
RETURN "<style>.tt{{font-family:Segoe UI,sans-serif;color:#E8F3F1;padding:4px}}.tt .l{{font-size:11px;color:#9FC9C1}}.tt .b{{font-size:22px;font-weight:600}}.tt .r{{display:flex;gap:16px;margin-top:8px}}.tt .s{{font-size:10px;color:#9FC9C1;margin-top:10px;border-top:1px solid rgba(255,255,255,.1);padding-top:6px;line-height:1.4}}</style>"
    & "<div class='tt'><div class='l'>Receita digital · " & [Período Selecionado] & "</div><div class='b'>" & {fmt("brl", "_r")} & " <span style='font-size:13px;color:" & _c & "'>" & IF ( ISBLANK ( _y ), "s/ base LY", FORMAT ( _y, "+0.0%;-0.0%", "pt-BR" ) & " vs LY" ) & "</span></div>"
    & "<div class='r'><div><div class='l'>Pedidos</div><b>" & FORMAT ( [Pedidos Digitais], "#,0", "pt-BR" ) & "</b></div>"
    & "<div><div class='l'>Ticket</div><b>R$ " & FORMAT ( [Ticket Médio Digital], "#,0.00", "pt-BR" ) & "</b></div>"
    & "<div><div class='l'>OTIF</div><b>" & FORMAT ( [OTIF %], "0.0%", "pt-BR" ) & "</b></div>"
    & "<div><div class='l'>NPS</div><b>" & FORMAT ( [NPS], "+0;-0", "pt-BR" ) & "</b></div></div>"
    & "<div class='s'>Receita digital = f_vendas nos canais Site, App e Delivery. "
    & IF ( [OTIF %] < 0.95, "Insight: OTIF abaixo do alvo de 95% — checar prazo prometido.", "Insight: OTIF no alvo." ) & "</div></div>" """)

# Chips de filtros (dimensões do relatório digital)
CHIPS = [("dCalendario[Ano]", "Ano"), ("dCalendario[Mes Nome]", "Mês"), ("dLoja[Loja]", "Loja"), ("dCanal[Canal]", "Canal"),
         ("dDispositivo[Dispositivo]", "Dispositivo"), ("dOrigemTrafego[Grupo Origem]", "Origem"), ("dProduto[Categoria]", "Categoria"),
         ("dCliente[Segmento RFV]", "RFV"), ("dIniciativa[Pilar]", "Pilar")]
mi("HTML Chips Filtros Digital", "11 SVG & HTML", "VAR _c = " + "\n    & ".join(V2.chip(c_, r_) for c_, r_ in CHIPS) +
   f'\nRETURN "{V2.CSS_CHIP}<div class=\'w\'>" & IF ( _c = "", "<span class=\'z\'>Canais digitais (Site · App · Delivery) · período completo 01/10/2024 a 30/09/2026</span>", _c ) & "</div>"')

# Cards HTML por página
P = {}
P["Home"] = [dict(t="Receita digital", v="Receita Digital", f="brl", sp="Receita Digital", sub="Site · App · Delivery · 24 meses"),
             dict(t="Share digital", v="Share Digital %", f="pct", sp="Share Digital %", sub="da receita da rede"),
             dict(t="Conversão", v="Taxa Conversão %", f="pct2", sp="Taxa Conversão %", sub="pedidos ÷ sessões", cor="Cor Conversão"),
             dict(t="NPS", v="NPS", f="nps", sp="NPS", sub="promotores − detratores", cor="Cor NPS"),
             dict(t="OTIF", v="OTIF %", f="pct", sp="OTIF %", sub="entregue no prazo prometido", cor="Cor OTIF")]
P["Executiva"] = [dict(t="Receita digital", v="Receita Digital", f="brl", var="Receita Digital YoY %", sp="Receita Digital"),
                  dict(t="Lucro bruto digital", v="Lucro Bruto Digital", f="brl", var="Lucro Bruto Digital YoY %", sp="Lucro Bruto Digital"),
                  dict(t="Margem bruta digital", v="Margem Bruta Digital %", f="pct", var="Margem Digital Var pp", vk="pp", sp="Margem Bruta Digital %"),
                  dict(t="Resultado digital simplificado", v="Resultado Digital Simplificado", f="brl", var="Txt Resultado Digital", vk="txt", cor="Cor Resultado Digital", sp="Resultado Digital Simplificado"),
                  dict(t="Share digital", v="Share Digital %", f="pct", var="Txt Share Digital", vk="txt", cor="Cor Share Digital", sp="Share Digital %"),
                  dict(t="Ticket médio digital", v="Ticket Médio Digital", f="brl2", var="Ticket Digital YoY %", sp="Ticket Médio Digital")]
P["Funil"] = [dict(t="Sessões", v="Sessões", f="int", var="Sessões YoY %", sp="Sessões"),
              dict(t="Conversão", v="Taxa Conversão %", f="pct2", var="Txt Conversão", vk="txt", cor="Cor Conversão", sp="Taxa Conversão %"),
              dict(t="Taxa de checkout", v="Taxa Checkout %", f="pct", sp="Taxa Checkout %", sub="checkouts ÷ sessões"),
              dict(t="Checkout → pedido", v="Checkout → Pedido %", f="pct", var="Txt Checkout", vk="txt", cor="Txt Neutro", sp="Checkout → Pedido %"),
              dict(t="Taxa de add to cart", v="Taxa Add to Cart %", f="pct", var="Txt ATC", vk="txt", cor="Txt Neutro", sp="Taxa Add to Cart %"),
              dict(t="Receita por sessão", v="Receita por Sessão", f="brl2", sp="Receita por Sessão", sub="receita digital ÷ sessões")]
P["CX"] = [dict(t="NPS", v="NPS", f="nps", var="Txt NPS", vk="txt", cor="Cor NPS", sp="NPS"),
           dict(t="CSAT médio", v="CSAT Médio", f="dec", sp="CSAT Médio", sub="escala 1 a 5 · alvo 4,5", cor="Cor CSAT"),
           dict(t="OTIF", v="OTIF %", f="pct", var="Txt OTIF Meta", vk="txt", cor="Cor OTIF", sp="OTIF %"),
           dict(t="Prazo real médio", v="Prazo Real Médio", f="dias1", var="Txt Prazo", vk="txt", cor="Txt Neutro", sp="Prazo Real Médio"),
           dict(t="Entregas com atraso", v="% Entregas com Atraso", f="pct", sp="% Entregas com Atraso", sub="pedidos digitais", cor="Cor OTIF"),
           dict(t="Frete médio", v="Frete Médio", f="brl2", var="Txt Frete", vk="txt", cor="Txt Neutro", sp="Frete Médio")]
P["Produtos"] = [dict(t="Avaliações", v="Avaliações", f="int", sp="Avaliações", sub="reviews de compras digitais"),
                 dict(t="Nota média", v="Nota Média Produto", f="dec", var="Txt Nota", vk="txt", cor="Txt Neutro", sp="Nota Média Produto"),
                 dict(t="Avaliações abaixo de 4", v="% Avaliações Abaixo de 4", f="pct", sp="% Avaliações Abaixo de 4", sub="sinal relativo de insatisfação", cor="Txt Neutro"),
                 dict(t="Receita digital (itens)", v="Receita Digital Itens", f="brl", sp="Receita Digital Itens", sub="f_itens_venda · canais digitais"),
                 dict(t="Margem digital (itens)", v="Margem Digital Itens %", f="pct", sp="Margem Digital Itens %", sub="receita − CMV de itens"),
                 dict(t="SKUs vendidos no digital", v="SKUs Digitais Vendidos", f="int", sp="SKUs Digitais Vendidos", sub="de 5.000 no catálogo")]
P["Clientes"] = [dict(t="Clientes digitais", v="Clientes Digitais", f="int", var="Clientes Digitais YoY %", sp="Clientes Digitais"),
                 dict(t="Novos no digital", v="Clientes Digitais Novos", f="int", var="Txt Novos Digitais", vk="txt", cor="Txt Neutro", sp="Clientes Digitais Novos"),
                 dict(t="Recompra digital", v="Recompra Digital %", f="pct", sp="Recompra Digital %", sub="2+ pedidos digitais no período"),
                 dict(t="Frequência digital", v="Frequência Digital", f="dec", sp="Frequência Digital", sub="pedidos por cliente"),
                 dict(t="Ticket identificado", v="Ticket Digital Identificado", f="brl2", sp="Ticket Digital Identificado", sub="clientes identificados"),
                 dict(t="Clientes omnichannel", v="% Clientes Omnichannel", f="pct", var="Txt Omni", vk="txt", cor="Txt Neutro", sp="% Clientes Omnichannel")]
P["Estratégia"] = [dict(t="Maturidade digital", v="Score Maturidade Digital", f="int", var="Txt Maturidade", vk="txt", cor="Cor Score"),
                   dict(t="Conclusão do roadmap", v="% Conclusão Roadmap", f="pct", var="Txt Roadmap", vk="txt", cor="Txt Neutro", sp="% Conclusão Roadmap"),
                   dict(t="Iniciativas em andamento", v="Iniciativas Em Andamento", f="int", sub="snapshot do último mês"),
                   dict(t="Testes A/B vencedores", v="Taxa de Vitória Testes %", f="pct", var="Txt Lift", vk="txt", cor="Txt Neutro"),
                   dict(t="Lift médio (vencedores)", v="Lift Médio Vencedores", f="pct", sub="métricas diferentes · não somar"),
                   dict(t="Mídia por cliente novo", v="Mídia por Cliente Novo (proxy CAC)", f="brl2", var="Txt Custo Mídia", vk="txt", cor="Txt Neutro", sp="Mídia por Cliente Novo (proxy CAC)")]
for k, cards in P.items():
    html_cards(f"HTML KPIs Ecom {k}", "11 SVG & HTML", cards)

# 99 Auditoria — reconciliação com RESUMO_ECOM.json
A = "99 Auditoria"
REF = [("Pedidos Digitais", 40029, INT), ("Receita Digital", 9774295.05, BRL), ("Pedidos Entrega", 40029, INT), ("Sessões", 1274133, INT),
       ("Pedidos (Funil)", 40029, INT), ("Avaliações", 13324, INT), ("Respostas Pesquisa", 7482, INT), ("Custo Digital Total", 1736490.06, BRL)]
for n_, v_, f_ in REF:
    m(f"Check {n_}", A, f_, f"CALCULATE ( [{n_}], REMOVEFILTERS () ) - {v_}", f"Deve ser 0 (RESUMO_ECOM.json: {v_}).")
m("Check OTIF 87,8%", A, PP, "ROUND ( CALCULATE ( [OTIF %], REMOVEFILTERS () ) * 100, 1 ) - 87.8")
m("Check NPS +5,9", A, NPSF, "ROUND ( CALCULATE ( [NPS], REMOVEFILTERS () ), 1 ) - 5.9")
m("Check CSAT 4,41", A, DEC2, "ROUND ( CALCULATE ( [CSAT Médio], REMOVEFILTERS () ), 2 ) - 4.41")
m("Check Nota 3,98", A, DEC2, "ROUND ( CALCULATE ( [Nota Média Produto], REMOVEFILTERS () ), 2 ) - 3.98")
m("Check Conversão 3,14%", A, PP, "ROUND ( CALCULATE ( [Taxa Conversão %], REMOVEFILTERS () ) * 100, 2 ) - 3.14")
m("Check Pedidos Funil vs Vendas", A, INT, "[Pedidos (Funil)] - [Pedidos Digitais]", "Deve ser 0 em qualquer filtro de data, loja e canal.")
m("Check Pedidos Entrega vs Vendas", A, INT, "[Pedidos Entrega] - [Pedidos Digitais]", "Deve ser 0 em qualquer filtro de data, loja, canal e cliente.")
m("Check Receita Digital Cupom vs Itens", A, BRL, "[Receita Digital] - [Receita Digital Itens]", "Deve ser ~0 sem filtro de produto.")

# nomes duplicados?
_n = [x["n"] for x in MED]
assert len(_n) == len(set(_n)), [x for x in _n if _n.count(x) > 1]

# ================================================================ 6. mini painéis HTML (preenchem os blocos de narrativa)
CSS_MP = ("<style>.mp{font-family:Segoe UI,sans-serif;color:#E8F3F1;height:100%;box-sizing:border-box;border-top:1px solid rgba(255,255,255,.08);padding-top:10px;animation:f .6s ease both}"
          ".mp .h{font-size:12.5px;font-weight:600;color:#DDF5EB;margin-bottom:8px}.mp .r{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:11.5px}"
          ".mp .l{width:112px;color:#9FC9C1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mp .b{flex:1;height:9px;border-radius:5px;background:rgba(255,255,255,.07);overflow:hidden}"
          ".mp .b i{display:block;height:100%;border-radius:5px;animation:g 1s ease both}.mp .v{width:150px;text-align:right;white-space:nowrap}"
          ".mp .ft{font-size:10.5px;color:#9FC9C1;margin-top:8px}.mp .ft b{color:#18B89F}"
          "@keyframes g{from{width:0}}@keyframes f{from{opacity:0}to{opacity:1}}</style>")
def _row(lbl, v_expr, pct_expr, cor, txt_expr):
    return (f'"<div class=\'r\'><span class=\'l\'>{lbl}</span><span class=\'b\'><i style=\'width:" & FORMAT ( MIN ( 1, MAX ( 0, {pct_expr} ) ) * 100, "0.0", "en-US" ) & "%;background:{cor}\'></i></span><span class=\'v\'>" & {txt_expr} & "</span></div>"')
def mini(nome, titulo, vars_, rows, ft, guard=None, msg="Sem dados para os filtros selecionados."):
    body = "\n".join(vars_) + "\nRETURN " + (f'IF ( {guard}, "{CSS_MP}<div class=\'mp\'><div class=\'ft\'>{msg}</div></div>", ' if guard else "") + \
        f'"{CSS_MP}<div class=\'mp\'><div class=\'h\'>{titulo}</div>" & ' + " & ".join(rows) + f' & "<div class=\'ft\'>" & {ft} & "</div></div>"' + (" )" if guard else "")
    mi(nome, "09 Narrativas", body)

R_ = lambda v: f'"R$ " & FORMAT ( {v} / 1000, "#,0", "pt-BR" ) & " mil"'
mini("HTML Custos Digitais", "Para onde vai o custo digital",
     ["VAR _t = [Custo Digital Total]", "VAR _r = [Receita Digital]"],
     [_row(n, f"[{m_}]", f"DIVIDE ( [{m_}], _t )", c, R_(f"[{m_}]") + f' & " · " & FORMAT ( DIVIDE ( [{m_}], _r ), "0.0%", "pt-BR" )')
      for n, m_, c in [("Mídia paga", "Custo Mídia Paga", BAD), ("Fulfillment", "Custo Fulfillment", ATN), ("Plataforma", "Custo Plataforma", "#DDF5EB"), ("Outros", "Outros Custos Digitais", "#5FA8A0")]],
     '"ROAS proxy <b>" & FORMAT ( [ROAS Proxy], "0.0", "pt-BR" ) & "x</b> · custo por pedido <b>R$ " & FORMAT ( [Custo por Pedido Digital], "#,0.00", "pt-BR" ) & "</b> · valor · % da receita digital"',
     guard="ISBLANK ( _t )", msg="Custos digitais são por loja × mês: indisponíveis com filtro de canal, produto ou cliente.")
mini("HTML Status Entrega", "Como os pedidos chegam",
     ["VAR _p = [Pedidos Entrega]"],
     [_row(n, "0", f'DIVIDE ( CALCULATE ( [Pedidos Entrega], fPedidosDigitais[Status Entrega] = "{s}" ), _p )', c,
           f'FORMAT ( CALCULATE ( [Pedidos Entrega], fPedidosDigitais[Status Entrega] = "{s}" ), "#,0", "pt-BR" ) & " · " & FORMAT ( DIVIDE ( CALCULATE ( [Pedidos Entrega], fPedidosDigitais[Status Entrega] = "{s}" ), _p ), "0.0%", "pt-BR" )')
      for n, s, c in [("No prazo", "Entregue no prazo", OK), ("Com atraso", "Entregue com atraso", ATN), ("Cancelado/problema", "Cancelado / Problema", BAD)]],
     '"frete grátis em <b>" & FORMAT ( [% Frete Grátis], "0%", "pt-BR" ) & "</b> dos pedidos · taxa de resposta da pesquisa <b>" & FORMAT ( [Taxa de Resposta %], "0.0%", "pt-BR" ) & "</b>"',
     guard="ISBLANK ( _p )")
FX = [("1 pedido", "[@n] = 1"), ("2 a 3 pedidos", "[@n] >= 2 && [@n] <= 3"), ("4 a 6 pedidos", "[@n] >= 4 && [@n] <= 6"), ("7 ou mais", "[@n] >= 7")]
mini("HTML Frequência Clientes", "Quantas vezes o cliente volta ao digital",
     [f'VAR _c = ADDCOLUMNS ( CALCULATETABLE ( VALUES ( fVendas[id_cliente] ), {DIG}, fVendas[cliente_identificado] = TRUE () ), "@n", CALCULATE ( COUNTROWS ( fVendas ), {DIG} ) )',
      "VAR _t = COUNTROWS ( _c )"] + [f"VAR _f{i} = COUNTROWS ( FILTER ( _c, {cond} ) ) + 0" for i, (_, cond) in enumerate(FX)],
     [_row(n, "0", f"DIVIDE ( _f{i}, _t )", [NEU, "#5FA8A0", OK, "#DDF5EB"][i], f'FORMAT ( _f{i}, "#,0", "pt-BR" ) & " · " & FORMAT ( DIVIDE ( _f{i}, _t ), "0%", "pt-BR" )')
      for i, (n, _) in enumerate(FX)],
     '"pedidos digitais por cliente identificado no período · base: " & FORMAT ( _t, "#,0", "pt-BR" ) & " clientes"', guard="_t = 0")
mi("HTML Próximos Marcos", "09 Narrativas", f"""
VAR _m = [_Mes Roadmap]
VAR _t = FILTER ( ADDCOLUMNS ( VALUES ( dIniciativa[Iniciativa] ), "@p", [% Conclusão Roadmap], "@tri", CALCULATE ( MAX ( dIniciativa[Trimestre Alvo] ) ), "@pil", CALCULATE ( MAX ( dIniciativa[Pilar] ) ) ), [@p] < 1 )
VAR _l = CONCATENATEX ( TOPN ( 5, _t, [@tri], ASC, [@p], ASC ),
    "<div class='r'><span class='l'>" & dIniciativa[Iniciativa] & "</span><span class='b'><i style='width:" & FORMAT ( [@p] * 100, "0", "en-US" ) & "%;background:" & IF ( [@p] < 0.3, "{BAD}", IF ( [@p] < 0.7, "{ATN}", "{OK}" ) ) & "'></i></span><span class='v'>" & FORMAT ( [@p], "0%", "pt-BR" ) & " · alvo " & [@tri] & "</span></div>",
    "", [@tri], ASC, [@p], ASC )
RETURN "{CSS_MP}<div class='mp'><div class='h'>Próximos marcos: iniciativas abertas por prazo</div>" & IF ( COUNTROWS ( _t ) = 0, "<div class='ft'>Todas as iniciativas do filtro estão concluídas.</div>", _l )
    & "<div class='ft'>" & FORMAT ( COUNTROWS ( _t ), "0" ) & " iniciativas abertas em " & FORMAT ( _m, "mm/yyyy" ) & " · coral &lt; 30% · âmbar &lt; 70%</div></div>" """)
mi("HTML Experimentos", "09 Narrativas", f"""
VAR _t = SUMMARIZE ( FILTER ( fExperimentosAB, fExperimentosAB[Resultado Teste] <> "baseline" ), fExperimentosAB[Experimento], fExperimentosAB[Métrica Teste], fExperimentosAB[Resultado Teste], fExperimentosAB[lift] )
VAR _mx = MAXX ( _t, fExperimentosAB[lift] )
VAR _l = CONCATENATEX ( _t,
    "<div class='r'><span class='l'>" & fExperimentosAB[Experimento] & "</span><span class='b'><i style='width:" & FORMAT ( DIVIDE ( fExperimentosAB[lift], _mx ) * 100, "0", "en-US" ) & "%;background:" & IF ( fExperimentosAB[Resultado Teste] = "vencedor", "{OK}", "{ATN}" ) & "'></i></span><span class='v'>" & FORMAT ( fExperimentosAB[lift], "+0%", "pt-BR" ) & " · " & SUBSTITUTE ( fExperimentosAB[Métrica Teste], "_", " " ) & "</span></div>",
    "", fExperimentosAB[lift], DESC )
RETURN "{CSS_MP}<div class='mp'><div class='h'>Testes A/B: lift da variante B por métrica</div>" & _l & "<div class='ft'>turquesa = venceu · âmbar = empatou · cada lift mede uma métrica diferente</div></div>" """)
mi("SVG Barra Receita Canal Loja", "11 SVG & HTML", """
VAR _v = [Receita Digital]
VAR _mx = MAXX ( CROSSJOIN ( ALLSELECTED ( dCanal[Canal] ), ALLSELECTED ( dLoja[Loja Curta] ) ), CALCULATE ( [Receita Digital] ) )
VAR _w = IF ( _mx > 0, MAX ( 2, DIVIDE ( _v, _mx ) * 116 ), 0 )
RETURN IF ( NOT ISBLANK ( _v ),
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='18'><rect x='0' y='5' width='120' height='8' rx='4' fill='%23FFFFFF' fill-opacity='0.08'/><rect x='0' y='5' width='" & FORMAT ( _w, "0", "en-US" ) & "' height='8' rx='4' fill='%2318B89F'/></svg>" )""", "Barra SVG relativa ao maior canal × loja da seleção.", cat="ImageUrl")
