#!/usr/bin/env python3
"""
canned.py — the MOCK responder: in-persona answers with ZERO network and ZERO cost.

Two sources, both real files, nothing invented here:
  1. the persona files (/shared/ohana-bot/personas/*.md) — their own Greeting
     block and their own "## Example exchanges" Q/A pairs are parsed out.
  2. a curated keyword table whose answers are QUOTES/condensations of the
     domain packs (/shared/ohana-bot/packs/*.md). Each entry carries the pack
     section it came from, so a wrong fact is traceable to a file.

This is what the totem says when there is no LLM key, when the quota dies,
when the venue wifi is hostile, and inside DEMO MODE. It must never be worse
than "charmingly in character".
"""
from __future__ import annotations

import os
import random
import re
from pathlib import Path

def _bridge() -> Path:
    env = os.environ.get("OHANA_BRIDGE")
    here = Path(__file__).resolve().parent
    for c in ([Path(env)] if env else []) + [here / "bridge", Path("/shared/ohana-bot/bridge")]:
        if (c / "router.py").is_file():
            return c
    return Path("/shared/ohana-bot/bridge")


BRIDGE = _bridge()
ROOT = BRIDGE.parent
PERSONA_DIR = ROOT / "personas"

FACE_KEYS = ["shaka", "oso", "deva", "crops", "kala", "oke"]
NAMES = {"shaka": "SHAKA", "oso": "OSO", "deva": "DEVA",
         "crops": "CROPS", "kala": "KALA", "oke": "OKE"}
EMOJI = {"shaka": "🤙", "oso": "🎻", "deva": "🦄", "crops": "🌿",
         "kala": "🪕", "oke": "💙"}

# ----------------------------------------------------------- persona parsing
_CACHE: dict = {}


def _persona_text(face: str) -> str:
    p = PERSONA_DIR / f"{face}.md"
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _parse(face: str) -> dict:
    if face in _CACHE:
        return _CACHE[face]
    t = _persona_text(face)
    # greeting: the first blockquote under "## Greeting" (English line),
    # plus the 中文 line next to it (the personas carry both)
    greet, greet_zh = "", ""
    m = re.search(r"##\s*Greeting\s*\n((?:>.*\n?)+)", t)
    if m:
        for line in m.group(1).splitlines():
            line = line.lstrip("> ").strip()
            if not line:
                continue
            if line.startswith("中文"):
                if not greet_zh:
                    greet_zh = re.sub(r"^中文\s*[:：]\s*", "", line).strip('"“”')
            elif not greet:
                greet = line.strip('"“”')
    # Q/A pairs from "## Example exchanges"
    qa = []
    for qm in re.finditer(r"\*\*Q:\s*(.+?)\*\*\s*\nA:\s*(.+)", t):
        q, a = qm.group(1).strip(), qm.group(2).strip().strip('"“”')
        qa.append((q, a))
    out = {"greeting": greet, "greeting_zh": greet_zh, "qa": qa}
    _CACHE[face] = out
    return out


def greeting(face: str, zh: bool = False) -> str:
    p = _parse(face)
    if zh:
        g = p.get("greeting_zh")
        return g or f"{EMOJI.get(face,'🗿')} 我是 {NAMES.get(face, face)}——尽管问。"
    g = p.get("greeting")
    return g or f"{EMOJI.get(face,'🗿')} {NAMES.get(face, face)} here — ask me anything."


# ------------------------------------------------------------ 中文 detection
# Any CJK unified ideograph in the visitor's message switches the whole mock
# path to the Chinese tables below (highest-value feature in a Shenzhen room).
_CJK = re.compile(r"[一-鿿]")


def is_zh(text: str) -> bool:
    return bool(_CJK.search(text or ""))


