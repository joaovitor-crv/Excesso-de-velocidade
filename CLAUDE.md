# Painel de excessos de velocidade (CRV)

Ao gerar ou atualizar o painel, use sempre o gerador. Não redesenhe a página à mão.

```
python3 gerar/gerar_painel.py --xlsx <Relatorio_Rastreamento_Alertasenotificacoes.xlsx> [--ini AAAA-MM-DD --fim AAAA-MM-DD]
```

## Padrão aprovado pelo usuário (04/11/2026)
- Entrada: "Relatório de Rastreamento — Alertas e notificações" (xlsx). O arquivo vem com o tamanho da planilha errado (A1:C1): o leitor usa `reset_dimensions()`.
- Frotas (`FROTAS` no gerador): caminhões 46100, 46111, 46221, 46222, 46171, 46122, 46123, 46121, 46226, 46118, 46225, 46114; pranchas 60521, 60530, 60524; vans 46234, 46236 (46234 e 46236 identificados como vans pelas regras "VAN" do rastreador; o usuário citou as duas frotas, mas a mensagem dele veio cortada antes de dizer o tipo). As outras frotas do arquivo ficam de fora.
- Período: o usuário pediu só dias completos (01 a 03/11/2026, sem o dia em andamento). Use `--ini`/`--fim`.
- Ocorrências: só as regras "(RELATÓRIO)" e "80 KM/H - VAN" (o alerta instantâneo duplica o "(RELATÓRIO)"). Limite = número da regra. Zona rural = área que começa com "Zona Rural".
- Ocorrência com mais de 1 h de duração conta, mas o tempo não é somado (rastreador sem leituras).
- Visual dos painéis CRV (logo, azul-marinho); cores dos grupos: caminhões azul-marinho, pranchas laranja, vans verde-água.
- Assinatura no rodapé: "Desenvolvido por João Vitor - CRV".

## Mudanças
- Visual em `gerar/modelo.html` (dados em `__DADOS__`); cálculo em `gerar/gerar_painel.py`.
- Depois de mudar, regenere o `index.html`, confira a página no navegador e faça commit e push.
