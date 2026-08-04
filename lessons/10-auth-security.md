# 第 10 课：认证、授权与安全边界

## 认证和授权

- Authentication：你是谁；
- Authorization：你能做什么；
- Ownership：这个资源是否属于你或你的租户。

登录成功不代表可以访问任意工单。每条查询都要执行 owner/tenant 检查。

## Token 基本边界

- Access Token：短期、用于请求；
- Refresh Token：长期、高价值，服务端通常只保存哈希；
- JWT 必须验证签名、过期时间、issuer、audience；
- 注销和全设备撤销通常需要 Session/版本状态，不能只相信无状态 JWT。

## 服务端可信身份

客户端 Body 中的 `user_id` 不可信。Gateway 验证 Token 后，可以通过受保护的内部 Header/RPC 字段传播身份；下游还需验证调用来源。

## 常见风险

- SQL 注入：参数化查询；
- SSRF：外部 URL allowlist、DNS/跳转复核、私网阻断；
- Mass Assignment：只接收明确允许修改的字段；
- 日志泄密：不记录 Token、密码、完整手机号、Prompt 秘密；
- 越权：服务端资源归属检查；
- 重放：nonce、时间窗、幂等事件 ID；
- 密钥泄漏：Secret/环境变量、轮换和最小权限。

## Webhook 验签

对原始请求字节计算 HMAC，不要先解析再重新序列化；比较签名使用常量时间函数，并同时检查时间窗口与 nonce。

## 练习

为“查询工单、关闭工单、管理员列表”写三类权限测试：未登录、登录但非 owner、管理员角色不足。
