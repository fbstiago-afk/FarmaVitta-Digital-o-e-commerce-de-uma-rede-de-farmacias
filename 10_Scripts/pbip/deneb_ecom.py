# -*- coding: utf-8 -*-
"""Specs Vega-Lite (Deneb) do relatório FarmaVitta E-commerce. Registra em deneb_specs.SPECS (reaproveita CONFIG da v2)."""
import deneb_specs as DS
VL, MI = DS.VL, DS.MI
S = DS.SPECS

S["ecom_receita"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "encoding": {"x": {"field": "mes", "type": "ordinal", "sort": {"field": "ord", "op": "min", "order": "ascending"}, "axis": {"title": None, "labelAngle": -45, "labelOverlap": False}}},
    "layer": [
        {"layer": [
            {"mark": {"type": "bar", "cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4, "width": {"band": 0.68}},
             "encoding": {"y": {"field": "receita", "type": "quantitative", "axis": {"title": None, "labelExpr": "format(datum.value / 1000, ',.0f') + ' mil'", "tickCount": 5}},
                          "color": {"field": "cor", "type": "nominal", "scale": None},
                          "tooltip": [{"field": "mes", "title": "Mês"}, {"field": "receita", "title": "Receita digital", "format": ",.0f"},
                                      {"field": "ly", "title": "Ano anterior", "format": ",.0f"}, {"field": "share", "title": "Share digital", "format": ".1%"}]}},
            {"mark": {"type": "line", "color": "#DDF5EB", "strokeWidth": 2, "opacity": 0.8, "point": {"filled": True, "size": 26, "color": "#DDF5EB"}},
             "encoding": {"y": {"field": "ly", "type": "quantitative"}}}]},
        {"mark": {"type": "line", "color": "#F2C46D", "strokeWidth": 2, "strokeDash": [5, 4], "point": {"filled": True, "size": 20, "color": "#F2C46D"}},
         "encoding": {"y": {"field": "share", "type": "quantitative", "scale": {"zero": False}, "axis": {"title": None, "format": ".0%", "orient": "right", "grid": False, "labelColor": "#F2C46D"}}}}],
    "resolve": {"scale": {"y": "independent"}}}

S["ecom_funil"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "transform": [
        {"window": [{"op": "first_value", "field": "val", "as": "topo"}, {"op": "lag", "field": "val", "as": "ant"}], "sort": [{"field": "ord"}], "frame": [None, None]},
        {"calculate": "datum.val / datum.topo", "as": "pct_topo"},
        {"calculate": "datum.ant ? datum.val / datum.ant : 1", "as": "pct_ant"},
        {"calculate": "max(datum.pct_topo, 0.006)", "as": "w"},
        {"calculate": "format(datum.val, ',.0f') + (datum.ord == 1 ? '' : '  ·  ' + format(datum.pct_ant, '.1%') + ' da etapa anterior')", "as": "rot"}],
    "encoding": {"y": {"field": "etapa", "type": "ordinal", "sort": {"field": "ord", "op": "min", "order": "ascending"}, "axis": {"title": None, "labelFontSize": 12, "labelColor": "#DDF5EB", "labelPadding": 8}}},
    "layer": [
        {"transform": [{"calculate": "1", "as": "one"}], "mark": {"type": "bar", "cornerRadius": 6, "height": {"band": 0.62}, "color": "rgba(255,255,255,0.06)"}, "encoding": {"x": {"field": "one", "type": "quantitative", "scale": {"domain": [0, 1]}, "axis": None}}},
        {"mark": {"type": "bar", "cornerRadius": 6, "height": {"band": 0.62}},
         "encoding": {"x": {"field": "w", "type": "quantitative", "scale": {"domain": [0, 1]}, "axis": None},
                      "color": {"field": "ord", "type": "ordinal", "scale": {"range": ["#125F61", "#18B89F", "#DDF5EB"]}, "legend": None},
                      "tooltip": [{"field": "etapa", "title": "Etapa"}, {"field": "val", "title": "Volume", "format": ",.0f"},
                                  {"field": "pct_topo", "title": "% das sessões", "format": ".2%"}, {"field": "pct_ant", "title": "% da etapa anterior", "format": ".1%"}]}},
        {"transform": [{"filter": "datum.pct_topo < 0.6"}], "mark": {"type": "text", "fontSize": 13, "fontWeight": 600, "align": "left", "dx": 10, "color": "#E8F3F1"},
         "encoding": {"x": {"field": "w", "type": "quantitative"}, "text": {"field": "rot"}}},
        {"transform": [{"filter": "datum.pct_topo >= 0.6"}], "mark": {"type": "text", "fontSize": 13, "fontWeight": 600, "align": "right", "dx": -12, "color": "#E8F3F1"},
         "encoding": {"x": {"field": "w", "type": "quantitative"}, "text": {"field": "rot"}}}]}

S["ecom_nps"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "encoding": {"x": {"field": "mes", "type": "ordinal", "sort": {"field": "ord", "op": "min", "order": "ascending"}, "axis": {"title": None, "labelAngle": -45}}},
    "layer": [
        {"transform": [{"fold": ["prom", "neu", "det"], "as": ["classe", "pct"]},
                       {"calculate": "datum.classe == 'prom' ? 'Promotores' : datum.classe == 'neu' ? 'Neutros' : 'Detratores'", "as": "Classe"},
                       {"calculate": "datum.classe == 'prom' ? 1 : datum.classe == 'neu' ? 2 : 3", "as": "co"}],
         "mark": {"type": "bar", "width": {"band": 0.7}},
         "encoding": {"y": {"field": "pct", "type": "quantitative", "stack": "normalize", "axis": {"title": None, "format": ".0%"}},
                      "color": {"field": "Classe", "type": "nominal", "scale": {"domain": ["Promotores", "Neutros", "Detratores"], "range": ["#18B89F", "#3D6E72", "#EF9277"]}, "legend": {"title": None}},
                      "order": {"field": "co"},
                      "tooltip": [{"field": "mes", "title": "Mês"}, {"field": "Classe"}, {"field": "pct", "title": "%", "format": ".1%"}]}},
        {"mark": {"type": "line", "color": "#F2C46D", "strokeWidth": 2.5, "point": {"filled": True, "size": 30, "color": "#F2C46D"}},
         "encoding": {"y": {"field": "nps", "type": "quantitative", "axis": {"title": "NPS", "orient": "right", "grid": False, "labelColor": "#F2C46D", "titleColor": "#F2C46D"}},
                      "tooltip": [{"field": "mes", "title": "Mês"}, {"field": "nps", "title": "NPS", "format": "+.1f"}, {"field": "resp", "title": "Respostas", "format": ",.0f"}]}}],
    "resolve": {"scale": {"y": "independent"}}}

S["ecom_otif_heat"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "encoding": {"x": {"field": "canal", "type": "nominal", "axis": {"title": None, "labelAngle": 0, "orient": "top"}},
                 "y": {"field": "loja", "type": "nominal", "axis": {"title": None}}},
    "layer": [
        {"mark": {"type": "rect", "cornerRadius": 4, "stroke": "#071E23", "strokeWidth": 3},
         "encoding": {"color": {"field": "otif", "type": "quantitative", "scale": {"range": ["#EF9277", "#F2C46D", "#18B89F"]}, "legend": None},
                      "tooltip": [{"field": "loja", "title": "Loja"}, {"field": "canal", "title": "Canal"}, {"field": "otif", "title": "OTIF", "format": ".1%"},
                                  {"field": "ped", "title": "Pedidos", "format": ",.0f"}, {"field": "nps", "title": "NPS", "format": "+.1f"}]}},
        {"mark": {"type": "text", "fontSize": 12, "fontWeight": 600, "color": "#071E23"}, "encoding": {"text": {"field": "otif", "type": "quantitative", "format": ".1%"}}}]}

S["ecom_oportunidade"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "transform": [{"filter": "datum.aval >= 20"},
                  {"joinaggregate": [{"op": "median", "field": "un", "as": "mun"}, {"op": "median", "field": "baixa", "as": "mba"}]},
                  {"calculate": "datum.un >= datum.mun && datum.baixa > datum.mba && datum.baixa > 0 ? 'Prioridade: volume alto + insatisfação' : 'Demais'", "as": "quad"}],
    "layer": [
        {"mark": {"type": "circle", "opacity": 0.85, "stroke": "#071E23", "strokeWidth": 1},
         "encoding": {"x": {"field": "un", "type": "quantitative", "axis": {"title": "unidades vendidas no digital"}, "scale": {"zero": False}},
                      "y": {"field": "baixa", "type": "quantitative", "axis": {"title": "% avaliações abaixo de 4", "format": ".1%"}, "scale": {"zero": False}},
                      "size": {"field": "aval", "type": "quantitative", "scale": {"range": [60, 700]}, "legend": None},
                      "color": {"field": "quad", "type": "nominal", "scale": {"domain": ["Prioridade: volume alto + insatisfação", "Demais"], "range": ["#EF9277", "#18B89F"]}, "legend": {"title": None}},
                      "tooltip": [{"field": "sub", "title": "Subcategoria"}, {"field": "cat", "title": "Categoria"}, {"field": "un", "title": "Unidades digitais", "format": ",.0f"},
                                  {"field": "aval", "title": "Avaliações", "format": ",.0f"}, {"field": "baixa", "title": "% abaixo de 4", "format": ".1%"}, {"field": "nota", "title": "Nota média", "format": ".2f"}]}},
        {"transform": [{"filter": "datum.baixa > 0"}], "mark": {"type": "text", "fontSize": 9, "dy": -12, "color": "#9FC9C1"}, "encoding": {"x": {"field": "un", "type": "quantitative"}, "y": {"field": "baixa", "type": "quantitative"}, "text": {"field": "sub"}}},
        {"mark": {"type": "rule", "color": "rgba(255,255,255,0.25)", "strokeDash": [4, 3]}, "encoding": {"x": {"aggregate": "median", "field": "un"}}},
        {"mark": {"type": "rule", "color": "rgba(255,255,255,0.25)", "strokeDash": [4, 3]}, "encoding": {"y": {"aggregate": "median", "field": "baixa"}}}]}

S["ecom_coorte"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "transform": [
        {"filter": "datum.coorte_ord != null && datum.ret != null"},
        {"calculate": "(floor(datum.mes_ord / 100) * 12 + datum.mes_ord % 100) - (floor(datum.coorte_ord / 100) * 12 + datum.coorte_ord % 100)", "as": "m"},
        {"filter": "datum.m >= 1 && datum.m <= 12"}],
    "mark": {"type": "rect", "cornerRadius": 2, "stroke": "#071E23", "strokeWidth": 1.5},
    "encoding": {
        "x": {"field": "m", "type": "ordinal", "axis": {"title": "meses desde a 1ª compra digital", "labelAngle": 0}},
        "y": {"field": "coorte", "type": "ordinal", "sort": {"field": "coorte_ord", "op": "min", "order": "ascending"}, "axis": {"title": None}},
        "color": {"field": "ret", "type": "quantitative", "scale": {"domainMin": 0, "range": ["#0E3138", "#125F61", "#18B89F", "#DDF5EB"]}, "legend": {"title": "Retenção", "format": ".0%", "orient": "right", "gradientLength": 160}},
        "tooltip": [{"field": "coorte", "title": "Coorte"}, {"field": "m", "title": "Mês +"}, {"field": "ret", "title": "Retenção", "format": ".1%"}, {"field": "cli", "title": "Clientes ativos", "format": ",.0f"}]}}

S["ecom_roadmap"] = {
    "$schema": VL, "data": {"name": "dataset"}, "width": "container", "height": "container",
    "encoding": {"y": {"field": "ini", "type": "nominal", "sort": {"field": "pct", "op": "max", "order": "descending"}, "axis": {"title": None, "labelLimit": 230}}},
    "layer": [
        {"transform": [{"calculate": "1", "as": "one"}], "mark": {"type": "bar", "cornerRadius": 4, "height": {"band": 0.7}, "color": "rgba(255,255,255,0.07)"}, "encoding": {"x": {"field": "one", "type": "quantitative", "scale": {"domain": [0, 1]}}}},
        {"mark": {"type": "bar", "cornerRadius": 4, "height": {"band": 0.7}},
         "encoding": {"x": {"field": "pct", "type": "quantitative", "scale": {"domain": [0, 1]}, "axis": {"title": None, "format": ".0%", "grid": False}},
                      "color": {"field": "pilar", "type": "nominal", "scale": {"domain": ["Conversão", "CX", "Produto", "Operação", "Estratégia"], "range": ["#18B89F", "#DDF5EB", "#F2C46D", "#EF9277", "#5FA8A0"]}, "legend": {"title": None}},
                      "tooltip": [{"field": "ini", "title": "Iniciativa"}, {"field": "pilar", "title": "Pilar"}, {"field": "pct", "title": "% conclusão", "format": ".0%"},
                                  {"field": "st", "title": "Status (último mês)"}, {"field": "tri", "title": "Trimestre-alvo"}]}},
        {"mark": {"type": "text", "align": "left", "dx": 4, "fontSize": 10, "color": "#E8F3F1"}, "encoding": {"x": {"field": "pct", "type": "quantitative"}, "text": {"field": "pct", "format": ".0%"}}}]}
