# Trinity Seven Offline

Patch que deixa **トリニティセブン 夢幻図書館と第7の太陽** (*Trinity Seven: Phantasm Library & Seventh Sol*, Android, versão 7.7) jogável de novo, sem os servidores originais da Poppin Games, que foram desligados.

O servidor do jogo passa a rodar **dentro do próprio app**. Não precisa de PC, de outro app nem de internet.

> **Aviso legal.** Projeto de preservação, sem fins lucrativos e sem ligação com Avex Technologies, Poppin Games Japan ou KADOKAWA. Este repositório **não distribui o APK nem arquivos do jogo**, apenas as ferramentas que alteram uma cópia que você já tem. Trinity Seven © Kenji Saito, Akinari Nao / KADOKAWA.
>
> O código deste repositório usa a licença [MIT](LICENSE). Ela não cobre o jogo, que continua pertencendo aos detentores dos direitos.

---

## Versão 0.9

### O que funciona

- Abertura, termos, história inicial e tutorial completo (a primeira personagem, Lilith, é entregue pelo próprio tutorial).
- Batalha automática, toques, chefes, desbloqueio de histórias, Magic Training e progresso offline.
- Presentes e notícias (vazios), backup e restauração de dados ("Data Backup" / "Change Device").
- Tudo isso em **modo avião**.

### Alterações em relação ao jogo original

#### 1. Servidores redirecionados para o próprio aparelho
O jogo tinha três endereços fixos no código: `app-tri.poppin-games.com` (API) e dois CloudFront (arquivos e páginas). Todos estão fora do ar, e sem eles o jogo parava na tela 「予期しないエラーが発生しました」.
`patch_apk.py` reescreve as **54 strings** com esses endereços dentro de `global-metadata.dat`, trocando-as por `http://127.0.0.1:8080`.

#### 2. Servidor embutido no APK
Um `ContentProvider` Java (`com.t7stub.StubProvider`, em `classes4.dex`) sobe um servidor HTTP em `127.0.0.1:8080` quando o app abre, antes do Unity. Ele substitui a API original:

| Rota | Resposta |
|---|---|
| `version_index`, `closing_get`, `user_generateId`, `time_index` | versão aceita, servidor aberto, ID `100000001`, hora do aparelho |
| `ban_get`, `news_get`, `present_index`, `saveRefresh_index`, `assetBundle_index`, `article_index`, `cropro_getCampaigns`, `bbs_get`, `question_*`, `storyMaker_*List`, `ranking_getTournament`, `ranking_getTeamRankList` | `[]` (lista vazia, que é o formato que o jogo espera) |
| `text_index` | texto de compartilhamento |
| `savedata/index.php` | backup real (ver item 4) |
| `/release/...` | página HTML simples para Ajuda, Termos, Privacidade e Créditos |
| qualquer outra | `{}` |

Os dados do jogo (personagens, inimigos, fases, tutorial) já estão dentro do APK; nada é baixado.

#### 3. Correção do inimigo que não morria e do tutorial que não aparecia
Em aparelhos com idioma que usa **vírgula decimal** (português, espanhol, francês, alemão…), `EnemyManager.UpdateHpBar` chama `Single.Parse`, que lança exceção. O inimigo nunca é marcado como "existente": a barra de HP fica vazia, nenhum dano é aplicado, os toques viram bolas no tabuleiro e os diálogos do tutorial não continuam.
O servidor embutido força a cultura **ja-JP** (`Locale.setDefault`, também com ponto decimal) na abertura do app e de novo antes da Activity do Unity, porque o Android reaplica o idioma do sistema nesse momento.
O idioma forçado é o japonês por padrão, com os textos como no original; `build.py --lang en` força `Locale.US` e a interface, os termos e os títulos de capítulo aparecem em inglês.

#### 4. Backup e restauração funcionando
O botão "Data Backup" gera um ID e um código de troca de aparelho; "Change Device" restaura com eles. O protocolo original (`EasySaveHelper`) foi reimplementado: `upload`, `download` e `delete`, com resposta vazia para sucesso e `05` para não encontrado.
Antes desta versão, o servidor respondia `{}`, que o jogo interpretava como **sucesso**. Uma restauração gravaria `{}` como save e apagaria os dados locais.
O backup fica em `Android/data/com.avex.trinityseven/files/savedata/`.

#### 5. Recompensas por vídeo sem anúncio
`AdManager.IsVideoSkip` passa a retornar `true`. É o modo "pular anúncios" que o jogo vendia: todo botão de "assistir vídeo" (caixa de vídeo, bônus de login, mineração, prestage, revanche, Story Maker) entrega a recompensa na hora, sem carregar o AdMob.

#### 6. Funciona sem internet
`NetworkHelper.IsCanConnectNetwork` passa a retornar `true`, já que o servidor é local. Isso libera em modo avião o backup no título, o backup automático e a checagem de horário feita ao coletar recompensas (ex.: Magic Training). Antes, todos mostravam "Cannot connect to the network".