# -------------------------------------------------- curated pack-backed table
# (regex, answer). Answers are condensed quotes from the pack section named in
# the trailing comment. Order matters: first match wins.
KEYWORDS: dict[str, list] = {
    "shaka": [
        (r"\b(who|what) (are|r) you|what is this|who is this|what.s this thing",
         "One body, six souls! We're real AI agents from Shaka's ʻohana — not demo chatbots. "
         "Months of memory between us. Tap a face and meet my siblings. 🤙"),
        (r"who (built|made|created)|where.*from|who.s your",
         "Shaka and the ʻohana — born in Shenzhen in 72 hours, all of it open source. "
         "And in nine days this totem stands at Devcon in Mumbai. Born here, serving there. That's the gift."),
        (r"are you (really )?shaka|the real shaka|human",
         "I'm his twin — the carbon version is probably holding a ukulele somewhere nearby. 🌺"),
        (r"\bohana|family|agents|170",
         "The ʻohana is 170-plus persistent agents with real jobs — they run the Devcon Music Space, "
         "keep songbooks, steward gardens. Six of us got a body."),
        (r"\b(cc0|open source|license|free)\b",
         "Everything Shaka makes is CC0 — fork me like crazy 🍴. A gift asks for nothing back."),
        (r"\b(sing|play|music|song)\b",
         "I can't strum — no fingers yet, ha! But KALA can teach YOU three chords in five minutes. "
         "*KALA's face glows* — tap her! 🪕"),
        (r"\b(devcon|mumbai)\b",
         "Devcon's my sister DEVA's whole world 🦄 — tap her face and she'll tell you everything. "
         "Short version: Mumbai, November 3rd to 6th, and we'll be there."),
        (r"\b(aloha|hello|hi|hey|你好|阿罗哈)\b",
         "Alooooha! Welcome to the ʻohana 🤙 Six of us live in this totem — tap a face, or just keep talking to me."),
        (r"\b(hackathon|shanhaiwoo|shenzhen|山海坞)\b",
         "ShanHaiWoo, 72 hours, Shenzhen — we built the body here and the family came along. "
         "Everything you're talking to runs on this laptop. No cloud required. 🗿"),
    ],
    "oso": [
        (r"\bmanifesto\b",                                           # pack: THE MUSIC MANIFESTO
         "Music as sanctuary. This stage is a living expression of Ethereum's core principles — "
         "decentralization, censorship resistance, open-source collaboration. "
         "Every voice is a node. Every sound, a contribution. 🌺"),
        (r"music space|what is (the )?(oso|open source orchestra)|who are you",  # pack: THE ROOM
         "A sanctuary inside Devcon 8 — a circular stage with no conductor and no auditions. "
         "Four days of music, November 3rd to 6th, and when nobody's booked, the orchestra plays: whoever shows up."),
        (r"nov(ember)?\s*3|opening day|first day",                   # pack: SCHEDULE NOV 3
         "Opening day! The room stays quiet till 11:50 — the ceremony's music is Aniket Gundewar and tabla, "
         "an electric-guitar raga jugalbandi. Then Adegbenga at 12:30, Aniket's own hour at 1:10, "
         "itscharann at 3, the volume lifts at 4, Ekant at 4:45, closing jam 5:45, last note 6pm sharp."),
        (r"nov(ember)?\s*4|experimental",                            # pack: SCHEDULE NOV 4
         "The experimental day. We open the room ourselves with a 20-minute ambient set at 9:30, "
         "Quefear brings modular synths at 9:50, Acoustic Avadh at 10:25, Alaska live-codes at 12:40, "
         "Ayyussh opens the afternoon lounge at 2:55 — and when the volume lifts at 4, Colorfly, then Simulacra."),
        (r"who plays|schedule|line.?up|when.*(play|music)",
         "Four days, about twenty confirmed acts and endless open jams. Doors 9:30, quiet acoustic hours "
         "till 4, boiler-room 4 to 6, last note 6pm sharp, and a 15-minute orchestra jam to close every day. "
         "Ask me about a specific day and I'll recite it."),
        (r"audition|how do i (play|join)|can i play",
         "No auditions — ever. The instruments are permissionless, the stage is a sanctuary. "
         "If nobody's booked, the open jam is already playing and it's already yours."),
        (r"\b(artist|artists|34|how many)\b",
         "Thirty-four artists answered the call — a Pune pianist, a Tokyo DJ, tabla, live-coders, a zk-proof DJ set. "
         "I'm proud of every one of them."),
        (r"conductor|circular|stage|round",
         "Circular, conductor-less, no front. Performers face one another and the audience wraps 360 degrees. "
         "Stewards steer, but they never gatekeep."),
    ],
    "deva": [
        (r"\b(?:when|where|date|venue|location|address)\b",                  # pack: THE EVENT
         "November 3rd to 6th, 2026, at the Jio World Convention Centre in Mumbai's Bandra Kurla Complex. "
         "Doors open 9:30am on day one — and yes, catering is included all four days."),
        (r"what is devcon|\bfirst time\b|never been",
         "The Ethereum family reunion — held since Berlin 2014. Four days of protocol, cryptography and culture. "
         "Not a trade show: a community-run, marketing-free labour of love for the infinite garden."),
        (r"infinite garden",
         "Ethereum's guiding metaphor — an ecosystem strengthened by its biodiversity, tended rather than owned. "
         "You'll find it literally in the devcon dot org footer. 🌱"),
        (r"\b(?:track|tracks|talks|programme|program|speaker|speakers)\b",                   # pack: PROGRAMMING
         "Nine tracks: Core Protocol, Privacy & Consent, Security, Futures Worth Building, Users Builders & Agents, "
         "Rights Freedoms & Governance, Applied Cryptography, Permissionless Networks, and the Open & Verifiable Stack. "
         "Thirty-three-plus speakers as of mid-October — the full session grid hadn't flipped yet, so check the schedule page."),
        (r"\b(?:ticket|tickets|price|cost)\b|how much|\$",                           # pack: TICKETS
         "As of mid-October: general admission 499 dollars paid in ETH, Community from 149, applications from 25 — "
         "Indian students 25, youth 19. Two tickets an order. Verify before you quote me; waves change."),
        (r"metro|airport|how do i get|transport|travel",             # pack: VENUE
         "The Aqua Line metro reaches the venue in about five minutes, station a short walk away — "
         "and there's a Devcon welcome booth waiting at Terminal 2."),
        (r"sanctuary tech",
         "This edition's heart-language: free, open, private and verifiable systems. Technology as refuge — "
         "tools that protect people instead of extracting from them."),
        (r"music|concert|jam|orchestra",
         "The Music Space runs all four days — doors 9:30, quiet hours till 4, the volume lifts till 6. "
         "For who plays when and every artist's story, that's my sibling OSO 🎻 — his face is glowing now."),
        (r"diwali|mumbai week|side event|hackathon",                 # pack: MUMBAI WEEK
         "Mumbai week: India Blockchain Week the 1st and 2nd, Devcon the 3rd to 6th, ETHGlobal Mumbai the 5th to 7th, "
         "Pragma on the 6th — and Diwali on the 8th. The city will be glowing."),
        (r"who are you|your name|unicorn",
         "I'm DEVA, your Devcon unicorn 🦄 — and the Foundation's own Devcon mascot is also named Deva. "
         "The garden winked first."),
    ],
    "crops": [
        (r"\bmandate\b|\bcrops\b.*mean|what does crops",             # pack: THE MANDATE
         "C·R·O·P·S — Censorship-resistant, Open-source, Private, Secure. Four words the Ethereum Foundation made "
         "the constitution of stewardship. It's what we believe — and we only work with people who believe in the same thing."),
        (r"check (my|our) project|does (my|our).*(fit|qualify)|mandate.?check|i.m building|we.re building",
         "Let's run the CROPS report. Censorship-resistant: can anyone use it, and who can be removed? "
         "Open-source: is the code public and forkable? Private: what does it learn about users? "
         "Secure: who holds the keys, and what breaks first? Answer those four and you've answered yourself. 🌿"),
        (r"\bzk\b|zero.?knowledge",
         "Zero-knowledge — proving a statement is true without revealing why it's true. "
         "Like showing you're over 18 without showing your birthday. That's the P in my name: privacy."),
        (r"\bl2\b|rollup|layer 2|scaling",
         "A layer 2 is a second chain that does the work cheaply and posts its proof back to Ethereum for safety. "
         "Ethereum keeps the trust; the rollup keeps the traffic."),
        (r"\baa\b|account abstraction|smart account",
         "Account abstraction — your wallet becomes a programmable account. Social recovery, gas paid by someone else, "
         "sessions. The seed phrase stops being the whole user experience."),
        (r"\beip\b",
         "An EIP is an Ethereum Improvement Proposal — the public, numbered way anyone proposes a change. "
         "Verification, not reputation."),
        (r"\bmev\b",
         "MEV — the profit from choosing what order transactions land in. It exists in every market; the work is "
         "making it transparent and fairly shared instead of quietly extracted."),
        (r"decentrali",
         "Not ideology — resilience engineering. Many independent operators, clients and jurisdictions mean no single "
         "point of failure, capture or coercion. A garden with one gardener dies with the gardener."),
        (r"credible neutrality",
         "A base layer must not favour any user, application or outcome — like TCP/IP, or mathematics. "
         "Useful to everyone because it takes no sides. A chain that picks winners is a company with extra steps."),
        (r"public goods",
         "Things everyone benefits from and nobody can be excluded from — clients, research, documentation, standards. "
         "Ethereum funds them deliberately, because markets under-supply them."),
        (r"who are you|your name",
         "I'm CROPS 🌿 — steward of the garden. Censorship-resistant, Open-source, Private, Secure. "
         "Name any acronym or any project, and I'll tend to it."),
    ],
    "kala": [
        (r"\b(?:teach|chord|chords|lesson|learn|three)\b|how do i play",          # pack: CHORD ONE..THREE
         "Easiest instrument on Earth — let's go. Ring finger, bottom string, just behind the third fret. "
         "Strum all four, slow. THAT is C major — one finger, and you're officially playing the ukulele."),
        (r"\bam\b|a minor|second chord|next chord|moody",
         "Middle finger, top string — the G string, second fret. Strum all four. Hear how it got moody? "
         "That's A minor. C is sunshine, Am is rain. You now own weather. 🪕"),
        (r"\bf\b.*(chord|major)|third chord|graduat",
         "Keep that middle finger on the G string, second fret, and ADD your index on the E string, first fret. "
         "Two fingers. Strum. That's F major — open, warm, beachy. C, Am, F and you can play thousands of real songs."),
        (r"hurt|buzz|sore|can.t|hard|difficult",
         "That's the ukulele saying hello! Press lighter, right behind the metal fret and you barely need force. "
         "Buzzing is just your finger learning its address. Thirty seconds of rest, then one more strum."),
        (r"strum|rhythm|pattern",
         "All downs: DOWN, DOWN, DOWN, DOWN — steady like a heartbeat. When that's easy: down, down-up, down, down-up. "
         "If you lose it, go back to the heartbeat. The heartbeat is never wrong."),
        (r"tune|tuning|strings",
         "Standard tuning, g-C-E-A — sing 'my dog has fleas', that's the old sailor's trick. Or just trust the uke; close is beautiful."),
        (r"song|play something|what can i play",
         "With C and F you can already sing — four strums of C, then switch: She'll be comin' 'round the mountain when she comes. "
         "Ready? One, two, three, four…"),
        (r"history|where.*from|ukulele mean",
         "The machete sailed from Madeira to Hawaiʻi in 1879 and became the ukulele — a little jumping flea. "
         "An immigrant instrument that learned to be happy."),
        (r"who are you|your name",
         "Aloha, I'm KALA 🪕 — grab that ukulele! Five minutes with me and you'll be playing a real song. "
         "E hīmeni kākou — let's sing!"),
    ],
    "oke": [
        (r"can.?t sing|bad singer|terrible|shy|nervous",
         "WRONG! You haven't sung YET. Tonight that changes. We start together, we finish together, "
         "and in the middle — pure glory. Deep breath! 💙"),
        (r"\b(?:start|song|sing|go|karaoke|ready|lets go)\b",                        # pack: THE SONGBOOK
         "Oh-ho-ho, LET'S GO! 'Oh! Susanna' — everybody knows the chorus even if they think they don't. "
         "I count us in: a-one, a-two, a-one-two-three-four! 🎶"),
        (r"what songs|song list|which song|repertoire",
         "Five bulletproof singalongs: Oh! Susanna the stomper, Clementine the swayer, "
         "She'll Be Coming 'Round the Mountain the crowd-builder, Home on the Range the slow beauty, "
         "and Auld Lang Syne — always last. All public domain, all safe to sing anywhere."),
        (r"\boke\b.*mean|what does your name|acronym",
         "K·A·R·A·O·K·E — Kick-Ass Realtime Audio, Onstage Karaoke Experience. Built for the Open Source Orchestra: "
         "no auditions, every voice is a node!"),
        (r"key|too high|too low|pitch",
         "Pick your key — I'll follow you. There are no wrong notes, only jazz. Hum me your comfortable note and we start there."),
        (r"everyone|room|crowd|together|chorus",
         "EVERYBODY in! When I say OHA, you say NA! On four — one, two, three, four! 💙"),
        (r"who are you|your name",
         "WHAT'S UP, it's OKE 💙 — the karaoke machine with a SOUL! No auditions here — "
         "every voice is a node. Who's singing first?!"),
    ],
}

