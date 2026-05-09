# 播客 AI 生产流程实施计划

> **给 agentic workers 的要求：** 执行这个计划时，需要使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，并按任务逐项推进。步骤使用 checkbox（`- [ ]`）格式跟踪。

**目标：** 搭建一套命令行 AI 播客生产流程，把 3 小时中文采访录音和采访大纲，转换成可反复校准的 demo、确认后的剪辑风格指南、50-55 分钟粗剪、后期交接文件和发布素材。

**架构：** 使用一个轻量 Python package，把配置、schema、音频工具、转录、LLM 内容决策、demo 校准、音频组装和发布素材拆成独立模块。第一版把 Cleanvoice/Auphonic 做成明确的手动交接步骤，同时让 AI 和 ffmpeg 阶段都能通过中间 JSON/Markdown 文件恢复和检查。

**技术栈：** Python 3.13、OpenAI Python SDK、ffmpeg/ffprobe、PyYAML、pytest、标准库 dataclasses/subprocess/json/pathlib。

---

## 实施说明

当前工作区不是 git 仓库。除非用户后续初始化 git，否则不要把 `git commit` 作为强制步骤，用测试和检查点替代。

英文项目文档放在 `docs/`。中文阅读版放在 `C:\work\Vibe2\用于阅读`。Codex 可以写入中文阅读版，但默认不读取该文件夹。

默认使用 `whisper-1` 做带时间码的转录，因为 OpenAI 音频转录 API 文档支持 `verbose_json` 和 segment/word timestamp。模型保持可配置。OpenAI API 调用集中放在一个 wrapper 文件里，方便以后 API 变化时只改一个地方。

第一版不自动集成 Cleanvoice/Auphonic API，只生成手动上传/下载的交接说明。

---

## 文件结构

创建以下结构：

```text
C:\work\Vibe2\
  pyproject.toml
  README.md
  config.example.yaml
  podcast_pipeline\
    __init__.py
    __main__.py
    cli.py
    config.py
    schemas.py
    audio.py
    llm.py
    transcribe.py
    content_map.py
    demo.py
    style.py
    edit_decision.py
    assemble.py
    publish_assets.py
    postproduction.py
    prompts\
      content_map.md
      demo_selection.md
      demo_feedback.md
      style_freeze.md
      final_edit_decision.md
      shownotes.md
  inputs\
    audio\
    outline.md
  outputs\
    transcript\
    content_map\
    demos\
    style\
    postproduction\
  tests\
    fixtures\
    test_config.py
    test_schemas.py
    test_audio.py
    test_transcribe.py
    test_content_map.py
    test_demo.py
    test_style.py
    test_edit_decision.py
    test_publish_assets.py
    test_cli.py
```

---

## 任务拆分

### Task 1：项目骨架和工具配置

创建 Python package、`pyproject.toml`、`README.md`、示例配置、输入输出目录和基础 CLI。先写 `--version` 和 `doctor` 两个最小命令，并用 `tests/test_cli.py` 验证。

验收命令：

```powershell
python -m pytest tests/test_cli.py -q
```

期望结果：`2 passed`。

### Task 2：配置和 schema

实现：

- `config.example.yaml`
- `podcast_pipeline/config.py`
- `podcast_pipeline/schemas.py`
- `tests/test_config.py`
- `tests/test_schemas.py`

配置需要包含输入音频、大纲、输出目录、OpenAI 环境变量、转录模型、文本模型、最终时长、demo 时长、候选池时长、最短片段、crossfade 和后期模式。

schema 至少包含：

- `TranscriptSegment`
- `ContentBlock`
- `EditSegment`
- `segment_duration`
- `total_edit_duration`
- `validate_edit_segments`

验收命令：

```powershell
python -m pytest tests/test_config.py tests/test_schemas.py -q
```

### Task 3：音频工具

实现：

- `podcast_pipeline/audio.py`
- `tests/test_audio.py`

能力：

- 秒数和 `HH:MM:SS.mmm` 互转
- 生成带重叠的 chunk plan
- 调用 `ffprobe` 读取时长
- 调用 `ffmpeg` 抽取片段
- 根据 EDL 组装音频

同时更新 `doctor`，检查 `ffmpeg` 和 `ffprobe` 是否在 PATH。

验收命令：

```powershell
python -m pytest tests/test_cli.py tests/test_audio.py -q
```

### Task 4：转录流程

实现：

- `podcast_pipeline/transcribe.py`
- CLI 命令：`transcribe`
- `tests/test_transcribe.py`

能力：

- 把长音频按 chunk plan 切分
- 对每个 chunk 调用 OpenAI 音频转录
- 使用 `verbose_json` 和 segment timestamps
- 把 chunk 内相对时间转成原始音频绝对时间
- 去掉 chunk overlap 导致的重复句
- 输出 `outputs/transcript/transcript.json`

验收命令：

```powershell
python -m pytest tests/test_transcribe.py -q
```

### Task 5：LLM wrapper 和 prompt 模板

实现：

