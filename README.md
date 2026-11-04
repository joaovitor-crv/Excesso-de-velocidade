# Excessos de velocidade — CRV

Painel dos excessos de velocidade dos caminhões, pranchas e ônibus, com filtros por grupo, frota, dia, turno (A 07–15h, B 15–23h, C 23–07h) e via (rodovia ou estrada de terra). Clicar numa frota abre os 5 maiores excessos dela em estrada de terra e em rodovia.

Abra o `index.html` ou acesse pelo GitHub Pages.

**Período atual:** 01/11/2026 a 03/11/2026

## Frotas
- **Caminhões:** todas as frotas 605xx do arquivo, menos as pranchas
- **Pranchas:** 60521, 60530, 60524, 60543
- **Ônibus:** 46100, 46111, 46221, 46222, 46171, 46122, 46123, 46121, 46226, 46118, 46225, 46114, mais as **vans** 46234 e 46236 (no mesmo grupo, marcadas como VAN)

As outras frotas 46 do arquivo ficam de fora. Para mudar, edite `PRANCHAS`, `ONIBUS` e `PREFIXO_CAMINHOES` em `gerar/gerar_painel.py`.

## Regras
- **Limites:** os da regra de cada alerta no rastreador — 70 km/h na rodovia e 50 km/h em estrada de terra; os ônibus 46234 e 46236 têm a regra de van do rastreador, 80 km/h na rodovia.
- **Sem contar duas vezes:** o rastreador gera um alerta instantâneo e um alerta "(RELATÓRIO)" para o mesmo excesso. O painel usa o "(RELATÓRIO)", que traz duração e velocidade mínima, máxima e média. A regra de van de 80 km/h (46234 e 46236) só existe na versão instantânea e entra como está.
- **Tempo acima do limite:** soma da duração das ocorrências. Ocorrência com mais de 1 hora (rastreador sem novas leituras) conta, mas o tempo não é somado.
- **Via:** excesso com limite de 50 km/h = estrada de terra; 70 km/h ou mais = rodovia.

## Como atualizar
1. Exporte do rastreador o **Relatório de Rastreamento — Alertas e notificações** (xlsx).
2. Rode:
   ```
   python3 gerar/gerar_painel.py --xlsx Relatorio_Rastreamento_Alertasenotificacoes.xlsx --ini 2026-11-01 --fim 2026-11-03
   ```
   Sem `--ini`/`--fim`, usa todos os dias do arquivo.
3. Faça commit e push do `index.html`.

Precisa de Python 3 com `openpyxl`. Para mudar o visual, edite `gerar/modelo.html` (os dados entram no lugar de `__DADOS__`).

Desenvolvido por João Vitor - CRV
