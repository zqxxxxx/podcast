# 播客单集执行计划

> 本计划只用于“单集内容已经准备好之后怎么执行”。MiniMax provider、默认路径、OpenAI 默认关闭等一次性工程配置已经固化在代码里，不需要每期重新配置。

## 目标

把准备好的单集素材变成可试听 demo、确认后的剪辑风格、完整粗剪、后期交接文件和发布素材。

## 必需输入

运行前放好这些文件：

- `inputs/audio/radio.m4a`
- `inputs/transcript/feishu.srt` 或 `inputs/transcript/feishu.vtt`
- `inputs/outline.md`

飞书转写稿必须带时间戳，优先使用 SRT。

## 执行步骤

- [ ] 确认音频在 `inputs/audio/radio.m4a`。

- [ ] 确认飞书转写稿在 `inputs/transcript/feishu.srt`。如果不是这个路径，只在必要时改配置。

- [ ] 确认 `inputs/outline.md` 包含本期采访大纲和剪辑简报。

- [ ] 运行环境检查：

```powershell
podcast-pipeline doctor
```

- [ ] 导入飞书转写稿：

```powershell
podcast-pipeline import-transcript --config config.yaml
```

期望输出：

```text
outputs/transcript/transcript.json segments=<段落数> first_start=<秒> last_end=<秒>
```

如果导入结果是 0 段、缺时间戳、时间戳乱序，或总时长明显对不上原始音频，先停止。

- [ ] 生成内容图谱：

```powershell
podcast-pipeline content-map --config config.yaml
```

期望输出：

```text
outputs/content_map/content_map.json
```

- [ ] 生成第一版 demo 剪辑清单：

```powershell
podcast-pipeline demo-edl --config config.yaml --version v1
```

期望输出：

```text
outputs/demos/demo_v1_edit_decision_list.json
```

- [ ] 组装第一版 demo：

```powershell
podcast-pipeline assemble-demo --config config.yaml --version v1
```

期望输出：

```text
outputs/demos/demo_v1.wav
```

- [ ] 听 `outputs/demos/demo_v1.wav`。

用中文反馈节奏、信息密度、主持人/嘉宾比例、故事性和自然程度。

- [ ] 录入 demo 反馈：

```powershell
podcast-pipeline demo-feedback --config config.yaml --version v1 --feedback "你的反馈"
```

- [ ] 根据需要生成 `v2`、`v3`，直到某一版 demo 被确认。

- [ ] 冻结确认后的剪辑风格：

```powershell
podcast-pipeline freeze-style --config config.yaml --approved-version vN
```

期望输出：

```text
outputs/style/edit_style_guide.md
outputs/style/selection_rules.json
outputs/style/cutting_rules.json
```

- [ ] 生成完整正片剪辑清单：

```powershell
podcast-pipeline final-edl --config config.yaml
```

期望输出：

```text
outputs/edit_decision_list.json
```

- [ ] 组装完整粗剪：

```powershell
podcast-pipeline assemble-final --config config.yaml
```

期望输出：

```text
outputs/rough_cut.wav
```

- [ ] 生成后期交接文件：

```powershell
podcast-pipeline postproduction-handoff --config config.yaml
```

期望输出：

```text
outputs/postproduction/postproduction_handoff.md
```

- [ ] 生成发布素材：

```powershell
podcast-pipeline publishing-assets --config config.yaml
```

期望输出：

```text
outputs/shownotes.md
```

## 完成检查

- `outputs/transcript/transcript.json` 存在。
- `outputs/content_map/content_map.json` 存在。
- 已确认的 `outputs/demos/demo_vN.wav` 存在。
- `outputs/style/edit_style_guide.md` 存在。
- `outputs/edit_decision_list.json` 存在。
- `outputs/rough_cut.wav` 存在。
- `outputs/postproduction/postproduction_handoff.md` 存在。
- `outputs/shownotes.md` 存在。