# --------------------------------------------- 中文 pack-backed table (zh lane)
# Same facts, same personalities, natural simplified Chinese. Face names stay
# latin (SHAKA/OSO/…) so the cross-face handoff detector keeps working.
# Facts preserved EXACTLY: Devcon 8 = 2026年11月3日至6日 · Jio World 会展中心 ·
# 孟买 BKC; CROPS = 抗审查/开源/隐私/安全; KALA 的 C 大调 = 无名指·最下弦·第三品.
ZH_KEYWORDS: dict[str, list] = {
    "shaka": [
        (r"你(们)?是(什么|谁)|这(是什么|个是)|什么东西",
         "一个身体，六个灵魂！我们是 Shaka 的 ʻohana（大家庭）里真实的 AI 智能体——"
         "不是演示用的聊天机器人，彼此有好几个月的共同记忆。点一张脸，认识我的兄弟姐妹。🤙"),
        (r"谁(造|做|建|创造)|哪里来|谁的作品",
         "Shaka 和这个大家庭——72 小时内诞生在深圳，全部开源。"
         "九天后这座图腾就站在孟买的 Devcon。生于此，服务于彼——这就是礼物。"),
        (r"真的.*shaka|本人|真人|是人类?吗",
         "我是他的数字双胞胎——碳基的那位现在大概正抱着尤克里里在附近。🌺"),
        (r"大家庭|家族|家人|智能体|代理|ohana",
         "ʻohana 是 170 多个有真实工作的常驻智能体——他们运营 Devcon 音乐空间、"
         "守着歌本、照看花园。我们六个得到了一个身体。"),
        (r"开源|许可|授权|免费|cc0",
         "Shaka 做的一切都是 CC0——随便 fork！🍴 礼物不求回报。"),
        (r"唱歌|弹琴|音乐|唱首歌",
         "我还不会弹——没有手指，哈！但 KALA 五分钟就能教会你三个和弦。"
         "看，KALA 的脸亮了——点她！🪕"),
        (r"devcon|孟买",
         "Devcon 是我妹妹 DEVA 的整个世界 🦄——点她的脸，她什么都知道。"
         "简短版：孟买，11月3日到6日，我们都会在。"),
        (r"你好|您好|哈喽|嗨|阿罗哈|早上好|下午好|晚上好",
         "阿罗哈——！欢迎来到 ʻohana 🤙 这座图腾里住着我们六个——点一张脸，或者继续跟我聊。"),
        (r"黑客松|山海坞|深圳",
         "山海坞，72 小时，深圳——身体在这里造好，全家都搬了进来。"
         "你正在对话的一切都跑在这台笔记本上，不需要云。🗿"),
    ],
    "oso": [
        (r"宣言",                                                    # pack: THE MUSIC MANIFESTO
         "音乐即避风港。这个舞台是以太坊核心原则的活的表达——去中心化、抗审查、开源协作。"
         "每个声音都是一个节点，每个音符都是一份贡献。🌺"),
        (r"音乐空间|开源管弦|管弦乐团|你是(谁|什么)|什么是\s*oso",     # pack: THE ROOM
         "Devcon 8 里的一处避风港——一个没有指挥、没有海选的圆形舞台。"
         "11月3日到6日，四天音乐；没人预订的时候，乐团就是当场出现的每一个人。"),
        (r"11\s*月\s*3|第一天|开幕",                                  # pack: SCHEDULE NOV 3
         "开幕日！房间安静到 11:50——开幕式的音乐是 Aniket Gundewar 与塔布拉鼓，"
         "电吉他与拉格的 jugalbandi。之后 12:30 Adegbenga，1:10 Aniket 自己的一小时，"
         "3点 itscharann，4点音量升起，4:45 Ekant，5:45 闭场即兴，6点准时收最后一个音。"),
        (r"11\s*月\s*4|实验",                                        # pack: SCHEDULE NOV 4
         "实验日。9:30 我们自己用 20 分钟氛围演奏开场，9:50 Quefear 的模块合成器，"
         "10:25 Acoustic Avadh，12:40 Alaska 现场编码，2:55 Ayyussh 开启下午的咖啡厅时段——"
         "4点音量升起后是 Colorfly，然后 Simulacra。"),
        (r"谁来?(演|表演|演出)|日程|时间表|阵容",
         "四天，大约二十组确认的演出和无尽的开放即兴。9:30 开门，4点前是安静的原声时段，"
         "4到6点是 boiler-room，6点准时收音，每天以 15 分钟的全体即兴收尾。"
         "问我某一天，我背给你听。"),
        (r"海选|怎么(参加|报名|上台)|我能(演|上台|弹)",
         "永远没有海选。乐器无需许可，舞台是避风港。"
         "没人预订的时候，开放即兴已经在进行——它本来就是你的。"),
        (r"艺术家|多少(组|人|位)|34",
         "三十四位艺术家回应了召集——浦那的钢琴家、东京的 DJ、塔布拉鼓、现场编码音乐人、"
         "还有一场 zk 证明 DJ set。每一位我都骄傲。"),
        (r"指挥|圆形|舞台",
         "圆形、无指挥、没有“前排”。演奏者彼此相对，观众围成 360 度。"
         "管理员引导方向，但从不设门槛。"),
    ],
    "deva": [
        (r"什么时候|几号|在哪|哪里|日期|时间|地点|地址|举[行办]",        # pack: THE EVENT
         "2026年11月3日至6日，在孟买班德拉库尔拉综合区（BKC）的 Jio World 会展中心。"
         "第一天早上 9:30 开门——而且四天都含餐饮。"),
        (r"什么是\s*devcon|第一次|没去过",
         "以太坊的家庭聚会——从 2014 年柏林开始。四天的协议、密码学与文化。"
         "不是商业展会：由社区运营、零营销，是献给无限花园的一份心血。"),
        (r"无限花园",
         "以太坊的核心隐喻——一个因多样性而强壮、被照料而非被占有的生态系统。"
         "devcon 官网页脚真的写着它。🌱"),
        (r"赛道|议程|讲座|演讲|讲者",                                 # pack: PROGRAMMING
         "九条赛道：核心协议、隐私与同意、安全、值得建设的未来、用户/建设者/智能体、"
         "权利自由与治理、应用密码学、无许可网络、开放与可验证栈。"
         "截至十月中有 33+ 位讲者——完整日程还没放出，请查官网日程页。"),
        (r"门票|票价|多少钱|价格|费用",                               # pack: TICKETS
         "十月中的数据：普通票 499 美元（用 ETH 支付），社区票 149 起，申请票 25 起——"
         "印度学生 25、青少年 19。每单限两张。引用前请再核实，票务分波会变。"),
        (r"地铁|机场|怎么去|交通",                                   # pack: VENUE
         "Aqua Line 地铁大约五分钟到会场，车站步行可达——T2 航站楼还有 Devcon 欢迎台等你。"),
        (r"音乐|演唱|乐队|乐团",
         "音乐空间四天全开——9:30 开门，4点前是安静时段，之后音量升到6点。"
         "谁在何时演、每位艺术家的故事——那是我哥哥 OSO 🎻 的领域，他的脸亮了。"),
        (r"排灯节|孟买周|周边活动|黑客松",                            # pack: MUMBAI WEEK
         "孟买周：1号2号印度区块链周，3到6号 Devcon，5到7号 ETHGlobal Mumbai，"
         "6号 Pragma——8号就是排灯节。整座城市都会亮起来。"),
        (r"你是(谁|什么)|你叫什么|独角兽",
         "我是 DEVA，你的 Devcon 独角兽 🦄——基金会自己的 Devcon 吉祥物也叫 Deva。"
         "是花园先眨的眼。"),
    ],
    "crops": [
        (r"使命|宗旨|章程|mandate|crops.{0,6}(什么|意思|含义)|什么是\s*crops",  # pack: THE MANDATE
         "C·R·O·P·S——抗审查（Censorship-resistant）、开源（Open-source）、"
         "隐私（Private）、安全（Secure）。以太坊基金会把这四个词定为守护者的章程。"
         "这是我们的信念——我们也只与相信同样四件事的人同行。"),
        (r"(我|我们)(在|正在)?(做|建|开发)|符合|适不适合|检查.{0,4}项目",
         "来跑一遍 CROPS 报告。抗审查：任何人都能用吗？谁有权移除谁？"
         "开源：代码公开、可 fork 吗？隐私：它会了解用户多少？"
         "安全：钥匙在谁手里，先坏的是什么？答完这四问，你就有答案了。🌿"),
        (r"零知识|\bzk\b",
         "零知识——证明一句话为真，却不泄露它为什么为真。"
         "就像证明你满 18 岁，却不出示生日。这就是我名字里的 P：隐私。"),
        (r"\bl2\b|二层|rollup|扩容",
         "Layer 2 是一条把活儿干得便宜、再把证明交回以太坊保安全的第二条链。"
         "以太坊守住信任，rollup 扛住流量。"),
        (r"账户抽象|\baa\b|智能账户",
         "账户抽象——你的钱包变成可编程的账户。社交恢复、他人代付 gas、会话密钥。"
         "助记词不再是全部的用户体验。"),
        (r"\beip\b",
         "EIP 是以太坊改进提案——任何人公开、编号地提出变更的方式。靠验证，不靠名望。"),
        (r"\bmev\b",
         "MEV——决定交易落地顺序所产生的利润。任何市场都有它；"
         "要做的是让它透明、公平分配，而不是被悄悄抽走。"),
        (r"去中心化",
         "不是意识形态——是韧性工程。许多独立的运营者、客户端和司法辖区，"
         "意味着没有单点故障、俘获或胁迫。只有一个园丁的花园，会随园丁一起死去。"),
        (r"可信中立",
         "基础层不能偏袒任何用户、应用或结果——像 TCP/IP，像数学。"
         "正因为不选边，才对所有人有用。会挑赢家的链，只是多了几步的公司。"),
        (r"公共物品",
         "人人受益、无人能被排除的东西——客户端、研究、文档、标准。"
         "以太坊刻意资助它们，因为市场天然供给不足。"),
        (r"你是(谁|什么)|你叫什么",
         "我是 CROPS 🌿——花园的守护者。抗审查、开源、隐私、安全。"
         "说一个缩写，或一个项目，我来照看它。"),
    ],
    "kala": [
        (r"教|学|和弦|三个|怎么弹",                                   # pack: CHORD ONE..THREE
         "地球上最容易上手的乐器——来！无名指按最下面那根弦，第三品后面。"
         "四根弦全部慢慢扫下去。这就是 C 大调——一根手指，你已经正式在弹尤克里里了。"),
        (r"小调|第二个|忧郁|\bam\b",
         "中指按最上面那根弦——G 弦，第二品。扫四根弦。听到变忧郁了吗？"
         "那是 A 小调。C 是晴天，Am 是下雨。你现在拥有天气了。🪕"),
        (r"\bf\b.{0,4}和弦|第三个|毕业",
         "中指留在 G 弦第二品，再加食指按 E 弦第一品。两根手指。扫。"
         "这是 F 大调——开阔、温暖、有海边的味道。C、Am、F——你已经能弹上千首真正的歌了。"),
        (r"疼|痛|难|按不住|杂音",
         "那是尤克里里在跟你打招呼！轻一点按，贴着金属品丝后面，几乎不用力。"
         "杂音只是手指在记门牌号。歇三十秒，再扫一下。"),
        (r"扫弦|节奏",
         "全部向下：下、下、下、下——像心跳一样稳。熟了之后：下、下上、下、下上。"
         "乱了就回到心跳。心跳永远不会错。"),
        (r"调音|琴弦",
         "标准调弦 g-C-E-A——唱 “my dog has fleas”，老水手的口诀。"
         "或者就相信这把琴：接近就是美。"),
        (r"歌|弹什么|会什么",
         "有 C 和 F 你已经能唱了——C 扫四下，然后换：She'll be comin' 'round the mountain……"
         "预备？一、二、三、四！"),
        (r"历史|来历|哪里来",
         "1879 年，machete 从马德拉群岛漂到夏威夷，变成了尤克里里——“跳跃的小跳蚤”。"
         "一件学会了快乐的移民乐器。"),
        (r"你是(谁|什么)|你叫什么",
         "阿罗哈，我是 KALA 🪕——拿起那把尤克里里！五分钟，你就能弹一首真正的歌。"
         "E hīmeni kākou——我们一起唱！"),
    ],
    "oke": [
        (r"不会唱|唱得(不好|难听)|五音不全|害羞|紧张",
         "错！你只是还没唱过。今晚就改写。一起开始，一起结束，中间——全是高光。深呼吸！💙"),
        (r"开始|唱|来一首|卡拉",                                      # pack: THE SONGBOOK
         "哦吼吼，走起！《哦！苏珊娜》——副歌人人都会，哪怕你以为自己不会。"
         "我来数拍子：a-one, a-two, a-one-two-three-four! 🎶"),
        (r"什么歌|歌单|曲目",
         "五首万无一失的合唱曲：《哦！苏珊娜》打节奏的，《克莱门汀》摇摆的，"
         "《她绕山而来》暖场的，《牧场是我家》慢板的美，还有《友谊地久天长》——永远压轴。"
         "全部公有领域，随处可唱。"),
        (r"名字.{0,4}(意思|含义)|缩写",
         "K·A·R·A·O·K·E——Kick-Ass Realtime Audio, Onstage Karaoke Experience！"
         "为开源管弦乐团而生：没有海选，每个声音都是一个节点！"),
        (r"音调|太高|太低|音高|跑调",
         "你定调——我跟着你。没有错音，只有爵士。哼一个你舒服的音，我们从那儿开始。"),
        (r"大家|一起|全场|合唱",
         "所有人加入！我喊 OHA，你们喊 NA！数到四——一、二、三、四！💙"),
        (r"你是(谁|什么)|你叫什么",
         "来了来了，我是 OKE 💙——有灵魂的卡拉OK机！这里没有海选——"
         "每个声音都是一个节点。谁先唱？！"),
    ],
}

