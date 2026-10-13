# video-crawl-qa-extract
按关键词搜索并下载目标视频；用本地 faster-whisper 把视频转成带时间戳的文字稿，再调用云端大模型（DeepSeek 等）提取提问与回答，最后汇总成高频问题清单。支持断点续跑、自动跳过已处理内容。

## ✨ 功能特性
- 关键词检索、批量下载目标视频
- 本地 faster-whisper 语音转文字，输出带时间戳字幕
- 调用DeepSeek等大模型，从字幕中抽取问答对
- 自动汇总高频问答清单
- 断点续跑，自动跳过已处理文件，避免重复运算

## 📦 技术栈
Python, faster-whisper, ffmpeg, DeepSeek API

## 📁 项目模块
1. 视频爬取模块：关键词搜索 + 视频下载，断点保存任务列表
2. 语音转写模块：faster-whisper本地转写，输出带时间戳字幕
3. 问答提取模块：调用DeepSeek API抽取问答对
4. 结果汇总模块：统计高频问题，输出清单文档

## ⚠️ 注意事项
- DeepSeek API密钥请放在`.env`，**不要提交到仓库**
- 下载的视频、模型权重不会上传仓库（.gitignore自动过滤）
