# 中文播客 AI 生产流程设计

## 目标

搭建一套可重复使用的 AI 辅助播客生产流程，把一段约 3 小时的中文采访原始音频和一份采访大纲，剪辑成 50-55 分钟的可发布音频节目。

用户不需要手动剪时间线。系统负责生成内容决策、短 demo、完整粗剪、后期精修交接文件和发布素材。

## 输入

- 一段长音频原始文件，通常约 3 小时。
- 一份采访大纲，Markdown 或纯文本均可。
- 可选节目信息：节目标题、嘉宾名、主持人名、目标听众、发布平台说明、期望语气。

## 输出

- `outputs/demos/demo_vN.wav`：用于反馈的短 demo。
- `outputs/demos/demo_vN_edit_decision_list.json`：每一版 demo 的时间码剪辑决策。
- `outputs/style/edit_style_guide.md`：demo 确认后的剪辑风格指南。
- `outputs/style/selection_rules.json`：机器可读的内容选择规则。
- `outputs/style/cutting_rules.json`：机器可读的节奏和转场规则。
- `outputs/edit_decision_list.json`：最终 50-55 分钟正片的剪辑清单。
- `outputs/rough_cut.wav`：外部声音清理前的完整 AI 粗剪。
- `outputs/final_episode.mp3`：声音清理和母带处理后的最终可发布音频。
- `outputs/final_transcript.md`：最终正片逐字稿。
- `outputs/shownotes.md`：标题候选、节目简介、章节和发布说明。

## 核心流程

### 1. 导入

创建项目目录，检查原始音频和采访大纲是否存在。把稳定路径和节目设置写入项目配置文件。

配置包含：

- 最终目标时长：50-55 分钟
- demo 目标时长：6-10 分钟
- 语言：中文
- 剪辑模式：保守的语义剪辑
- 精修模式：只在粗剪完成后进行
- 导出格式：粗剪用 WAV，最终成片用 MP3

### 2. 转录

把长音频切成适合 API 处理的小段，分别转录成中文，再把所有转录片段合并回原始音频时间线。

转录格式需要保留：

- 绝对开始和结束时间
- 文本
- 可选说话人标签
- 来源音频分块编号
- 可用时记录置信度或质量说明

在粗剪音频生成之前，所有时间码都必须指向原始音频。

### 3. 内容地图

结合采访大纲和全文转录稿，生成 3 小时录音的内容地图。

每个内容块包含：

- 原始时间范围
- 主题标签
- 与采访大纲的关系
- 摘要
- 亮点分
- 删除分
- 关于故事性、情绪、洞察、冲突、重复或跑题的说明

这一步不剪音频，只创建 AI 剪辑决策所需的内容表面。

### 4. Demo 候选选择

在剪完整正片前，先从全片里选出一组混合 demo 候选片段。

demo 不应只是截节目开头，而应覆盖几种代表性内容：

- 一个故事段
- 一个观点或洞察段
- 一个主持人追问或挑战段
- 一个自然转场或聊天段
- 一个用于测试节奏和停顿处理的片段

第一轮候选池可以是 12-18 分钟，最终导出的 demo 为 6-10 分钟。

### 5. Demo 校准循环

生成 `demo_v1.wav` 和对应的 `demo_v1_edit_decision_list.json`。

用户只听 demo，然后给反馈，例如：

- 太慢或太快
- 太碎
- 故事不够
- 主持人太多或太少
- 太像观点合集
- 保留了太多口头禅
- 删掉了太多自然停顿
- 转场突兀
- 内容有用但情绪不够

每一轮反馈都会生成：

- 新 demo 版本
- 新 demo 剪辑清单
- 简短反馈总结
- 更新后的剪辑规则草稿

循环持续到用户确认 demo 可接受为止。

### 6. 风格冻结

demo 被确认后，把已接受的 demo 和用户反馈转化为稳定规则。

`edit_style_guide.md` 应描述：

- 目标节目感觉
- 理想节奏
- 故事和观点的比例
- 主持人和嘉宾的比例
- 自然停顿保留程度
- 如何处理中文口头禅，例如“嗯”“啊”“就是”“然后”“那个”
- 是否保留笑声、犹豫和情绪停顿
- 什么算跑题
- 什么内容值得保留
- 什么内容可以安全删除

`selection_rules.json` 编码内容偏好。`cutting_rules.json` 编码节奏、边界、转场和最短片段长度规则。

### 7. 正片剪辑决策

使用以下材料生成完整 50-55 分钟正片剪辑清单：

- 转录稿
- 内容地图
- 采访大纲
- 已确认 demo 的剪辑清单
- 冻结后的风格指南
- 内容选择规则和剪辑规则

完整剪辑清单应优先保留完整语义段，避免过多碎切。它要在删除重复、长铺垫、支线和弱解释的同时，保留足够自然的聊天感。

系统应先生成一个略长的内部候选版本，约 60-70 分钟，再压缩到目标 50-55 分钟。

### 8. 粗剪组装

根据最终剪辑清单，从原始音频自动组装 `rough_cut.wav`。

这一步需要：

- 按顺序保留选中片段
- 只在需要时加入短交叉淡化
- 不改变语速
- 在粗剪导出前不做会改变时长的声音清理
- 校验最终时长
- 生成剪辑报告

### 9. 音频清理

只在 `rough_cut.wav` 生成后进行声音清理。这样可以避免转录时间码漂移。

