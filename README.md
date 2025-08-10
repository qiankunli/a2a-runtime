# 简介

a2a-runtime 是一个支持a2a协议的agent 容器，用户可以在agent 包下实现自己的agent（不限制框架），多个agent以a2a协议暴漏在特定endpoint下。

比如用户实现了两个agent，分别是agent1和agent2，同属于一个namespace下（比如default），则
```
# 访问agent1 rpc url
http://a2a-runtime:port/default/agent1

# 访问agent2 rpc url
http://a2a-runtime:port/default/agent2
```

<img src="assets/overview.png" alt="overview"/>

建议与[chat-a2a](https://github.com/qiankunli/chat-a2a) 配合使用

# 改动

对a2a 一些现有实现的改动放在server.a2a2 包下
1. 提供一个入口RuntimeAgentExecutor，将收到的请求转发给具体的a2a AgentExecutor
2. 提供一个新的RuntimeA2AFastAPIApplication（仿自eA2AFastAPIApplication）将不同agent 挂在到同一个endpoint（不同path）下
3. 提供一个RuntimeRequestHandler（仿自DefaultRequestHandler），使得新message/send 也可以指定task_id

# 联系我

项目仍不完善，欢迎共创

<img src="assets/wechat-qrcode.jpg" alt="WeChat QR Code" width="350" height="350"/>