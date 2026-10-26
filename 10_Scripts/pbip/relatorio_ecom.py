# -*- coding: utf-8 -*-
"""FarmaVitta E-commerce Intelligence — relatório PBIR no padrão visual da v2 (tema escuro, menu lateral em vidro,
cards HTML Content + SVG, Deneb, painel de filtros oculto por bookmarks, chips, tooltip HTML)."""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import relatorio as R
import relatorio_v2 as V
import deneb_specs as DS
import deneb_ecom  # noqa: F401  (registra os specs)
from relatorio import L, N, COL, M, CLM, P, PS, proj, Page, hid, SCH
from relatorio_v2 import K, FONT, FONTB, NONE, tb, html, deneb, bar, table, matrix, button, slicer, nav_link, bm_link, inner, glass, fundo_base, logo_negativo

W, H = V.W, V.H
SB, TOP, KPI, MAIN, R1, R2, B1, B2, B3, FP = V.SB, V.TOP, V.KPI, V.MAIN, V.R1, V.R2, V.B1, V.B2, V.B3, V.FP
B23, R12 = V.B23, V.R12
NAV_Y0, NAV_H, NAV_GAP = V.NAV_Y0, V.NAV_H, V.NAV_GAP

PAGES = [("home", "Home E-com"), ("exec", "Visão Executiva Digital"), ("funil", "Funil & Conversão"), ("cx", "Experiência do Cliente"),
         ("prod", "Produtos & Desenvolvimento"), ("cli", "Clientes & Retenção"), ("estr", "Estratégia de Evolução")]
SUBT = {"exec": "Quanto o digital vende, com que margem e quanto sobra depois dos custos digitais",
        "funil": "Sessões → checkout → pedido por dispositivo, origem e canal",
        "cx": "NPS, CSAT, motivos e entrega no prazo (OTIF)",
        "prod": "Reviews, insatisfação relativa e oportunidades por SKU",
        "cli": "Clientes digitais, recompra, omnichannel e coortes",
        "estr": "Roadmap, testes A/B, maturidade digital e prioridades"}
PANELS = {"exec": [MAIN, R1, R2, B1, B23], "funil": [MAIN, R1, R2, B1, B2, B3], "cx": [MAIN, R12, B1, B2, B3],
          "prod": [MAIN, R1, R2, B1, B23], "cli": [MAIN, R1, R2, B1, B23], "estr": [MAIN, R1, R2, B1, B2, B3]}

def digital_filter(pg_key):
    return {"name": hid("flt", pg_key, "digital"), "field": CLM("dCanal", "Grupo Canal"), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "c", "Entity": "dCanal", "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Grupo Canal"}}],
                                                       "Values": [[{"Literal": {"Value": "'Digital'"}}]]}}}]},
            "isLockedInViewMode": True}

def line_dark(pg, key, box, cat, measure, series, title, sub=None):
    x, y, w, h = inner(box, 6)
    obj = {"lineStyles": [P(strokeWidth=N(2), showMarker=L(True), markerSize=N(3))],
           "legend": [P(show=L(True), position=L("Top"), fontSize=N(9), labelColor=COL(K["texto"]))],
           "valueAxis": [P(show=L(True), fontSize=N(9), labelColor=COL(K["sub"]), gridlineColor=COL("#1B4A51"), gridlineStyle=L("dotted"))],
           "categoryAxis": [P(show=L(True), fontSize=N(9), labelColor=COL(K["sub"]))],
           "labels": [P(show=L(False))],
           "dataPoint": [PS({"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": {"Column": {"Expression": {"SourceRef": {"Entity": "dCanal"}}, "Property": "Canal"}},
                                                         "Right": {"Literal": {"Value": f"'{c}'"}}}}}]}, fill=COL(cl))
                         for c, cl in [("Aplicativo", K["turquesa"]), ("Site", K["menta"]), ("Delivery", K["ambar"])]]}
    pg.add(key, "lineChart", x, y, w, h, query={"Category": [cat], "Y": [M(measure)], "Series": [series]}, objects=obj,
           vco=dict(NONE, **V.vtitle(title, sub)), sort=[(cat, "Ascending")])