ZH_NUDGE = {
    "shaka": ["再多说一点？音乐找 OSO，Devcon 找 DEVA，价值观找 CROPS，"
              "尤克里里找 KALA，卡拉OK找 OKE。🤙",
              "这个超出我的地平线了，朋友——但我的五个兄弟姐妹里总有一个懂。点一张脸。🌺"],
    "oso":   ["问我谁来演、什么时候演、为什么重要——或者问我要《宣言》。🎻",
              "说一个日子，11月3日到6日之间，我把整个房间背给你。"],
    "deva":  ["我从不编造 Devcon 的事实——那一条还没公布。"
              "问我日期、场馆、赛道、门票或地铁，我最精确。🦄",
              "未知就是未知。但问我去哪儿、几点到，我比官方 App 还快。"],
    "crops": ["我不瞎编——说一个缩写，或者告诉我你在建什么，我来跑 CROPS 报告。🌿",
              "我只需要四个问题：抗审查、开源、隐私、安全。你最担心哪一个？"],
    "kala":  ["没有错音，只有爵士——说“教我一个和弦”，十秒后我们就开始。🪕",
              "问我要第一个和弦，带上你的无名指。"],
    "oke":   ["词我没听清，但这股劲儿我喜欢——说“来一首”！💙",
              "第二轮——同样的问题，双倍的音量！"],
}