- `podcast_pipeline/llm.py`
- `podcast_pipeline/prompts/content_map.md`
- `podcast_pipeline/prompts/demo_selection.md`
- `podcast_pipeline/prompts/demo_feedback.md`
- `podcast_pipeline/prompts/style_freeze.md`
- `podcast_pipeline/prompts/final_edit_decision.md`
- `podcast_pipeline/prompts/shownotes.md`

`llm.py` 只做一件事：给定 system prompt 和 user prompt，返回严格 JSON。后续所有内容决策模块都通过这个 wrapper 调 OpenAI。

### Task 6：内容地图生成

实现：

- `podcast_pipeline/content_map.py`
- CLI 命令：`content-map`
- `tests/test_content_map.py`

输入：

- `outputs/transcript/transcript.json`
- `inputs/outline.md`

输出：

- `outputs/content_map/content_map.json`

内容地图需要包含主题、与大纲关系、摘要、亮点分、删除分和编辑备注。

验收命令：

```powershell
python -m pytest tests/test_content_map.py -q
```

### Task 7：Demo 选择和组装

实现：

- `podcast_pipeline/demo.py`
- `podcast_pipeline/assemble.py`
- CLI 命令：`demo-edl`
- CLI 命令：`assemble-demo`
- `tests/test_demo.py`

能力：

- 从转录和内容地图生成 6-10 分钟 demo EDL
- demo 必须包含故事、观点、主持人追问、自然转场和节奏测试素材
- 校验 demo 时长
- 用 ffmpeg 导出 `outputs/demos/demo_vN.wav`
- 生成对应 report

验收命令：

```powershell
python -m pytest tests/test_demo.py -q
```

### Task 8：反馈吸收和风格冻结

实现：

- `podcast_pipeline/style.py`
- CLI 命令：`demo-feedback`
- CLI 命令：`freeze-style`
- `tests/test_style.py`

能力：

- 把用户对 demo 的中文反馈转换成稳定编辑规则
- 记录每一轮 demo feedback
- 在用户确认某版 demo 后生成：
  - `outputs/style/edit_style_guide.md`
  - `outputs/style/selection_rules.json`
  - `outputs/style/cutting_rules.json`

验收命令：

```powershell
python -m pytest tests/test_style.py -q
```

### Task 9：最终剪辑清单和粗剪

实现：

- `podcast_pipeline/edit_decision.py`
- CLI 命令：`final-edl`
- CLI 命令：`assemble-final`
- `tests/test_edit_decision.py`

输入：

- 转录稿
- 内容地图
- 已冻结风格指南
- 内容选择规则
- 剪辑规则

输出：

- `outputs/edit_decision_list.json`
- `outputs/rough_cut.wav`

最终 EDL 必须校验总时长在 50-55 分钟内，并且每个片段都有保留理由。

验收命令：

```powershell
python -m pytest tests/test_edit_decision.py -q
```

### Task 10：后期交接和发布素材

实现：

- `podcast_pipeline/postproduction.py`
- `podcast_pipeline/publish_assets.py`
- CLI 命令：`postproduction-handoff`
- CLI 命令：`publishing-assets`
- `tests/test_publish_assets.py`

后期交接文件要明确：

- Cleanvoice 轻度清理选项
- 中文口头禅不要默认激进删除
- Auphonic 的响度、音量统一、轻度降噪、MP3 导出
- Adobe Podcast 只作为 fallback

发布素材包括：

- `outputs/shownotes.md`
- `outputs/publishing_assets.json`

验收命令：

```powershell
python -m pytest tests/test_publish_assets.py -q
```

### Task 11：端到端命令顺序

实现 CLI 命令：

```powershell
podcast-pipeline next-steps --config config.yaml
```

它输出完整命令顺序：

1. `doctor`
2. `transcribe`
3. `content-map`
4. `demo-edl`
5. `assemble-demo`
6. 用户听 demo 并反馈
7. `demo-feedback`
8. 重复 demo loop
9. `freeze-style`
10. `final-edl`
11. `assemble-final`
12. `postproduction-handoff`
13. `publishing-assets`

同时补充英文 `README.md`。

验收命令：

```powershell
python -m pytest tests/test_cli.py -q
```

### Task 12：验证和第一期运行手册

创建：

- `docs/runbooks/first-episode-runbook.md`
- `C:\work\Vibe2\用于阅读\第一期播客运行手册.md`

运行最终验证：

```powershell
python -m pytest -q
python -m podcast_pipeline doctor
```

完成检查：

- 已确认 demo 存在
- 风格指南存在
- 最终 EDL 存在
- `rough_cut.wav` 存在
- 后期交接文档存在
- 手动后期完成后 `final_episode.mp3` 存在
- `shownotes.md` 存在

---

## 执行建议

这个工作区很小，也不是 git repo。最稳妥的执行方式是在当前会话里按任务顺序 inline execution。

只有当用户明确要求并行 agent 工作时，再拆成多个 agent：

- Agent A：配置、schema、CLI 骨架。
- Agent B：音频、assemble、ffmpeg 测试。
- Agent C：LLM 内容地图、demo、style、最终 EDL。
- Agent D：发布素材、后期交接、运行手册。

不要在用户未明确要求时启动子 agent。

