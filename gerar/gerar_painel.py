"""Gera o index.html do painel de excessos de velocidade (CRV).

Uso:
  python3 gerar/gerar_painel.py --base ../excessos-base/dados/alertas.csv --ini 2026-11-01 --fim 2026-11-03
  python3 gerar/gerar_painel.py --xlsx Relatorio_Rastreamento_Alertasenotificacoes.xlsx [--ini ... --fim ...]
  ... --monit "crv_industrial_EXPORTACAO MONIT221_....csv"   (opcional: motorista dos caminhões)

Entrada: a base histórica (repositório excessos-base, dados/alertas.csv) ou direto o
"Relatório de Rastreamento — Alertas e notificações" (xlsx) do rastreador.
Frotas e grupos: FROTAS abaixo. Limites: os da própria regra de cada alerta.

Desenvolvido por João Vitor - CRV
"""
import argparse
import bisect
import csv
import json
import os
import re
from datetime import datetime, timedelta

import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))

# Frotas do painel, por grupo (definidas pelo usuário em 04/11/2026). As outras frotas do arquivo ficam de fora.
PRANCHAS = ["60521", "60530", "60524", "60543"]
ONIBUS = ["46100", "46111", "46221", "46222", "46171", "46122", "46123", "46121", "46226", "46118", "46225", "46114", "46234", "46236"]
PREFIXO_CAMINHOES = "605"  # todas as frotas 605xx do arquivo, menos as pranchas
VANS = ["46234", "46236"]  # vans: ficam no grupo dos ônibus, com destaque "VAN" no painel (pedido do usuário, 04/11/2026)
LIMITES = {
    "Caminhões": "70 km/h na rodovia · 50 km/h em estrada de terra",
    "Pranchas": "70 km/h na rodovia · 50 km/h em estrada de terra",
    "Ônibus": "70 km/h na rodovia · 50 km/h em estrada de terra · vans 46234 e 46236: 80 km/h na rodovia",
}


def grupos(frotas_arquivo):
    """Grupos do painel: caminhões (605xx do arquivo, menos pranchas), pranchas e ônibus (lista fixa)."""
    cam = sorted(f for f in frotas_arquivo if f.startswith(PREFIXO_CAMINHOES) and f not in PRANCHAS)
    return {"Caminhões": cam, "Pranchas": PRANCHAS, "Ônibus": ONIBUS}
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


def ler_base(caminho):
    """Lê a base histórica (excessos-base/dados/alertas.csv) no mesmo formato do xlsx."""
    out = []
    with open(caminho, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            s = int(r["duracao_s"] or 0)
            out.append(dict(frota=r["frota"], regra=r["regra"], data=f'{r["data"][8:]}/{r["data"][5:7]}/{r["data"][:4]}', hora=r["hora"],
                            dur=f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}",
                            tel=f'[Velocidade: {r["vel_min"]} | {r["vel_max"]} | {r["vel_media"]}]' if r["vel_max"] else "",
                            area=f'[{r["area"]}]', loc=r["local_inicio"]))
    return out


SEM_OP = "Sem Operador"
FOLGA = 120  # s antes do início e depois do fim da ocorrência
APROX_MIN = 30  # monit sem leitura no horário: usa a leitura mais próxima até 30 min, se for do mesmo operador


def nome(n):
    return " ".join(w.lower() if w in ("DE", "DA", "DO", "DOS", "DAS", "E") else w.capitalize() for w in n.split())


