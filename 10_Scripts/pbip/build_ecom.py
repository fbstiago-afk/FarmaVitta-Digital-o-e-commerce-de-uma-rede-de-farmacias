# -*- coding: utf-8 -*-
"""Monta o PBIP FarmaVitta_Ecom e valida os JSON contra os esquemas oficiais.
Uso: python3 build_ecom.py <pasta_saida> <logo.png> [pasta_json_schemas]"""
import os, sys, json, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelo, modelo_ecom, relatorio_ecom

out, logo = sys.argv[1], sys.argv[2]
schemas = sys.argv[3] if len(sys.argv) > 3 else None
NAME = "FarmaVitta_Ecom"
for p in (f"{NAME}.SemanticModel", f"{NAME}.Report", "Deneb_Ecom"):
    shutil.rmtree(os.path.join(out, p), ignore_errors=True)
os.makedirs(out, exist_ok=True)
sm = os.path.join(out, f"{NAME}.SemanticModel"); rp = os.path.join(out, f"{NAME}.Report")
modelo.write_semantic_model_root(sm)
n_med = modelo.write_model(sm)
pages, n_vis, n_bm = relatorio_ecom.write_report(rp, f"{NAME}.SemanticModel", logo)
json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
           "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}},
          open(os.path.join(out, f"{NAME}.pbip"), "w", encoding="utf-8"), indent=2)
print(f"Tabelas: {len(modelo.T)} · Relações: {len(modelo.REL)} · Medidas: {n_med} (podadas da base: {modelo_ecom.N_PODADAS}) · Páginas: {len(pages)} · Visuais: {n_vis} · Bookmarks: {n_bm}")
if schemas:
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource
    import referencing.jsonschema as RJ
    base_url = "https://developer.microsoft.com/json-schemas/"
    res = []
    for f in glob.glob(os.path.join(schemas, "**", "*.json"), recursive=True):
        try: s = json.load(open(f, encoding="utf-8"))
        except Exception: continue
        r = Resource.from_contents(s, default_specification=RJ.DRAFT7)
        res.append((base_url + os.path.relpath(f, schemas).replace(os.sep, "/"), r))
        if isinstance(s, dict) and s.get("$id"): res.append((s["$id"], r))
    reg = Registry().with_resources(res); urls = {u for u, _ in res}
    erros, n = 0, 0
    for f in glob.glob(os.path.join(rp, "**", "*.json"), recursive=True) + glob.glob(os.path.join(sm, "*.pbism")) + glob.glob(os.path.join(sm, ".pbi", "*.json")):
        doc = json.load(open(f, encoding="utf-8")); sch = doc.get("$schema")
        if not sch: continue
        n += 1
        if sch not in urls: print("SEM ESQUEMA LOCAL:", sch); continue
        es = list(Draft7Validator(reg.contents(sch), registry=reg).iter_errors(doc))
        for e in es[:3]: print("ERRO", os.path.relpath(f, out), "→", "/".join(map(str, e.absolute_path)), ":", e.message[:220])
        erros += len(es)
    print(f"Validação de esquema: {n} arquivos JSON, {erros} erros")