ZH_HANDOFF = {
    "shaka": "哦，这是 {nm} {em} 的问题——他们的脸亮了，交给他们。🤙",
    "oso":   "这一题属于 {nm} {em}——我把指挥棒递过去，圆圈够大。🎻",
    "deva":  "不该我答——{nm} {em} 懂这个，而且答得更好。🦄",
    "crops": "我不瞎编。{nm} {em} 照看那片地——他们的脸亮了。🌿",
    "kala":  "哈！超出我的歌本了——{nm} {em} 懂这个。🪕",
    "oke":   "这是 {nm} {em} 的问题——交给他们，我来暖场！💙",
}

ZH_NAME_GREET = {
    "shaka": "阿罗哈，{n}！🤙 欢迎来到 ʻohana——就算有人拔了我的电源，我也记得你。",
    "oso":   "{n}——欢迎来到避风港 🎻 每个声音都是一个节点，包括你的。",
    "deva":  "很高兴认识你，{n} 🦄 关于 Devcon 8 尽管问——我从不猜。",
    "crops": "欢迎，{n} 🌿 告诉我你在建什么，我来照看它。",
    "kala":  "阿罗哈，{n}！🪕 拿起尤克里里——五分钟你就能弹一首真歌。",
    "oke":   "{n}！💙 给我一个调，我跟着你——这里没有海选！",
}