def ler_monit(caminho, frotas):
    """Lê o monit (csv ; ) e devolve {frota: [(datahora, operador), ...]} ordenado, só das frotas pedidas."""
    out = {}
    with open(caminho, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            f = (r.get("Equipamento") or "").strip()
            if f not in frotas:
                continue
            op = (r.get("Operador") or "").strip()
            if not op or op.lower() == "null":
                op = SEM_OP
            out.setdefault(f, []).append((datetime.strptime(r["Data/Hora"], "%d/%m/%Y %H:%M:%S"), op))
    for L in out.values():
        L.sort()
    return out


def motorista(mon, e):
    """Operador logado no monit durante a ocorrência: [situação, nome, detalhe].
    Situações: ok, aprox (leitura mais próxima), sem (sem login), semreg (sem leitura), fora (frota fora do monit)."""
    L = mon.get(e[0])
    if not L:
        return ["fora", "", ""]
    t = datetime.strptime(f"{e[2]} {e[3]}", "%Y-%m-%d %H:%M:%S")
    ts = [x[0] for x in L]
    s = min(e[4] if e[4] is not None else DUR_MAX, DUR_MAX) or 60
    a = bisect.bisect_left(ts, t - timedelta(seconds=FOLGA))
    b = bisect.bisect_right(ts, t + timedelta(seconds=s + FOLGA))
    jan = [op for _, op in L[a:b]]
    if jan:
        nomes = [op for op in jan if op != SEM_OP]
        if nomes:
            cont = sorted({n: nomes.count(n) for n in nomes}.items(), key=lambda x: -x[1])
            return ["ok", nome(cont[0][0]), ("troca no período: " + " / ".join(nome(n) for n, _ in cont)) if len(cont) > 1 else ""]
        return ["sem", "", ""]  # sem login: sem "último login" (retirado a pedido do usuário, 05/11/2026)
    i = bisect.bisect_left(ts, t)
    viz = [L[j] for j in (i - 1, i) if 0 <= j < len(L) and abs((L[j][0] - t).total_seconds()) <= APROX_MIN * 60]
    if viz and len({op for _, op in viz}) == 1 and viz[0][1] != SEM_OP:
        mn = min(abs((x[0] - t).total_seconds()) for x in viz) / 60
        return ["aprox", nome(viz[0][1]), f"monit sem leitura no horário; leitura mais próxima a {round(mn)} min"]
    return ["semreg", "", ""]


def anterior(caminho):
    """Motoristas já calculados no painel anterior: {(frota, dia, hora, limite): [situação, nome, detalhe]}."""
    if not caminho or not os.path.exists(caminho):
        return {}, "", ""
    m = re.search(r"const D=(\{.*?\});\n", open(caminho, encoding="utf-8").read(), re.S)
    if not m:
        return {}, "", ""
    D = json.loads(m.group(1))
    mot = D.get("mot") or {}
    out = {(e[0], e[2], e[3], e[8]): mot[str(i)] for i, e in enumerate(D["ev"]) if str(i) in mot}
    return out, D.get("monit", ""), D.get("monitPer", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", help="relatório de alertas do rastreador (xlsx)")
    ap.add_argument("--base", help="base histórica: excessos-base/dados/alertas.csv")
    ap.add_argument("--ini", help="primeiro dia (AAAA-MM-DD); padrão: o primeiro do arquivo")
    ap.add_argument("--fim", help="último dia (AAAA-MM-DD); padrão: o último do arquivo")
    ap.add_argument("--monit", help="opcional: exportação do monit (csv ;) para o motorista dos caminhões")
    ap.add_argument("--saida", default=os.path.join(AQUI, "..", "index.html"))
    ap.add_argument("--anterior", default=None,
                    help="painel anterior (padrão: o próprio --saida); com --monit, os dias que o monit novo não cobre "
                         "mantêm o motorista já calculado nele")
    a = ap.parse_args()

    if bool(a.xlsx) == bool(a.base):
        raise SystemExit("Informe --base (base histórica) ou --xlsx (relatório do rastreador).")
    todas = ler_base(a.base) if a.base else ler(a.xlsx)
    FROTAS = grupos({x["frota"] for x in todas})
    grupo = {f: g for g, L in FROTAS.items() for f in L}
    dias_arq = sorted({datetime.strptime(x["data"], "%d/%m/%Y").strftime("%Y-%m-%d") for x in todas})
    ini, fim = a.ini or dias_arq[0], a.fim or dias_arq[-1]

    ev, longas = [], []
    for x in todas:
        if x["frota"] not in grupo:
            continue
        # sem contar duas vezes: o rastreador gera um alerta instantâneo e um "(RELATÓRIO)" para o mesmo excesso;
        # usa-se o "(RELATÓRIO)". A regra de van de 80 km/h (ônibus 46234 e 46236) só existe na versão instantânea.
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
        tipo = "Estrada de terra" if lim <= 50 else "Rodovia"  # usuário (04/11/2026): 50 km/h = estrada de terra; 70 km/h ou mais = rodovia
        s = seg(x["dur"])
        fora = s > DUR_MAX
        if fora:
            longas.append(f'{x["frota"]} em {dia[8:]}/{dia[5:7]} às {x["hora"][:5]} ({s // 3600}h{s % 3600 // 60:02d})')
        e = [x["frota"], grupo[x["frota"]], dia, x["hora"], None if fora else s, vmin, vmax, vmed, lim, tipo, area, local(x["loc"])]
        if fora:
            e.append(1)
        ev.append(e)
    ev.sort(key=lambda e: (e[2], e[3], e[0], e[8]))  # dia, hora, frota, limite

    br = lambda d: f"{d[8:]}/{d[5:7]}/{d[:4]}"
    cortados = [d for d in dias_arq if not ini <= d <= fim]
    com = {e[0] for e in ev}
    D = dict(ev=ev, frotas=FROTAS, limites=LIMITES, vans=VANS, ini=f"{br(ini)} 00:00", fim=f"{br(fim)} 23:59",
             fora=len({x["frota"] for x in todas} - set(grupo)), sem=[f for f in grupo if f not in com], longas=longas,
             cortado=("O arquivo também trazia " + ", ".join(br(d)[:5] for d in cortados) + ", que ficou de fora.") if cortados else "")
    if a.monit:
        mon = ler_monit(a.monit, set(FROTAS["Caminhões"]))
        dias_mon = {x[0].strftime("%Y-%m-%d") for L in mon.values() for x in L}
        ant, ant_nome, ant_per = anterior(a.anterior or a.saida)
        D["mot"] = {}
        for i, e in enumerate(ev):
            if e[1] != "Caminhões":
                continue
            k = (e[0], e[2], e[3], e[8])
            # monit novo só cobre alguns dias: nos outros, mantém o motorista do painel anterior
            D["mot"][i] = motorista(mon, e) if e[2] in dias_mon or k not in ant else ant[k]
        usou_ant = any(e[2] not in dias_mon and (e[0], e[2], e[3], e[8]) in ant for e in ev if e[1] == "Caminhões")
        D["monit"] = " + ".join(x for x in ([ant_nome] if usou_ant and ant_nome else []) + [os.path.basename(a.monit)])
        dts = [x[0] for L in mon.values() for x in (L[0], L[-1])]
        ini_m = min(dts).strftime("%d/%m") if dts else ""
        if usou_ant and ant_per:
            ini_m = ant_per.split(" a ")[0]
        D["monitPer"] = f"{ini_m} a {max(dts):%d/%m}" if dts else ""
        sit = {}
        for m in D["mot"].values():
            sit[m[0]] = sit.get(m[0], 0) + 1
        print("Motorista (caminhões): " + " · ".join(f"{k} {v}" for k, v in sorted(sit.items())))
    else:
        # sem --monit: mantém os motoristas do painel anterior; dias sem monit ficam "pend" (monit não enviado)
        ant, ant_nome, ant_per = anterior(a.anterior or a.saida)
        if ant:
            D["mot"] = {i: ant.get((e[0], e[2], e[3], e[8]), ["pend", "", ""]) for i, e in enumerate(ev) if e[1] == "Caminhões"}
            D["monit"], D["monitPer"] = ant_nome, ant_per
            sit = {}
            for m in D["mot"].values():
                sit[m[0]] = sit.get(m[0], 0) + 1
            print("Motorista (caminhões, do painel anterior): " + " · ".join(f"{k} {v}" for k, v in sorted(sit.items())))
    html = open(os.path.join(AQUI, "modelo.html"), encoding="utf-8").read().replace("__DADOS__", json.dumps(D, ensure_ascii=False))
    open(a.saida, "w", encoding="utf-8").write(html)
    por = {g: sum(1 for e in ev if e[1] == g) for g in FROTAS}
    print(f"Painel gerado: {br(ini)} a {br(fim)} · {len(ev)} ocorrências · " + " · ".join(f"{g} {n}" for g, n in por.items())
          + (f" · sem alerta: {', '.join(D['sem'])}" if D["sem"] else ""))


if __name__ == "__main__":
    main()
