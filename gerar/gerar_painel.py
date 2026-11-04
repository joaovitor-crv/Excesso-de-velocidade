"""Gera o index.html do painel de excessos de velocidade (CRV).

Uso:
  python3 gerar/gerar_painel.py --xlsx Relatorio_Rastreamento_Alertasenotificacoes.xlsx [--ini 2026-11-01 --fim 2026-11-03]

Entrada: exportação "Relatório de Rastreamento — Alertas e notificações" (xlsx) do rastreador.
Frotas e grupos: FROTAS abaixo. Limites: os da própria regra de cada alerta.

Desenvolvido por João Vitor - CRV
"""
import argparse
import json
import os
import re
from datetime import datetime

import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))

# Frotas do painel, por grupo (definidas pelo usuário em 04/11/2026). As outras frotas do arquivo ficam de fora.
FROTAS = {
    "Caminhões": ["46100", "46111", "46221", "46222", "46171", "46122", "46123", "46121", "46226", "46118", "46225", "46114"],
    "Pranchas": ["60521", "60530", "60524"],
    "Vans": ["46234", "46236"],
}
DUR_MAX = 3600  # ocorrência com mais de 1 h sem novas leituras: conta, mas o tempo não é somado


def seg(t):
    h, m, s = (int(x) for x in str(t).split(":"))
    return h * 3600 + m * 60 + s


def local(v):
    v = str(v or "").replace(", Brasil", "")
    return re.sub(r", (\d{5}-?\d{3}|\d{8})$", "", v)


def ler(caminho):
    ws = openpyxl.load_workbook(caminho, read_only=True).active
    ws.reset_dimensions()  # o arquivo do rastreador vem com o tamanho da planilha errado (A1:C1)
    linhas = list(ws.iter_rows(min_row=3, values_only=True))
    out = []
    for r in linhas:
        frota, regra = r[1], r[3]
        if not frota or not regra:
            continue
        out.append(dict(frota=str(frota).strip(), regra=str(regra).strip(), data=r[4], hora=r[5], dur=r[7],
                        tel=r[9] or "", area=r[10] or "", loc=r[13]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--ini", help="primeiro dia (AAAA-MM-DD); padrão: o primeiro do arquivo")
    ap.add_argument("--fim", help="último dia (AAAA-MM-DD); padrão: o último do arquivo")
    ap.add_argument("--saida", default=os.path.join(AQUI, "..", "index.html"))
    a = ap.parse_args()

    grupo = {f: g for g, L in FROTAS.items() for f in L}
    todas = ler(a.xlsx)
    dias_arq = sorted({datetime.strptime(x["data"], "%d/%m/%Y").strftime("%Y-%m-%d") for x in todas})
    ini, fim = a.ini or dias_arq[0], a.fim or dias_arq[-1]

    ev, longas = [], []
    for x in todas:
        if x["frota"] not in grupo:
            continue
        # sem contar duas vezes: o rastreador gera um alerta instantâneo e um "(RELATÓRIO)" para o mesmo excesso;
        # usa-se o "(RELATÓRIO)". A regra de 80 km/h das vans só existe na versão instantânea.
        if "RELATÓRIO" not in x["regra"] and "80 KM/H - VAN" not in x["regra"]:
            continue
        dia = datetime.strptime(x["data"], "%d/%m/%Y").strftime("%Y-%m-%d")
        if not ini <= dia <= fim:
            continue
        v = re.findall(r"\d+", x["tel"])
        if len(v) < 3:
            continue
        vmin, vmax, vmed = int(v[0]), int(v[1]), int(v[2])
        lim = int(re.search(r"(\d+) KM/H", x["regra"]).group(1))
        area = x["area"].strip("[]").title().replace(" - ", " – ")
        tipo = "Zona rural" if area.startswith("Zona Rural") else "Rodovia"
        s = seg(x["dur"])
        fora = s > DUR_MAX
        if fora:
            longas.append(f'{x["frota"]} em {dia[8:]}/{dia[5:7]} às {x["hora"][:5]} ({s // 3600}h{s % 3600 // 60:02d})')
        e = [x["frota"], grupo[x["frota"]], dia, x["hora"], None if fora else s, vmin, vmax, vmed, lim, tipo, area, local(x["loc"])]
        if fora:
            e.append(1)
        ev.append(e)
    ev.sort(key=lambda e: (e[2], e[3]))

    br = lambda d: f"{d[8:]}/{d[5:7]}/{d[:4]}"
    cortados = [d for d in dias_arq if not ini <= d <= fim]
    com = {e[0] for e in ev}
    D = dict(ev=ev, frotas=FROTAS, ini=f"{br(ini)} 00:00", fim=f"{br(fim)} 23:59",
             fora=len({x["frota"] for x in todas} - set(grupo)), sem=[f for f in grupo if f not in com], longas=longas,
             cortado=("O arquivo também trazia " + ", ".join(br(d)[:5] for d in cortados) + ", que ficou de fora.") if cortados else "")
    html = open(os.path.join(AQUI, "modelo.html"), encoding="utf-8").read().replace("__DADOS__", json.dumps(D, ensure_ascii=False))
    open(a.saida, "w", encoding="utf-8").write(html)
    por = {g: sum(1 for e in ev if e[1] == g) for g in FROTAS}
    print(f"Painel gerado: {br(ini)} a {br(fim)} · {len(ev)} ocorrências · " + " · ".join(f"{g} {n}" for g, n in por.items())
          + (f" · sem alerta: {', '.join(D['sem'])}" if D["sem"] else ""))


if __name__ == "__main__":
    main()
