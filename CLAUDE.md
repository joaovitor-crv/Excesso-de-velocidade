# Painel de excessos de velocidade (CRV)

Ao gerar ou atualizar o painel, use sempre o gerador. Não redesenhe a página à mão.

```
python3 gerar/gerar_painel.py --xlsx <Relatorio_Rastreamento_Alertasenotificacoes.xlsx> [--ini AAAA-MM-DD --fim AAAA-MM-DD]
```

## Padrão aprovado pelo usuário (04/11/2026)
- Entrada: "Relatório de Rastreamento — Alertas e notificações" (xlsx). O arquivo vem com o tamanho da planilha errado (A1:C1): o leitor usa `reset_dimensions()`.
- Grupos (04/11/2026, definidos pelo usuário): **caminhões** = todas as frotas 605xx do arquivo, menos as pranchas; **pranchas** = 60521, 60530, 60524, 60543 (60543 incluída a pedido do usuário em 04/11/2026); **ônibus** = frotas 46, só 46100, 46111, 46221, 46222, 46171, 46122, 46123, 46121, 46226, 46118, 46225, 46114, 46234, 46236 (as outras 46 ficam de fora). 46234 e 46236 são **vans** (confirmado pelo usuário em 04/11/2026): ficam no grupo dos ônibus, com a marca "VAN" em todo o painel (`VANS` no gerador), e o limite delas é o da regra de van do rastreador (80 km/h na rodovia). Configuração em `PRANCHAS`, `ONIBUS`, `PREFIXO_CAMINHOES` e `LIMITES` no gerador.
- Período: o usuário pediu só dias completos (01 a 03/11/2026, sem o dia em andamento). Use `--ini`/`--fim`.
- Ocorrências: só as regras "(RELATÓRIO)" e "80 KM/H - VAN" (o alerta instantâneo duplica o "(RELATÓRIO)"). Limite = número da regra. Tipo de via pelo limite (usuário, 04/11/2026): 50 km/h = **estrada de terra**, 70 km/h ou mais = **rodovia** (o painel não usa mais "zona rural").
- Frotas clicáveis (gráfico por frota e tabelas): abrem a janela com os 5 maiores excessos da frota em estrada de terra e os 5 maiores em rodovia (pico, acima do limite, média, duração, área e local), respeitando o filtro de dia, com botão para filtrar o painel pela frota.
- Indicadores do topo (04/11/2026): velocidade máxima, ocorrências, pico médio acima do limite e frotas com excesso. O cartão "Tempo acima do limite" foi retirado a pedido do usuário.
- Turnos (04/11/2026): A 07–15h, B 15–23h, C 23–07h, pela hora de início. Seção "Excessos por turno" (ocorrências, % do total, pico — sem o tempo acima do limite, a pedido do usuário —, rodovia × estrada de terra, mix de grupos, maior pico e frota com mais ocorrências), clicável, e filtro "Turno". Turno aparece também nas tabelas.
- O `modelo.html` tem `[hidden]{display:none!important}`: sem isso a janela escondida cobre a página no GitHub Pages e bloqueia os cliques.
- Ocorrência com mais de 1 h de duração conta, mas o tempo não é somado (rastreador sem leituras).
- Visual dos painéis CRV (logo, azul-marinho); cores dos grupos: caminhões roxo, pranchas laranja, ônibus azul-marinho.
- Assinatura no rodapé: "Desenvolvido por João Vitor - CRV".

## Mudanças
- Visual em `gerar/modelo.html` (dados em `__DADOS__`); cálculo em `gerar/gerar_painel.py`.
- Depois de mudar, regenere o `index.html`, confira a página no navegador e faça commit e push.
