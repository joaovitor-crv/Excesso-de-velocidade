# Excessos de velocidade — CRV

Painel dos excessos de velocidade dos caminhões, pranchas e ônibus, com filtros por grupo, frota, dia e via (rodovia ou zona rural).

Abra o `index.html` ou acesse pelo GitHub Pages.

**Período atual:** 01/11/2026 a 03/11/2026

## Frotas
- **Caminhões:** todas as frotas 605xx do arquivo, menos as pranchas
- **Pranchas:** 60521, 60530, 60524, 60543
- **Ônibus:** 46100, 46111, 46221, 46222, 46171, 46122, 46123, 46121, 46226, 46118, 46225, 46114, 46234, 46236

As outras frotas 46 do arquivo ficam de fora. Para mudar, edite `PRANCHAS`, `ONIBUS` e `PREFIXO_CAMINHOES` em `gerar/gerar_painel.py`.

## Regras
- **Limites:** os da regra de cada alerta no rastreador — 70 km/h na rodovia e 50 km/h na zona rural; os ônibus 46234 e 46236 têm a regra de van do rastreador, 80 km/h na rodovia.
- **Sem contar duas vezes:** o rastreador gera um alerta instantâneo e um alerta "(RELATÓRIO)" para o mesmo excesso. O painel usa o "(RELATÓRIO)", que traz duração e velocidade mínima, máxima e média. A regra de van de 80 km/h (46234 e 46236) só existe na versão instantânea e entra como está.
- **Tempo acima do limite:** soma da duração das ocorrências. Ocorrência com mais de 1 hora (rastreador sem novas leituras) conta, mas o tempo não é somado.
- **Via:** área ou rota que começa com "Zona Rural" = zona rural; as demais = rodovia.

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