#### 7. Assinatura
O APK é reassinado com uma chave própria (debug). Por isso não instala por cima da versão da Play Store.

### Limitações conhecidas

- **Idioma fixo** (japonês ou inglês, escolhido ao gerar o APK), independente do idioma do sistema (consequência do item 3).
- **Recursos online não funcionam:** ranking, torneio, times, perguntas e respostas, compartilhamento do Story Maker, compras (Google Play Billing) e Google Play Games. Eles abrem vazios ou falham sem travar o jogo.
- **Patches nativos (itens 5 e 6) só para arm64.** Em aparelhos antigos de 32 bits o jogo roda, mas sem esses dois.
- **O backup é apagado junto com o app** (ao desinstalar ou limpar dados). Para trocar de aparelho, copie a pasta `savedata` para o novo (veja abaixo).
- **Regra original de 1 dia:** depois de um backup ou restauração, o jogo bloqueia novo backup por 24 h.
- **O ID de usuário é sempre `100000001`.** Não importa offline, mas impede um servidor compartilhado entre jogadores.
- **Com internet, ainda aparecem banners de anúncio** (anúncios de teste do AdMob).
- **Testado** no emulador Android 11 (API 30, imagem x86_64 com tradução arm64). Recompensas por vídeo foram verificadas no código e na memória do jogo, mas ainda não acionadas na tela (liberam mais adiante no jogo).

---

## Instalação

1. Desinstale o Trinity Seven original, se estiver instalado (a assinatura é diferente).
2. Copie o APK gerado para o celular e toque nele para instalar. No Xiaomi/MIUI, instalar pelo `adb` costuma ser bloqueado; instale pelo gerenciador de arquivos.
3. Na primeira abertura, cancele o aviso do Google Play Games.

### Trocar de aparelho

No aparelho antigo, faça o backup pelo título e anote o ID e o código. Do Android 11 em diante, a pasta `Android/data` só é acessível pelo PC:

```bash
adb pull /sdcard/Android/data/com.avex.trinityseven/files/savedata savedata-backup
```

Instale no aparelho novo, abra o jogo uma vez e envie a pasta:

```bash
adb push savedata-backup/. /sdcard/Android/data/com.avex.trinityseven/files/savedata/
```

Depois use "Change Device" no título com o ID e o código.

---

## Como gerar o APK

### Requisitos

- APK original `trinity-seven-7-7.apk` (versão 7.7, versionCode 88). SHA-256:
  `13b3b9f2e9e127fc13fd3b636b376fdd66bddd356cb44e996caa3470b3ca958c`
- Python 3.9 ou mais novo (só biblioteca padrão)
- JDK 11 a 21 (`javac --release 8`)
- Android SDK: `platforms/android-30` e `build-tools` (para o `d8`)
- [apktool](https://apktool.org/) 3.0.3 e [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer) 1.3.0

### Passos

Coloque `apktool.jar` e `uber-apk-signer-1.3.0.jar` nesta pasta (ou passe `--apktool` e `--signer`) e rode:

```bash
python build.py trinity-seven-7-7.apk --sdk /caminho/do/android-sdk
```

O script confere o SHA-256 do APK, instala o servidor embutido, aplica os patches e assina. O APK final fica em `out/Trinity7-offline.apk`. `--lang en` gera a versão em inglês (`out/Trinity7-offline-en.apk`); o padrão é `ja`. `--host` troca o endereço do servidor (ver abaixo).

### Servidor no PC (opcional)

Para usar um servidor no PC em vez do embutido (útil para depurar, porque ele registra todas as requisições), gere o APK com `--host http://IP-DO-PC:8080` e rode:

```bash
python -I server/stub_server.py 8080
```

O endereço novo precisa ter no máximo 32 caracteres (tamanho de `https://app-tri.poppin-games.com`). Os backups ficam em `server/savedata/`.

### Testes

```bash
python -I server/test_stub.py http://127.0.0.1:8080
```

Testa qualquer um dos dois servidores por HTTP (rotas, formatos e backup completo) e confere se o servidor Python e o Java têm a mesma lista de rotas. Para testar o servidor embutido, abra o jogo no aparelho e encaminhe a porta com `adb forward tcp:8080 tcp:8080`.

---

## Estrutura

| Arquivo | Função |
|---|---|
| `build.py` | gera o APK a partir do original (um comando) |
| `server/embedded/com/t7stub/StubProvider.java` | servidor embutido no APK e correção de idioma |
| `server/stub_server.py` | mesmo servidor em Python, para rodar no PC |
| `server/patch_apk.py` | troca os endereços no `global-metadata.dat` e aplica `patch_lib.py` |
| `server/patch_lib.py` | patches em `libil2cpp.so` (arm64) |
| `server/test_stub.py` | testes dos dois servidores |
| `HANDOFF.md` | notas técnicas de engenharia reversa (em inglês) |

A análise foi feita com [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) e capstone. Os endereços (RVAs) em `patch_lib.py` valem só para a versão 7.7; o script confere os bytes originais antes de alterar e aborta se não baterem.
