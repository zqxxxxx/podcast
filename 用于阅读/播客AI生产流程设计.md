# 中文播客 AI 生产流程设计

## 当前状态

本文档是当前执行基线，覆盖旧的 OpenAI 转写和 GPT 文本主链路方案。

默认生产路径是：

```text
飞书转写稿 + 原始音频
  -> 导入并校验转写
  -> MiniMax 做内容分析和剪辑决策
  -> ffmpeg 组装音频
  -> 用户试听 demo 并反馈
  -> 生成完整粗剪和发布素材
```

OpenAI API 默认关闭。它以后可以作为手动开启的可选复核，但不能成为正常执行的必需条件。

## 目标

搭建一套可重复使用的 AI 辅助播客生产流程，把一段中文长访谈变成：

- 可反复校准的 demo；
- demo 通过后的剪辑风格指南；
- 第一期自然完整的 45-60 分钟粗剪；
- 后期交接文件；
- shownotes 等发布素材。

该流程要控制成本，并绕开 OpenAI API quota/billing 造成的中断。

## 输入

必需输入：

- `inputs/audio/radio.m4a`：原始音频。所有剪辑时间戳都基于这条音频。
- `inputs/transcript/feishu.srt` 或 `inputs/transcript/feishu.vtt`：飞书导出的带时间戳转写稿。
- `inputs/outline.md`：采访大纲和剪辑简报。
- `MINIMAX_API_KEY`：MiniMax 文本模型环境变量。

可选输入：

- 说话人映射，例如 `Riko = 说话人 1`、`嘉宾 = 说话人 2`。
- 需要纠错的人名、地名、英文词、专有名词。
- 制作人手动标注的必保留/必删除段落。

## 输出

- `outputs/transcript/transcript.json`：标准化转写稿，供所有下游步骤使用。
- `outputs/content_map/content_map.json`：主题、亮点、可删除段落和大纲关系。
- `outputs/demos/demo_vN_edit_decision_list.json`：demo 剪辑清单。
- `outputs/demos/demo_vN.wav`：demo 音频。
- `outputs/demos/demo_vN_feedback.json`：用户反馈结构化结果。
- `outputs/style/edit_style_guide.md`：确认后的剪辑风格指南。
- `outputs/style/selection_rules.json`：机器可读选段规则。
- `outputs/style/cutting_rules.json`：机器可读剪辑规则。
- `outputs/edit_decision_list.json`：完整正片剪辑清单。
- `outputs/rough_cut.wav`：完整粗剪。
- `outputs/postproduction/postproduction_handoff.md`：Cleanvoice/Auphonic 后期交接。
- `outputs/shownotes.md`：发布文案。

## 架构

### 飞书转写导入

导入步骤把飞书 SRT/VTT/TXT 转成统一 schema：

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 12.5,
      "text": "标准化后的转写文本",
      "speaker": "Riko",
      "chunk_id": "feishu"
    }
  ]
}
```

必须校验：

- 时间戳非负且递增；
- 每段 `end` 大于 `start`；
- 空文本段落被过滤；
- 转写覆盖时长应接近原始音频时长；
- 如果说话人标签不清楚，先停止并确认说话人映射。

### LLM Provider

MiniMax 是默认 LLM provider，通过配置选择：

```yaml
providers:
  llm:
    provider: minimax
    api_key_env: MINIMAX_API_KEY
    base_url: https://api.minimax.io/v1
    model: MiniMax-M2.7
```

Provider 接口必须返回严格 JSON，供现有内容图谱、demo EDL、最终 EDL、shownotes 模块使用。

除非配置显式启用 OpenAI 可选复核，任何默认命令都不能初始化 OpenAI client。

### 剪辑流程

1. 根据标准化转写稿和大纲生成内容图谱。
2. 生成一组 demo 候选 EDL。
3. 校验并选择最稳的 demo EDL。
4. 用 ffmpeg 组装 demo。
5. 用户试听并反馈，必要时迭代 v2/v3。
6. 用户确认 demo 后冻结风格。
7. 使用冻结风格生成最终 EDL。
8. 校验并组装完整粗剪。
9. 生成后期交接和发布素材。

### 质量闸门

系统不能只相信单次模型输出，必须使用质量闸门：

- 转写闸门：飞书导入合法，且时长与原始音频基本一致。
- 内容闸门：覆盖大纲中的关键叙事部分，标出亮点和可删段落。
- Demo 闸门：6-10 分钟，突出嘉宾，包含故事、观点、自然转场，不只取开头。
- 最终 EDL 闸门：45-60 分钟，时间戳排序，单段不碎，语义完整优先。
- 人类闸门：用户没有明确确认 demo 前，不能冻结风格。

## OpenAI 使用政策

OpenAI 不属于默认路径。

允许：

- 手动开启的可选复核；
- 一次性对照实验；
- 迁移完成前保留旧命令兼容。

默认禁止：

- 要求 `OPENAI_API_KEY`；
- 用 OpenAI 做转写；
- 未经用户明确同意，用 GPT 文本模型做内容图谱、demo EDL、最终 EDL 或 shownotes。

## 后期

第一版仍然使用手动 Cleanvoice/Auphonic 交接。后期服务 API 自动化可以以后再加，不影响第一期执行。