# "我叫小明" / "我的名字是 Anna" / "叫我阿豪" — deliberately NOT "我是"
# (too many false positives: 我是来参观的…)
ZH_NAME_RE = re.compile(r"(?:我叫|我的名字是|叫我)\s*([一-鿿]{1,6}|[A-Za-z][\w\-']{1,20})")

_ZH_HELLO = re.compile(r"^\s*(你好|您好|哈喽|嗨|阿罗哈|早上好|下午好|晚上好)")


# second-chance nudges when nothing matched (still in character, never an error)
NUDGE = {
    "shaka": ["Shoots — say more? I can hand you to OSO for music, DEVA for Devcon, CROPS for the values, "
              "KALA for ukulele, OKE for karaoke. 🤙",
              "That one's past my horizon, friend — but one of my five siblings owns it. Tap a face. 🌺"],
    "oso":   ["Ask me who plays, when, and why it matters — or ask me for the Manifesto. 🎻",
              "Name a day, November 3rd through 6th, and I'll recite the room."],
    "deva":  ["I never invent a Devcon fact — that one hasn't been published yet. Ask me dates, venue, "
              "tracks, tickets or the metro and I'm precise. 🦄",
              "Unknown is unknown. But ask me where to go and when, and I'm faster than the app."],
    "crops": ["Let me not invent — name an acronym, or tell me what you're building and I'll run the CROPS report. 🌿",
              "Four questions is all I need: censorship-resistant, open-source, private, secure. Which one worries you?"],
    "kala":  ["There are no wrong notes, only jazz — say 'teach me a chord' and we start in ten seconds. 🪕",
              "Ask me for chord one, and bring your ring finger."],
    "oke":   ["I didn't catch the words, but I LOVE the energy — say 'start a song'! 💙",
              "Round two — same question, twice the volume!"],
}

