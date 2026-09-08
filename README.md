# 两种方向可选的社媒封面 Skill

为小红书、抖音和视频发布页制作真人品牌封面。先从观众为什么想看出发，设计人物与主题物的互动，再用确定性方法排标题。

| 方向 | 适合的需求 | 具体规范 |
| --- | --- | --- |
| 同片视觉 | 希望封面沿用视频的色盘、材质与图形语言 | [同片封面](references/video-coherent-cover.md) |
| 美漫高冲击 | 希望强化近景透视、巨型主题道具与漫画文字张力 | [美漫与公共质量要求](references/approved-cover-system.md) |

两种方向在同一个 Skill 中，不需要另装一个“爆款封面 Skill”。吸引力需要实际看图判断，不承诺点击率或爆款。

## 怎么开始

下载或克隆完整仓库，保留 `SKILL.md`、`references`、`scripts` 和 `agents`，放入所用 AI 工具配置的 Skills 目录，文件夹名保持为 `produce-social-media-cover`。Codex 用户也可以让内置 `$skill-installer` 从本仓库安装。

先准备主题、观众、观看收益、人物身份参考和所需比例。有视频时一并提供认可的视频帧；真人封面使用你本人或已获授权的人物照片。

可以直接这样说：

> 使用 produce-social-media-cover，为【主题】做封面，面向【观众】，标题想表达【观看理由】。身份参考在【位置】。先做一张 3:4 的【同片视觉／美漫高冲击】封面，确认方向后，再独立设计 9:16 和 4:3。

也可以只要求一张或同主题两种方向比较。三比例必须分别构图，不能把竖版硬裁成横版。

## 需要什么、能得到什么

- 需要能读写文件、调用图片生成或处理能力、渲染文字布局的 AI 环境，以及可用且获授权的中文字体。
- 主视觉与标题分开制作：图像生成负责无字画面，HTML/CSS/SVG/Canvas 等负责准确排字。
- 标准输出是 1242×1660、1080×1920、1600×1200 三种比例；实际数量遵守你的请求。
- 检查人物身份、手与道具接触、文字避让、手机可读性和每个画幅的构图。尺寸脚本和排版检查不能代替实际看图。
- 图像生成或 AI 服务可能收费；不包含原作者的照片、生成封面、字体文件或服务账号。

## 配套与检查

完整视频使用 [主 MG Skill](https://github.com/xupengli406-del/produce-voiceover-mg-social-video)，画面节奏可配合 [节奏增强 Skill](https://github.com/xupengli406-del/enhance-voiceover-video-rhythm)。只做封面不需要运行视频渲染器。

入口与顺序见 [SKILL.md](SKILL.md)，文字排版要求见 [typography-and-layout.md](references/typography-and-layout.md)。检查脚本使用 Python：

```bash
python scripts/test_validate_typography.py
python scripts/validate_typography.py <排版清单.json> --image <封面.png>
python scripts/validate_cover_set.py <输出目录> --topic "主题"
```

## 开源与参与

原创说明与脚本使用 [MIT License](LICENSE)。输入素材、字体及外部服务仍按各自授权使用。

觉得有用可以 Star 收藏；问题和改进想法提 Issue；已改好的规范或脚本可提交 PR。描述实际场景和验证结果，使用合成示例或有权公开的素材，不提交私人照片与凭证。