def build():
    pages = {k: Page(k, d, bg=f"ecom_{k}.png") for k, d in PAGES}
    tt = Page("tt_digital", "TT Digital", w=420, h=220, tooltip=True, hidden=True)
    html(tt, "tt_html", (6, 6, 408, 208), "HTML Tooltip Digital"); tt.bg = None
    bookmarks = []
    D, Lj, Pr, Cl, Ca = "dCalendario", "dLoja", "dProduto", "dCliente", "dCanal"
    Dv, Og, Mo, In, Et, Ma = "dDispositivo", "dOrigemTrafego", "dMotivoSatisfacao", "dIniciativa", "dEtapaFunil", "dMaturidade"
    mes, ordm = (CLM(D, "Mes Ano"), "mes"), (CLM(D, "AnoMes Num"), "ord")

    def chrome(pg):
        for i, (k, d) in enumerate(PAGES):
            y = NAV_Y0 + i * (NAV_H + NAV_GAP); act = k == pg.key
            button(pg, f"nav_{k}", (28, y, 176, NAV_H), ("●  " if act else "    ") + d, nav_link(pages[k]), 50000 + i,
                   fill=K["petroleo2"] if act else None, fill_hover="#1A6E6F", color=K["turquesa"] if act else K["texto"], size=10, align="left",
                   tooltip=SUBT.get(k, "Página inicial"))
        tb(pg, "titulo", (TOP[0] + 20, 22, 600, 60), [[(pg.display, 15, K["branco"], True)], [(SUBT[pg.key], 9, K["sub"], False)]], z=49000)
        html(pg, "chips", (870, 26, 820, 52), "HTML Chips Filtros Digital", z=49001)
        button(pg, "btn_filtros", (1724, 30, 164, 44), "⚲  Filtros", bm_link(hid("bm", pg.key, "abrir")), 49002,
               fill=K["turquesa"], fill_hover="#21D1B4", color=K["fundo"], size=11, tooltip="Abrir painel de filtros")

    def painel(pg, extra):
        names = []; x, y, w, h = FP
        shp = pg.add("fp_bg", "shape", x, y, w, h, objects={"shape": [P(tileShape=L("rectangleRounded"), roundEdge=N(16))],
                                                            "fill": [P(show=L(False))], "outline": [P(show=L(False))]},
                     vco={"background": [P(show=L(True), color=COL("#0A262C"), transparency=N(2))],
                          "border": [P(show=L(True), color=COL(K["turquesa"]), radius=N(16), width=N(1))],
                          "dropShadow": [P(show=L(True), color=COL("#000000"), transparency=N(40), position=L("Outer"), preset=L("Custom"),
                                           shadowBlur=N(30), shadowDistance=N(0), shadowSpread=N(4))],
                          "title": [P(show=L(False))]}, z=70000)
        shp["isHidden"] = True; names.append(shp)
        names.append(tb(pg, "fp_t", (x + 24, y + 18, w - 90, 56), [[("Filtros", 16, K["branco"], True)], [("Sincronizados entre as páginas · só canais digitais", 9, K["sub"], False)]], z=70010, hidden=True))
        names.append(button(pg, "fp_x", (x + w - 56, y + 18, 36, 36), "✕", bm_link(hid("bm", pg.key, "fechar")), 70020, fill_hover="#1A6E6F", size=12, hidden=True, tooltip="Fechar"))
        campos = [(D, "Ano", "Ano"), (D, "Mes Nome", "Mês"), (Lj, "Loja", "Loja")] + extra
        for i, (ent, prop, lab) in enumerate(campos):
            names.append(slicer(pg, f"fp_s{i}", (x + 24, y + 92 + i * 84, w - 48, 72), ent, prop, lab, hidden=True, z=70100 + i))
        names.append(button(pg, "fp_ok", (x + 24, y + h - 76, (w - 64) // 2 + 20, 48), "Aplicar e fechar", bm_link(hid("bm", pg.key, "fechar")), 70200,
                            fill=K["turquesa"], fill_hover="#21D1B4", color=K["fundo"], hidden=True))
        names.append(button(pg, "fp_clear", (x + 44 + (w - 64) // 2 + 20, y + h - 76, (w - 64) // 2 - 20, 48), "Limpar", {"type": L("ClearAllSlicers")}, 70201,
                            outline=K["turquesa"], fill_hover="#1A6E6F", color=K["turquesa"], hidden=True, tooltip="Limpar as segmentações do painel"))
        for estado in ("abrir", "fechar"):
            vcs = {}
            for v in names:
                sv = {"visualType": v["visual"]["visualType"]}
                if estado == "fechar": sv["display"] = {"mode": "hidden"}
                vcs[v["name"]] = {"singleVisual": sv}
            bookmarks.append({"$schema": f"{SCH}/bookmark/1.4.0/schema.json", "displayName": f"{pg.display} · filtros {estado}",
                              "name": hid("bm", pg.key, estado),
                              "options": {"applyOnlyToTargetVisuals": True, "targetVisualNames": [v["name"] for v in names], "suppressData": True},
                              "explorationState": {"version": "1.3", "activeSection": pg.name, "sections": {pg.name: {"visualContainers": vcs}}},
                              "_grupo": pg.display})

    # ---------------- HOME
    pg = pages["home"]
    tb(pg, "h1", (120, 300, 1000, 50), [[("FarmaVitta E-commerce Intelligence", 22, K["menta"], False)]])
    tb(pg, "h2", (120, 350, 1200, 80), [[("O digital da rede, do clique à entrega.", 38, K["branco"], True)]])
    tb(pg, "h3", (120, 432, 1000, 60), [[("Site, Aplicativo e Delivery das 4 farmácias: vendas, funil, experiência do cliente, produtos, retenção e evolução digital.", 14, K["sub"], False)]])
    button(pg, "iniciar", (120, 512, 240, 60), "Iniciar  ›", nav_link(pages["exec"]), 60000, fill=K["turquesa"], fill_hover="#21D1B4",
           color=K["fundo"], size=15, tooltip="Começar pela Visão Executiva Digital")
    html(pg, "h_kpis", (120, 636, 1680, 150), "HTML KPIs Ecom Home")
    for i, (k, d) in enumerate(PAGES[1:]):
        button(pg, f"atalho_{k}", (120 + i * 284, 830, 268, 64), d + "  ›", nav_link(pages[k]), 60100 + i,
               fill="#0E3138", fill_hover="#1A6E6F", color=K["menta"], size=11, outline="#1F5A60", tooltip=SUBT[k])
    tb(pg, "h4", (120, 990, 1680, 40), [[("Dados 100% fictícios para portfólio · 01/10/2024 a 30/09/2026 · receita sempre de f_vendas · resultado digital simplificado não é EBITDA · alertas de qualidade da base nas páginas Funil e Produtos.", 10, K["sub"], False)]])

    # ---------------- EXECUTIVA DIGITAL
    pg = pages["exec"]; chrome(pg); painel(pg, [(Ca, "Canal", "Canal")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom Executiva")
    deneb(pg, "d_rec", MAIN, [mes, ordm, (M("Receita Digital"), "receita"), (M("Receita Digital LY"), "ly"), (M("Share Digital %"), "share"),
                              (M("Cor Destaque Receita Digital Mes"), "cor")], "ecom_receita",
          "Receita digital mensal", "Barra = realizado (destaque: maior mês) · linha clara = ano anterior · tracejado âmbar = share digital (eixo direito)")
    bar(pg, "canal", R1, CLM(Ca, "Canal"), ["Receita Digital"], "Receita digital por canal", tooltip_page=tt)
    bar(pg, "loja", R2, CLM(Lj, "Loja Curta"), ["Receita Digital"], "Receita digital por loja", color=K["petroleo2"], tooltip_page=tt)
    x, y, w, h = inner(B1, 14)
    html(pg, "narr", (x, y, w, 132), "HTML Narrativa Digital Executiva")
    html(pg, "mini", (x, y + 136, w, h - 136), "HTML Custos Digitais")
    table(pg, "tab", B23, [proj(CLM(Ca, "Canal")), proj(CLM(Lj, "Loja Curta"), "Loja"), proj(M("SVG Barra Receita Canal Loja"), "Receita"), proj(M("Receita Digital"), "Receita (R$)"),
                           proj(M("Share Canal no Digital %"), "Part."), proj(M("Receita Digital YoY %"), "vs LY"), proj(M("Pedidos Digitais"), "Pedidos"),
                           proj(M("Ticket Médio Digital"), "Ticket"), proj(M("Margem Bruta Digital %"), "Margem"), proj(M("Taxa Conversão %"), "Conversão"),
                           proj(M("OTIF %"), "OTIF"), proj(M("NPS"), "NPS")],
          "Canais digitais × loja", sub="Receita e margem: f_vendas · conversão: sessões · OTIF: pedidos digitais · NPS: pesquisas",
          sort=[(M("Receita Digital"), "Descending")])

    # ---------------- FUNIL
    pg = pages["funil"]; chrome(pg); painel(pg, [(Ca, "Canal", "Canal"), (Dv, "Dispositivo", "Dispositivo"), (Og, "Grupo Origem", "Origem")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom Funil")
    deneb(pg, "d_funil", MAIN, [(CLM(Et, "Etapa"), "etapa"), (CLM(Et, "Ordem Etapa"), "ord"), (M("Valor Etapa Funil"), "val")], "ecom_funil",
          "Funil digital", "Add to cart fora do funil: na base ele é menor que o checkout (ver alerta)")
    bar(pg, "disp", R1, CLM(Dv, "Dispositivo"), ["Taxa Conversão %"], "Conversão por dispositivo", "verde ≥ 4% · âmbar ≥ 2,5% · coral abaixo", cor_measure="Cor Conversão")
    bar(pg, "orig", R2, CLM(Og, "Grupo Origem"), ["Taxa Conversão %"], "Conversão por grupo de origem", cor_measure="Cor Conversão")
    x, y, w, h = inner(B1, 14)
    html(pg, "narr", (x, y, w, h - 118), "HTML Narrativa Funil")
    html(pg, "alerta", (x, y + h - 108, w, 108), "HTML Alerta Funil")
    line_dark(pg, "conv_mes", B2, CLM(D, "Mes Ano"), "Taxa Conversão %", CLM(Ca, "Canal"), "Conversão mensal por canal")
    table(pg, "tab", B3, [proj(CLM(Og, "Origem")), proj(M("SVG Barra Sessões Origem"), "Sessões"), proj(M("Sessões"), "Sessões (n)"),
                          proj(M("Pedidos (Funil)"), "Pedidos"), proj(M("Taxa Conversão %"), "Conv."), proj(M("Checkout → Pedido %"), "Chk→Ped")],
          "Origens de tráfego", sort=[(M("Sessões"), "Descending")])

    # ---------------- CX
    pg = pages["cx"]; chrome(pg); painel(pg, [(Ca, "Canal", "Canal"), (Mo, "Eixo", "Eixo do motivo"), (Mo, "Polaridade", "Polaridade")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom CX")
    deneb(pg, "d_nps", MAIN, [mes, ordm, (M("% Promotores"), "prom"), (M("% Neutros"), "neu"), (M("% Detratores"), "det"), (M("NPS"), "nps"),
                              (M("Respostas Pesquisa"), "resp")], "ecom_nps",
          "Composição do NPS por mês", "Barras = % promotores / neutros / detratores · linha âmbar = NPS (eixo direito)")
    bar(pg, "motivos", R12, CLM(Mo, "Motivo"), ["Respostas Pesquisa"], "Motivo principal declarado", "turquesa = elogio · coral = reclamação", cor_measure="Cor Polaridade")
    x, y, w, h = inner(B1, 14)
    html(pg, "narr", (x, y, w, 132), "HTML Narrativa CX")
    html(pg, "mini", (x, y + 136, w, h - 136), "HTML Status Entrega")
    deneb(pg, "d_otif", B2, [(CLM(Lj, "Loja Curta"), "loja"), (CLM(Ca, "Canal"), "canal"), (M("OTIF %"), "otif"), (M("Pedidos Entrega"), "ped"), (M("NPS"), "nps")],
          "ecom_otif_heat", "OTIF: loja × canal", "Coral = pior · turquesa = melhor (relativo à seleção) · alvo 95%")
    table(pg, "tab", B3, [proj(CLM(Ca, "Canal")), proj(CLM(Lj, "Loja Curta"), "Loja"), proj(M("NPS"), "NPS"), proj(M("CSAT Médio"), "CSAT"), proj(M("OTIF %"), "OTIF"),
                          proj(M("Prazo Real Médio"), "Prazo"), proj(M("% Entregas com Atraso"), "Atraso"), proj(M("Frete Médio"), "Frete"),
                          proj(M("Respostas Pesquisa"), "Resp.")],
          "CX por canal × loja", sort=[(M("OTIF %"), "Ascending")], sub="ordenado do pior OTIF para o melhor")

    # ---------------- PRODUTOS
    pg = pages["prod"]; chrome(pg); painel(pg, [(Ca, "Canal", "Canal"), (Pr, "Categoria", "Categoria"), (Pr, "Subcategoria", "Subcategoria")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom Produtos")
    deneb(pg, "d_op", MAIN, [(CLM(Pr, "Subcategoria"), "sub"), (CLM(Pr, "Categoria"), "cat"), (M("Unidades Digitais Itens"), "un"),
                             (M("% Avaliações Abaixo de 4"), "baixa"), (M("Avaliações"), "aval"), (M("Nota Média Produto"), "nota")], "ecom_oportunidade",
          "Matriz de oportunidade por subcategoria", "x = volume digital · y = % avaliações abaixo de 4 · tamanho = nº de avaliações · linhas = medianas")
    bar(pg, "cat", R1, CLM(Pr, "Categoria"), ["% Avaliações Abaixo de 4"], "% avaliações abaixo de 4 por categoria", "relativo à seleção · coral = acima de 1,5× a média", cor_measure="Cor Nota")
    bar(pg, "notas", R2, CLM("fAvaliacoesProduto", "Nota"), ["Avaliações"], "Distribuição das notas", "a base só tem notas 3 e 4", color=K["petroleo2"], sort_cat=True)
    x, y, w, h = inner(B1, 14)
    html(pg, "narr", (x, y, w, h - 110), "HTML Narrativa Produtos Digital")
    html(pg, "alerta", (x, y + h - 100, w, 100), "HTML Alerta Reviews")
    table(pg, "tab", B23, [proj(M("Ranking Oportunidade"), "#"), proj(CLM(Pr, "Produto")), proj(CLM(Pr, "Categoria")),
                           proj(M("SVG Barra Oportunidade SKU"), "Oportunidade"), proj(M("Score Oportunidade"), "Score"),
                           proj(M("Unidades Digitais Itens"), "Unid. digitais"), proj(M("Avaliações"), "Aval."), proj(M("% Avaliações Abaixo de 4"), "% < 4"),
                           proj(M("Receita Digital Itens"), "Receita digital"), proj(M("Margem Digital Itens %"), "Margem")],
          "SKUs para investigar: volume digital × insatisfação relativa", sub="Score = unidades × % avaliações abaixo de 4 (mín. 5 avaliações) · priorização, não causa",
          sort=[(M("Score Oportunidade"), "Descending")])

    # ---------------- CLIENTES
    pg = pages["cli"]; chrome(pg); painel(pg, [(Ca, "Canal", "Canal"), (Cl, "Segmento RFV", "Segmento RFV")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom Clientes")
    deneb(pg, "d_coorte", MAIN, [(CLM(Cl, "Coorte Digital"), "coorte"), (CLM(Cl, "Coorte Digital Num"), "coorte_ord"), (CLM(D, "AnoMes Num"), "mes_ord"),
                                 (M("Retenção Coorte %"), "ret"), (M("Clientes Digitais"), "cli")], "ecom_coorte",
          "Coortes digitais: % que volta a comprar no digital", "Linha = mês da 1ª compra digital observada · coluna = meses depois · coorte simples")
    bar(pg, "canal", R1, CLM(Ca, "Canal"), ["Clientes Digitais"], "Clientes por canal", "um cliente pode comprar em mais de um canal")
    bar(pg, "rfv", R2, CLM(Cl, "Segmento RFV"), ["Clientes Digitais"], "Clientes digitais por segmento RFV", "RFV da rede · foto 30/09/2026", color=K["petroleo2"], sort_cat=True)
    x, y, w, h = inner(B1, 14)
    html(pg, "narr", (x, y, w, 132), "HTML Narrativa Clientes Digitais")
    html(pg, "mini", (x, y + 136, w, h - 136), "HTML Frequência Clientes")
    table(pg, "tab", B23, [proj(CLM(Ca, "Canal")), proj(CLM(Lj, "Loja Curta"), "Loja"), proj(M("Clientes Digitais"), "Clientes"),
                           proj(M("Clientes Digitais Novos"), "Novos"), proj(M("Frequência Digital"), "Pedidos/cliente"), proj(M("Recompra Digital %"), "Recompra"),
                           proj(M("Ticket Digital Identificado"), "Ticket"), proj(M("Receita Digital por Cliente"), "Receita/cliente"), proj(M("% Clientes Omnichannel"), "Omnichannel")],
          "Clientes digitais por canal × loja", sub="Total ≠ soma das linhas: clientes multicanal contam uma vez no total", sort=[(M("Clientes Digitais"), "Descending")])

    # ---------------- ESTRATÉGIA
    pg = pages["estr"]; chrome(pg); painel(pg, [(In, "Pilar", "Pilar"), (In, "Status Iniciativa", "Status")])
    html(pg, "kpis", KPI, "HTML KPIs Ecom Estratégia")
    deneb(pg, "d_rm", MAIN, [(CLM(In, "Iniciativa"), "ini"), (CLM(In, "Pilar"), "pilar"), (CLM(In, "Trimestre Alvo"), "tri"),
                             (M("% Conclusão Roadmap"), "pct"), (M("Status Roadmap Atual"), "st")], "ecom_roadmap",
          "Roadmap digital: conclusão por iniciativa", "Snapshot do último mês do filtro · cor = pilar")
    bar(pg, "pilar", R1, CLM(In, "Pilar"), ["% Conclusão Roadmap"], "Conclusão média por pilar")
    bar(pg, "ab", R2, CLM("fExperimentosAB", "Experimento"), ["Lift Experimento"], "Testes A/B: lift da variante B", "turquesa = venceu · âmbar = empatou", cor_measure="Cor Resultado Teste")
    html(pg, "rec", inner(B1, 14), "Recomendações Priorizadas")
    table(pg, "mat", B2, [proj(CLM(Ma, "Componente")), proj(M("SVG Barra Score Componente"), "Atingimento"), proj(M("Score Componente"), "Score"),
                          proj(M("Valor Componente"), "Atual"), proj(CLM(Ma, "Alvo")), proj(CLM(Ma, "Fonte Alvo"), "Origem do alvo")],
          "Maturidade digital: componentes vs alvo", sub="Score = média simples dos 5 componentes (0–100)", sort=[(CLM(Ma, "Componente"), "Ascending")])
    _o = pg.visuals[-1]["visual"]["objects"]
    _o["grid"][0]["properties"]["rowPadding"] = N(9); _o["values"][0]["properties"]["fontSize"] = N(11)
    _o["total"] = [P(totals=L(False))]
    x, y, w, h = inner(B3, 14)
    html(pg, "narr", (x, y, w, 118), "HTML Narrativa Estratégia")
    html(pg, "marcos", (x, y + 122, w, h - 122), "HTML Próximos Marcos")

    for k, _ in PAGES[1:]:
        pages[k].filters = [digital_filter(k)]
    return [pages[k] for k, _ in PAGES] + [tt], bookmarks

def backgrounds(out, logo_path):
    os.makedirs(out, exist_ok=True)
    lg = logo_negativo(logo_path); files = []
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Regular.otf", 12)
    for i, (k, d) in enumerate(PAGES):
        im = fundo_base()
        if k == "home":
            big = lg.resize((int(lg.width * 150 / lg.height), 150), Image.LANCZOS)
            im.alpha_composite(big, (110, 110))
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            # motivo gráfico: cursor/clique + sacola estilizada em turquesa translúcido
            od.rounded_rectangle((1380, 250, 1700, 560), 48, fill=(24, 184, 159, 30))
            od.arc((1460, 180, 1620, 340), 180, 360, fill=(24, 184, 159, 90), width=14)
            od.ellipse((1640, 470, 1800, 630), fill=(221, 245, 235, 20))
            od.polygon([(1230, 330), (1230, 450), (1262, 420), (1286, 470), (1302, 462), (1279, 413), (1320, 410)], fill=(221, 245, 235, 70))
            im = Image.alpha_composite(im, ov.filter(ImageFilter.GaussianBlur(2)))
            im = glass(im, (100, 620, 1720, 182), r=20, a=8)
        else:
            im = glass(im, SB, r=20, a=14)
            sm = lg.resize((176, int(lg.height * 176 / lg.width)), Image.LANCZOS)
            im.alpha_composite(sm, (28, 40))
            dr = ImageDraw.Draw(im); dr.line((36, 112, 196, 112), fill=(24, 184, 159, 90), width=1)
            ay = NAV_Y0 + i * (NAV_H + NAV_GAP)
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((22, ay + 8, 26, ay + NAV_H - 8), 2, fill=(24, 184, 159, 255))
            im = Image.alpha_composite(im, ov)
            ImageDraw.Draw(im).text((32, 970), "E-commerce · Site · App · Delivery", fill=(24, 184, 159, 255), font=f)
            ImageDraw.Draw(im).text((32, 990), "Base sintética · dados fictícios", fill=(159, 201, 193, 255), font=f)
            ImageDraw.Draw(im).text((32, 1010), "01/10/2024 a 30/09/2026", fill=(221, 245, 235, 255), font=f)
            im = glass(im, TOP, r=16, a=10)
            for b in PANELS[k]: im = glass(im, b, r=16, a=12)
        fn = f"ecom_{k}.png"; im.convert("RGB").save(os.path.join(out, fn), optimize=True); files.append(fn)
    lg.save(os.path.join(out, "logo_negativo.png"))
    return files

def write_report(base, model_folder, logo_path):
    defs = os.path.join(base, "definition"); res = os.path.join(base, "StaticResources", "RegisteredResources")
    bgs = backgrounds(res, logo_path)
    R.wj(os.path.join(res, "FarmaVitta_Tema_Dark.json"), V.theme())
    R.wj(os.path.join(base, "definition.pbir"), {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
                                                "version": "4.0", "datasetReference": {"byPath": {"path": f"../{model_folder}"}}})
    items = [{"name": "FarmaVitta_Tema_Dark.json", "path": "FarmaVitta_Tema_Dark.json", "type": "CustomTheme"}] + \
            [{"name": f, "path": f, "type": "Image"} for f in bgs + ["logo_negativo.png"]]
    R.wj(os.path.join(defs, "report.json"), {
        "$schema": f"{SCH}/report/{R.V_REP}/schema.json",
        "themeCollection": {"customTheme": {"name": "FarmaVitta_Tema_Dark.json", "reportVersionAtImport": {"visual": "2.2.0", "report": "3.0.0", "page": "2.0.0"}, "type": "RegisteredResources"}},
        "publicCustomVisuals": [V.DENEB_VT, V.HTML_VT],
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": items}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True}})
    R.wj(os.path.join(defs, "version.json"), {"$schema": f"{SCH}/versionMetadata/{R.V_VER}/schema.json", "version": "2.0.0"})
    pages, bms = build()
    R.wj(os.path.join(defs, "pages", "pages.json"), {"$schema": f"{SCH}/pagesMetadata/{R.V_PAGES}/schema.json",
                                                     "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    nvis = 0
    for p in pages:
        pj = {"$schema": f"{SCH}/page/{R.V_PAGE}/schema.json", "name": p.name, "displayName": p.display, "displayOption": "FitToPage", "height": p.h, "width": p.w}
        if p.bg:
            pj["objects"] = {"background": [P(image={"image": {"name": L(p.bg), "url": {"expr": {"ResourcePackageItem": {
                "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": p.bg}}}, "scaling": L("Fit")}}, transparency=N(0))]}
        else:
            pj["objects"] = {"background": [P(color=COL(K["fundo2"]), transparency=N(0))]}
        if getattr(p, "filters", None): pj["filterConfig"] = {"filters": p.filters}
        if p.tooltip:
            pj["type"] = "Tooltip"; pj["pageBinding"] = {"name": hid("bind", p.key), "type": "Tooltip", "referenceScope": "Default"}
        if p.hidden: pj["visibility"] = "HiddenInViewMode"
        R.wj(os.path.join(defs, "pages", p.name, "page.json"), pj)
        for v in p.visuals:
            R.wj(os.path.join(defs, "pages", p.name, "visuals", v["name"], "visual.json"), v); nvis += 1
    grupos = {}
    for b in bms:
        g = b.pop("_grupo"); grupos.setdefault(g, []).append(b["name"])
        R.wj(os.path.join(defs, "bookmarks", f"{b['name']}.bookmark.json"), b)
    R.wj(os.path.join(defs, "bookmarks", "bookmarks.json"), {"$schema": f"{SCH}/bookmarksMetadata/1.0.0/schema.json",
         "items": [{"name": hid("grp", g), "displayName": f"Filtros · {g}", "children": c} for g, c in grupos.items()]})
    dd = os.path.join(os.path.dirname(base), "Deneb_Ecom"); os.makedirs(dd, exist_ok=True)
    for k_ in [k for k in DS.SPECS if k.startswith("ecom_")]: R.wj(os.path.join(dd, f"{k_}.vl.json"), DS.SPECS[k_])
    R.wj(os.path.join(dd, "_config.json"), DS.CONFIG)
    return pages, nvis, len(bms)