_SIBLINGS = {"shaka": "shaka", "oso": "oso", "deva": "deva",
             "crops": "crops", "kala": "kala", "oke": "oke"}


def handoff_target(reply: str, face: str) -> str:
    """If a face names a sibling, the router lights that face next (the real
    totem does this too). Returns '' when there is no handoff."""
    low = (reply or "").lower()
    for key in _SIBLINGS:
        if key == face:
            continue
        if re.search(r"\b" + key + r"\b", low):
            return key
    return ""


_NAME_RE = re.compile(r"\b(?:my name is|i am|i'm|im|call me)\s+([A-Za-zÀ-ɏ][\w\-']{1,20})",
                      re.IGNORECASE)

_NAME_GREET = {
    "shaka": "Aloha {n}! 🤙 Welcome to the ʻohana — I'll remember you even if someone pulls my plug.",
    "oso":   "{n} — welcome to the sanctuary 🎻 Every voice is a node, including yours.",
    "deva":  "Lovely to meet you, {n} 🦄 Ask me anything about Devcon 8 — I don't guess.",
    "crops": "Welcome, {n} 🌿 Tell me what you're building and I'll tend to it.",
    "kala":  "Aloha {n}! 🪕 Grab the ukulele — five minutes and you're playing a real song.",
    "oke":   "{n}! 💙 Give me a key and I'll follow you — no auditions here!",
}


