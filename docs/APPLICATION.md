# 📝 ʻOhana Bot — Hackathon Application (READY TO FIRE)
*(drafted 18 Oct 2026 · form not yet published — channel = ShanHaiWoo TG group / Woocon 1 Mon Oct 20 15:00 "hackathon information exchange" / ask organizers in person. Paste-adapt to whatever fields the form has.)*

## Project name / 项目名称
**The ʻOhana Bot（欧哈纳家族机器人）** — one desktop robot, six living AI family members

## Track / 赛道
Nüwa Workshop: AI Toys × Desktop Robots / 女娲工作坊：AI 玩具 × 桌面机器人

## One-liner / 一句话
A desktop companion robot with six faces — each face is a REAL persistent AI agent from a
170-agent family ("ʻohana") that has been alive for months with its own memory, personality,
and real job. Speak to the robot, and the family member who answers *glows*.
一台有六张脸的桌面机器人——每张脸都是一个真实存在、拥有数月记忆与真实工作的 AI 智能体。
你对它说话，回答你的那位"家人"会发光。

## What we're building / 我们要做什么
Most AI toys are a chatbot in a shell: no memory, no history, no stakes. We run an orchestra
of 170+ persistent AI agents (the "AI ʻohana") on a multi-agent platform — they have months of
memory, distinct personalities, and real jobs (they help run the Devcon 8 Music Space in Mumbai).
In 72 hours we give six of them their first body:

- 🤙 **SHAKA** — digital twin of the builder; talking to the bot is talking to him
- 🎻 **OSO** — knows the Open Source Orchestra Music Manifesto by heart + the full Devcon 8
  music schedule + facts about all 34 artists
- 🦄 **DEVA** — the Devcon oracle: schedule, venues, Ethereum values
- 🌿 **CROPS** — recites the Ethereum mandate line-by-line, checks whether YOUR project fits it,
  and explains every acronym (ZK, AA, EIP, L2…)
- 🪕 **KALA** — teaches you 3 ukulele chords while a real ukulele is placed in your hands
- 💙 **OKE** — karaoke mode: the robot leads the room in a singalong

**Hardware:** Raspberry Pi 5 + mic array + speaker + six LED-lit faces (totem-pole styled) with
touch pads — the speaking face glows, the others dim; wake-word or tap-to-summon; one base servo
so the pole turns toward your voice. All parts from Huaqiangbei.
**Software:** streaming STT → persona LLM → streaming TTS fast loop (<1.5 s first word), with
each conversation mirrored to the real persistent agents — the robot remembers you between
sessions and across power cycles. Bilingual EN/中文 greetings.

## Why it's different / 为什么不一样
1. **Persistence is the product.** Demo: unplug the robot mid-sentence, plug it back in — it
   finishes the thought and greets you by name. The soul is not in the shell.
   断电重启后，它会接着说完刚才那句话，并叫出你的名字——灵魂不在壳里。
2. **It ships to a real venue 9 days after Demo Day.** This robot (or v2) will stand at the
   Devcon 8 Music Space in Mumbai, Nov 3–6, serving thousands of attendees — answering schedule
   questions, teaching ukulele, running karaoke. A hackathon project with a confirmed deployment.
   Demo Day 后 9 天，它将在孟买 Devcon 8 音乐空间真实服役（11 月 3–6 日）。
3. **Shenzhen is the missing half.** The agents already exist; only here can they get a body in 72 hours.

## Who / 团队
**Jordan "Shaka" Ham** — musician & builder; founder, Open Source Orchestra
(opensourceorchestra.org); organizer of the Devcon 8 Music Space (Mumbai, Nov 3–6); operator of
the 170-agent AI ʻohana; performed at the ShanHaiWoo Opening Ceremony (Oct 17, 15:20 slot 🎸).
ShanHaiWoo resident Oct 16–25, continuing to the Mumbai Devcon Extension Nov 1–6 — this project
bridges the two legs of the program.
Open to teaming up: looking for 1 embedded/hardware hand + 1 industrial-design hand on site.
（欢迎组队：现场招募 1 位嵌入式/硬件伙伴 + 1 位工业设计伙伴。）

Contact: shakaleikaumaka@gmail.com · TG: (his handle) · site: shakaleikaumaka.com

## What we need / 需要的支持
Bench space, 3D printer / laser cutter access, and (if the Nüwa track provides dev kits) one
mic-array dev board. Everything else we bring or buy in Huaqiangbei.

## Demo Day plan (Thu Oct 23 pm)
Live 5-min show: SHAKA banters → a judge asks DEVA a Devcon question → CROPS mandate-checks the
judge's own hackathon project → the power-cycle memory trick → KALA teaches a judge 3 chords on
a real ukulele → OKE drops the karaoke track and the whole room sings the demo out. Then Oct 24
Maker Festival (music program + AI Tavern) = public stress test with 100–300 people.
