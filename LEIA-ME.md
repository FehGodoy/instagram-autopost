# Instagram Autopost — 1 Reel por hora, grátis

## Como funciona
- Você coloca os vídeos na pasta `videos/` e as legendas no `posts.csv`.
- O GitHub Actions roda a cada hora, posta o próximo vídeo da fila e anota em `postados.txt`.
- Quando a fila acaba, ele simplesmente não faz nada até você adicionar mais.

## Passo 1 — Conta Profissional
No app do Instagram: **Configurações → Tipo de conta e ferramentas → Mudar para conta profissional** (Criador ou Empresa).

## Passo 2 — Criar o app na Meta
1. Acesse https://developers.facebook.com → **Meus apps → Criar app**.
2. Caso de uso: **"Gerenciar mensagens e conteúdo no Instagram"**.
3. No painel do app, vá em **Instagram → Configuração da API com login do Instagram**.
4. Em **"Gerar tokens de acesso"**, clique em **Adicionar conta** e entre com seu Instagram.
5. Clique em **Gerar token** → copie o token (já é de longa duração, 60 dias).
6. Na mesma tela aparece o **ID da conta** (número) → copie também.

> Permissões necessárias: `instagram_business_basic` e `instagram_business_content_publish` (já vêm marcadas nesse caso de uso).
> Não precisa de revisão do app: em modo de desenvolvimento ele funciona na sua própria conta.

## Passo 3 — Criar o repositório no GitHub
1. Crie um repositório **público** (os vídeos precisam de URL pública para o Instagram baixar).
2. Suba estes arquivos + uma pasta `videos/` com seus MP4.
3. Vá em **Settings → Secrets and variables → Actions → New repository secret** e crie:
   - `IG_TOKEN` = o token do passo 2
   - `IG_USER_ID` = o ID da conta do passo 2

## Passo 4 — Testar
Aba **Actions → Postar no Instagram → Run workflow**. Em 1–3 min o Reel aparece no seu perfil.
Depois disso ele roda sozinho a cada hora.

## Formato do posts.csv
```
video,legenda
meu-video.mp4,"Minha legenda com #hashtags"
```
O nome do vídeo tem que ser igual ao arquivo em `videos/`. Use legendas entre aspas.

## Requisitos dos vídeos
MP4 (H.264 + AAC), vertical 9:16 de preferência, 3 s a 15 min, até 300 MB.
Dica: arquivos acima de 100 MB não sobem no GitHub — comprima antes.

## Renovar o token (a cada ~50 dias)
No seu PC:
```
set IG_TOKEN=seu_token_atual
python postar.py --renovar
```
Copie o novo token e atualize o secret `IG_TOKEN` no GitHub.

## Observações
- O cron do GitHub usa UTC e às vezes atrasa alguns minutos — normal.
- Repositórios sem atividade por 60 dias têm o agendamento pausado; o commit do `postados.txt` evita isso enquanto houver fila.
- Limite da API: 100 posts / 24 h.