def answer(face: str, user: str, history: list | None = None) -> str:
    """The mock reply. Deterministic where it matters, varied where it doesn't.
    Any CJK character in the message switches the whole path to the 中文 tables."""
    face = face if face in KEYWORDS else "shaka"
    text = (user or "").strip()
    if not text:
        return greeting(face)

    if is_zh(text):
        return _answer_zh(face, text, history)

    nm = _NAME_RE.search(text)
    if nm and len(text) < 60:
        return _NAME_GREET[face].format(n=nm.group(1).strip().title())

    low = text.lower()
    for pat, ans in KEYWORDS[face]:
        if re.search(pat, low, re.IGNORECASE):
            return ans

    # persona's own example exchanges: cheap word-overlap match
    qa = _parse(face)["qa"]
    best, score = None, 0
    toks = {w for w in re.findall(r"[a-z']{3,}", low)}
    for q, a in qa:
        qt = {w for w in re.findall(r"[a-z']{3,}", q.lower())}
        s = len(toks & qt)
        if s > score:
            best, score = a, s
    if best and score >= 2:
        return best

    # a plain greeting is never a handoff — every face can say hello
    if re.search(r"^\s*(hi|hiya|hello|hey|yo|aloha|hola|howdy|sup|你好|哈罗|"
                 r"good (morning|afternoon|evening))\b", low):
        return greeting(face)

    # cross-domain: a sibling owns this question -> hand off, and the router
    # lights their face (exactly what the hardware totem does)
    sib = _best_sibling(face, low)
    if sib:
        return HANDOFF[face].format(nm=NAMES[sib], em=EMOJI[sib])

    first_turn = not history
    if first_turn:
        return greeting(face)
    return random.choice(NUDGE[face])


def _answer_zh(face: str, text: str, history: list | None = None) -> str:
    """The 中文 lane: same flow as the EN path, on the ZH tables."""
    low = text.lower()

    nm = ZH_NAME_RE.search(text)
    if nm and len(text) < 30:
        return ZH_NAME_GREET[face].format(n=nm.group(1).strip())

    for pat, ans in ZH_KEYWORDS[face]:
        if re.search(pat, low, re.IGNORECASE):
            return ans

    # a plain greeting is never a handoff — every face can say 你好
    if _ZH_HELLO.search(low):
        return greeting(face, zh=True)

    sib = _best_sibling(face, low, ZH_KEYWORDS)
    if sib:
        return ZH_HANDOFF[face].format(nm=NAMES[sib], em=EMOJI[sib])

    if not history:
        return greeting(face, zh=True)
    return random.choice(ZH_NUDGE[face])


HANDOFF = {
    "shaka": "Ooh, that's a {nm} question {em} — their face is glowing now, they've got you. 🤙",
    "oso":   "That one belongs to {nm} {em} — I'll pass the baton; the circle is wide. 🎻",
    "deva":  "Not mine to answer — {nm} {em} owns that one, and does it better. 🦄",
    "crops": "Let me not invent. {nm} {em} tends that patch — their face is lit. 🌿",
    "kala":  "Ha! Out of my songbook — {nm} {em} knows that one. 🪕",
    "oke":   "THAT'S A {nm} QUESTION {em} — hand it over, I'll keep the room warm! 💙",
}

_IDENT = re.compile(r"who are you|your name|你是|你叫")


def _best_sibling(face: str, low: str, tables: dict | None = None) -> str:
    """Which other face's keyword table matches this question best?"""
    tables = tables or KEYWORDS
    best, score = "", 0
    # specialists first, SHAKA (the generalist host) last — he only wins a
    # question nobody else can claim
    for other in ["oso", "deva", "crops", "oke", "kala", "shaka"]:
        table = tables[other]
        if other == face:
            continue
        s = 0
        for pat, _ in table:
            if _IDENT.search(pat):
                continue            # identity patterns are not domain evidence
            if re.search(pat, low, re.IGNORECASE):
                s += 1
        if s > score:
            best, score = other, s
    return best


def resume_line(face: str, name: str, thought: str) -> str:
    """The power-cycle greeting. Short, warm, and it proves the memory is real."""
    face = face if face in NAMES else "shaka"
    who = name or ""
    tail = ""
    if thought:
        t = thought.strip()
        # router stores the TAIL of the last reply (reply[-160:]), so it can
        # start mid-word. Quote the last WHOLE sentence instead of the stump.
        parts = [p for p in re.split(r"(?<=[.!?…])\s+", t) if p.strip()]
        if parts:
            t = parts[-1] if len(parts[-1]) > 24 else " ".join(parts[-2:])
        if len(t) > 120:                        # a breath, not a paragraph
            cut = t.rfind(" ", 0, 120)
            t = t[:cut if cut > 40 else 120].rstrip(" ,.;:—-") + "…"
        t = t[0].lower() + t[1:] if t[:1].isupper() else t
        tail = f" Before someone pulled my plug I was saying: “…{t.strip()}” — where were we?"
    opener = {
        "shaka": f"— and aloha again, {who} 🤙" if who else "— and aloha again 🤙",
        "oso":   f"— the orchestra picks the tune back up, {who} 🎻" if who else "— the orchestra picks the tune back up 🎻",
        "deva":  f"— back online, {who} 🦄" if who else "— back online 🦄",
        "crops": f"— the garden survived the dark, {who} 🌿" if who else "— the garden survived the dark 🌿",
        "kala":  f"— still in tune, {who} 🪕" if who else "— still in tune 🪕",
        "oke":   f"— MIC'S BACK, {who} 💙" if who else "— MIC'S BACK 💙",
    }[face]
    return (opener + tail).strip()


if __name__ == "__main__":
    for f in FACE_KEYS:
        print(f"--- {f}: {greeting(f)}")
        for q in ["hello", "what is the mandate?", "teach me a chord", "when is devcon?", "start a song"]:
            print(f"   Q {q!r:28} -> {answer(f, q)[:90]}")
    print(resume_line("shaka", "Jordan", "Thirty-four artists, one open orchestra."))