推荐的中文播客清理顺序：

1. Cleanvoice 轻度清理
   - 口水音
   - 过重呼吸
   - 明显卡顿
   - 长停顿，保守处理
   - 默认避免激进删除口头禅

2. Auphonic 最终母带
   - 响度标准化
   - 说话人音量拉平
   - 轻度降噪
   - 最终 MP3 导出

Adobe Podcast Enhance Speech 作为备选，不作为默认方案。只有当录音有明显房间混响或噪声，并且处理后仍能保留自然中文语气时才使用。

### 10. 发布素材

根据最终剪辑清单和转录稿生成发布材料：

- 最终逐字稿
- shownotes
- 标题候选
- 节目摘要
- 章节时间轴，基于最终成片时间，不是原始音频时间
- 可选短视频片段建议

## Skills

实施和运行时使用这些 Codex skills：

- `skill-installer`：按需安装 curated skills，例如 `transcribe`。
- `transcribe`：安装后辅助音频转录流程。
- `openai-docs`：检查当前 OpenAI 转录和模型文档。
- `writing-plans`：把这份设计转换成逐步实施计划。
- `verification-before-completion`：在声明流程可用前，用真实或样例文件验证。
- `systematic-debugging`：排查转录、剪辑清单、ffmpeg 或导出失败。
- 可选未来自定义 skill：`podcast-editor`，等流程稳定后，把这套方法固化成后续节目可直接复用的 skill。

## 工具

### 必需本地工具

- Python：流程编排、API 调用、JSON 处理、Markdown 生成。
- ffmpeg：音频切片、拼接、WAV/MP3 导出、时长检查。

### 外部服务

- OpenAI transcription：中文转录和时间码。
- OpenAI text model：内容地图、demo 选择、剪辑清单、风格指南、shownotes。
- Cleanvoice：粗剪后的语音清理。
- Auphonic：最终响度标准化和母带。

### 可选服务

- Adobe Podcast Enhance Speech：用于噪声或混响特别重的录音。
- CapCut/剪映：可选的人工视觉检查或视频发布流程。

## Agent 角色

这些是实施和未来自动化时的概念角色。除非用户明确批准并行 agent 工作，否则不需要真的启动子 agent。

- Pipeline Architect：项目结构、配置和命令入口。
- Transcription Agent：音频分块、转录、转录合并、时间码校验。
- Content Editor Agent：内容地图、大纲对齐、亮点评分。
- Demo Editor Agent：demo 候选选择、demo 剪辑清单、反馈吸收。
- Style Guide Agent：把已确认 demo 的反馈转成稳定剪辑规则。
- Assembly Agent：ffmpeg 剪辑组装、时长校验、粗剪导出。
- Postproduction Agent：Cleanvoice/Auphonic 交接说明或 API 集成。
- QA Agent：检查文件、时长、JSON、缺失转录片段和最终交付物。

## 推荐项目结构

```text
podcast_pipeline/
  __init__.py
  cli.py
  config.py
  ingest.py
  audio.py
  transcribe.py
  content_map.py
  demo.py
  style.py
  edit_decision.py
  assemble.py
  publish_assets.py
  schemas.py
  prompts/
    content_map.md
    demo_selection.md
    demo_feedback.md
    style_freeze.md
    final_edit_decision.md
    shownotes.md
inputs/
  audio/
  outline.md
outputs/
  transcript/
  content_map/
  demos/
  style/
  postproduction/
tests/
  fixtures/
```

## 实施边界

第一版应先做成命令行可运行流程，不做网页界面。

第一版可以先用手动上传/下载方式处理 Cleanvoice 和 Auphonic，并生成明确的交接文件。等账号、凭证和服务限制明确后，再加入 API 自动化。

流程应可恢复。如果转录已经完成，后续命令应复用已有转录文件，除非用户要求重新生成。

每个主要阶段都应产出可检查的中间文件。

## 质量检查

完整正片导出前：

- 转录 JSON 合法
- 所有片段时间码单调递增
- demo 时长在 6-10 分钟内
- 最终剪辑清单时长在 50-55 分钟内
- 选中片段没有错误重叠
- 每个选中片段都有保留理由
- 生成最终剪辑清单前，风格指南已经存在

完成前：

- `rough_cut.wav` 存在
- `final_episode.mp3` 存在，或后期精修交接说明已生成
- 输出时长已报告
- 最终逐字稿和 shownotes 已存在
- 所有生成的 JSON 文件通过 schema 校验

## 实施阶段需要确认的问题

- 是否需要本地开源转录作为备用方案。
- Cleanvoice 和 Auphonic 第一版是 API 集成，还是先做明确的手动上传/下载流程。
- 是否必须做说话人分离来控制主持人/嘉宾比例，还是先从文本模式推断。
- 最终节目是否需要加入 intro/outro 音乐。

## 推荐第一版

第一版应搭建：

- 项目配置
- 音频时长检查
- 转录分块计划
- 转录 schema
- 内容地图生成
- demo 剪辑清单生成
- demo 自动组装
- 反馈吸收
- 风格指南生成
- 最终剪辑清单生成
- 粗剪自动组装
- 后期精修交接清单
- 发布素材生成

第一版暂缓：

- Cleanvoice API 自动化
- Auphonic API 自动化
- Adobe Podcast 自动化
- Web dashboard
- 自动混入 intro/outro 音乐

