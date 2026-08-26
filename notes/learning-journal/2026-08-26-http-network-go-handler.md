# 2026-08-26：从 HTTP 请求一路走到 Go `http.Handler`

这份日志沉淀一次完整的“网络 -> HTTP -> Go `net/http`”心智模型。重点不是记术语，而是知道一次请求为什么按这个顺序经过这些层，以及看到错误时应该先查哪一层。

---

## 1. HTTP Request 先读懂什么

典型请求：

```http
GET /api/v1/orders/123 HTTP/1.1
Host: api.example.com
Authorization: Bearer xxx
Accept: application/json
```

核心关系：

```text
GET
= HTTP Method，表达这次请求想做什么

/api/v1/orders/123
= Path

/api/v1/orders/{id}
= Route Pattern

123
= Path Parameter 的具体值

HTTP/1.1
= HTTP 协议版本
```

Router 选择 Handler 时，关键是：

```text
Method + Route Pattern
-> Handler
```

不是根据具体的 `123`、`999` 选择不同 Handler。同一个：

```text
GET /api/v1/orders/{id}
```

可以处理：

```text
/orders/123
/orders/999
```

只是提取出来的 `id` 不同。

### 404 与 405

```text
Path 都匹配不到
-> 404 Not Found

Path 能匹配，但当前 Method 不被该路由允许
-> 405 Method Not Allowed
```

例如只有：

```text
GET /orders/{id}
DELETE /orders/{id}
```

请求：

```text
POST /orders/88
```

应该理解成：

```text
Path ✅
Method ❌
-> 405
```

具体框架可能有实现差异，但 API 语义上这是 405 的典型情况。

---

## 2. Header 中几个最容易混的字段

```text
Host
= 这次请求要访问的目标主机名/域名
≠ “物理宿主机叫什么”

Authorization
= HTTP 中携带认证凭证的标准 Header
≠ “授权已经通过”

Content-Type
= 当前 Message Body 是什么格式

Accept
= Client 希望收到什么表示格式
```

最容易记错的一组：

```text
Content-Type
= 我发出的 Body 是什么格式

Accept
= 我希望你返回什么格式
```

`Content-Type` 既可以出现在 Request，也可以出现在 Response，因为它描述的是“当前这条 HTTP Message 的 Body”。

---

## 3. Authentication 与 Authorization

两个词必须彻底分开：

```text
Authentication
= 认证
= 你是谁？

Authorization
= 授权
= 你能做什么？
```

完整关系：

```text
Authorization: Bearer TOKEN
        ↓
提供 Credential
        ↓
Authentication
验证这个 Credential 代表谁
        ↓
Principal
例如 user_id / tenant_id / role
        ↓
Authorization
检查这个 Principal 能不能执行当前 Action / 访问当前 Resource
```

因此：

```text
Authorization Header
≠ Authorization 检查结果
```

常见状态码：

```text
401
= 没有有效身份 / Authentication 失败

403
= 身份已确定，但没有权限 / Authorization 失败
```

真实资源级授权还可能依赖 owner、tenant、resource state，因此不一定全部能在一个前置 middleware 中完成。

---

## 4. Client 不是“前端页面”的同义词

```text
Client
= 主动发起请求的一方
```

可能是：

```text
Browser
Mobile App
curl
Postman
Go http.Client
Python 程序
另一个后端服务
```

同一个 Go 服务在不同通信段里可以同时扮演不同角色：

```text
Mobile App -> Go API
Mobile App = Client
Go API = Server

Go API -> downstream API
Go API = Client
downstream API = Server
```

安全上的直接结论：

> 前端不是安全边界。攻击者可以绕过 UI 直接构造 HTTP Request，所以后端必须自己做认证、授权和输入校验。

---

## 5. Domain -> DNS -> IP -> Port

一次访问：

```text
https://api.example.com
```

可以先展开为：

```text
Domain
api.example.com
   ↓
DNS
把域名解析为网络地址
   ↓
IP
   ↓
Port
定位该地址上的网络服务
```

粗略类比：

```text
IP
≈ 大楼地址

Port
≈ 大楼里的房间号
```

但 Port 本身只是编号，不是程序，也不是 Socket。

### `127.0.0.1`

```text
127.0.0.1
= loopback
= 当前网络命名空间中的“自己”
```

所以在宿主机、服务器、Docker 容器中，`127.0.0.1` 指向的是各自自己，不是永远指向开发者电脑。

### `0.0.0.0`

在监听语境中：

```text
0.0.0.0:8080
```

通常表示在本机所有 IPv4 网络接口上监听 8080，而不是一个应该被 Client 当成真实目标地址访问的远端地址。

---

## 6. listen / bind / accept / Socket

“监听端口”更准确的说法是：

> 进程通过操作系统创建网络 Socket，把它绑定到某个 `IP:Port`，进入监听状态，等待新的 Client Connection。

概念顺序：

```text
bind
= 把 Socket 绑定到 IP:Port

listen
= 开始等待新连接

accept
= 接受一个已经到来的具体连接
```

### Port 与 Socket

```text
Port
= 编号

Socket
= OS 管理、程序用于网络通信的对象/端点
```

服务器通常有：

```text
Listening Socket
= 专门等待新连接

Connected Socket A
= 服务 Client A 的已建立连接

Connected Socket B
= 服务 Client B 的已建立连接
```

因此一个 `:8080` 可以同时服务很多 Client，而不是“一个端口只能对应一个连接”。

---

## 7. TCP Connection 与 HTTP Request 不是一回事

TCP 可以先理解成：

> 给应用提供可靠、有序的字节流。

它不理解：

```text
GET
JSON
JWT
/orders/123
```

这些是 HTTP 的语义。

关系：

```text
HTTP
= 定义 Request / Response 的格式和语义

TCP
= 传输有序可靠的 bytes
```

所以：

```text
TCP Connection
= 通信通道

HTTP Request
= 在这条通道中传输的一次应用层请求
```

一个 TCP Connection 可以在一段时间内承载多个 HTTP Request；两者不能画等号。

### TCP 三次握手的初始心智模型

```text
Client -> Server : SYN
Server -> Client : SYN + ACK
Client -> Server : ACK
```

现在只需要理解：双方在正式传应用数据前建立连接状态，不需要提前深入 sequence number、拥塞控制等算法。

---

## 8. TLS / HTTPS

TCP 负责可靠传输，不等于传输内容保密。

TLS 主要提供：

```text
Encryption
= 机密性

Integrity
= 传输内容被修改时能发现

Server Authentication
= Client 验证目标服务器身份
```

对当前 HTTP/1.1 / HTTP/2 心智模型：

```text
HTTP
↓
TLS
↓
TCP
```

也就是常说的 HTTPS。

### Certificate

服务器证书会参与证明目标域名对应的服务器身份。Client 会关注域名匹配、有效期、签名链、可信 CA 等。

证书体系与 JWT signing key 不是同一个东西：

```text
JWT Signature
= 保护 Token 的完整性/真实性

TLS
= 保护网络传输通道
```

因此：

> JWT 有签名仍然必须使用 HTTPS。签名不能阻止攻击者把偷来的 Bearer Token 原样重放。

---

## 9. Nginx 在链路里的位置

Nginx 可以先理解成放在 Client 和业务服务之间的通用网络入口之一。

典型结构：

```text
Client
  ↓ HTTPS :443
Nginx
  ↓ HTTP :8080 或另一段 HTTPS
Go API
```

常见职责：

```text
Reverse Proxy
TLS termination
Load Balancing
Routing
Rate limiting / access log 等通用入口能力
```

### Reverse Proxy

```text
Client
↓
Nginx
↓
Backend
```

Client 不需要知道后面真实 Backend 有几个实例、内部端口是什么。

与 Forward Proxy 的第一层区别：

```text
Forward Proxy
= 站在 Client 一侧替 Client 找 Server

Reverse Proxy
= 站在 Server 一侧替 Backend 接 Client
```

Nginx 能承担一些 API Gateway 能力，但：

```text
Nginx ≠ API Gateway 这个架构概念本身
```

---

## 10. OS -> Process -> Go `net/http`

网络数据不是直接从“网线”进入 Handler。

更准确：

```text
Network
↓
Operating System network stack
↓
Socket
↓
Go Process
↓
net/http
```

`Process` 可以先理解成：

> 一个程序真正运行起来后的执行实例，由 OS 管理内存、线程、Socket 等资源。

### `http.ListenAndServe`

```go
http.ListenAndServe(":8080", handler)
```

概念上帮应用完成很多底层工作：

```text
create listener / socket
↓
bind + listen
↓
accept connections
↓
read HTTP bytes
↓
parse HTTP
↓
build *http.Request
↓
dispatch Handler
↓
serialize/write HTTP Response
```

所以它不是“直接运行 Handler”。

---

## 11. `*http.Request` 与 `http.ResponseWriter`

Client 发到网络上的最终是 bytes，不是 Go struct。

`net/http` 解析 HTTP 后，构造：

```go
*http.Request
```

于是 Handler 可以读取：

```go
r.Method
r.URL
r.Header
r.Body
r.Host
r.Context()
```

而：

```go
http.ResponseWriter
```

是 Handler 用来构造 Response 的接口：

```go
w.Header().Set(...)
w.WriteHeader(...)
w.Write(...)
```

方向：

```text
r = Client -> Server 的 Request
w = Server -> Client 的 Response 构造入口
```

---

## 12. `http.Handler` / `HandlerFunc` / `ServeHTTP`

Go 标准库核心接口：

```go
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

因此：

> 任何类型，只要拥有正确签名的 `ServeHTTP` 方法，就满足 `http.Handler`。

普通函数：

```go
func healthHandler(w http.ResponseWriter, r *http.Request) {
    // ...
}
```

本身没有 `ServeHTTP` 方法，所以它本身不是 `http.Handler`。

`http.HandlerFunc` 是一个命名函数类型，并且标准库给它实现了：

```go
func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) {
    f(w, r)
}
```

因此：

```text
普通 func(w, r)
↓
转换成 HandlerFunc
↓
HandlerFunc 有 ServeHTTP
↓
满足 http.Handler
```

这就是一个非常典型的 Adapter：

> `HandlerFunc` 把普通处理函数对接到 `http.Handler` 接口。

这也是本次复述已经讲对的关键点。

### `ServeMux`

`*http.ServeMux` 自身也实现了 `ServeHTTP`，因此它也是一个 `http.Handler`。

```text
net/http
↓
ServeMux.ServeHTTP
↓
根据 Method + Route Pattern 找具体 Handler
↓
具体 Handler.ServeHTTP
```

所以 Router 和 Handler 并不是两套完全无关的机制；Router 本身也可以作为一个更上层的 Handler。

---

## 13. 当前错误定位地图

看到错误先问：**请求最后成功走到哪一层？第一处错误状态在哪里？**

```text
Could not resolve host
-> DNS

connection refused
-> 已经在找目标 IP:Port / TCP 建连附近，通常还没到 HTTP Handler

certificate error
-> TLS handshake / certificate validation

404
-> 已经收到 HTTP Response；路由或资源查找失败

405
-> Path 语义能匹配，但 Method 不允许

401
-> Authentication

403
-> Authorization

500
-> Server 内部未预期错误

503
-> Server 明确表示当前服务/依赖暂时不可用
```

不要看到所有错误都先查 Handler；先定位层级。

---

## 14. 当前完整心智图

```text
Client
↓
Domain
↓
DNS
↓
IP + Port
↓
Server listening socket
↓
TCP connection
↓
TLS（HTTPS 时）
↓
OS network stack / connected socket
↓
Go process
↓
net/http
↓
*http.Request
↓
ServeMux / Router
↓
Middleware
↓
Authentication
↓
Principal
↓
Authorization（部分资源级判断也可能更后）
↓
Handler
↓
Service
↓
Repository
↓
Database
↓
ResponseWriter
↓
net/http
↓
Client
```

---

## 15. 当前掌握状态与下一步

本次已经能在对话中正确复述/纠正：

- Path 能匹配但 Method 不支持 -> 405；
- Authentication = 身份认证，Authorization = 权限判断；
- listen = 进程通过 OS 在 `IP:Port` 等待连接；
- TCP Connection 与 HTTP Request 不是同一个东西；
- `HandlerFunc` 有 `ServeHTTP`，因此能把普通函数适配成 `http.Handler`。

但“听懂并能回答”还不等于独立工程能力。下一步先继续：

```text
Middleware wrapper / onion 模型
↓
Handler -> Service -> Repository -> Database 职责
↓
关闭文档完整复述 Request -> Response 链
↓
再进入 context.Context
```

在进入 `context.Context` 前，先确保不靠提示也能解释：

1. `http.ListenAndServe` 前后到底发生了什么；
2. Router 为什么根据 `Method + Route Pattern` 找 Handler；
3. `HandlerFunc` 为什么满足 `http.Handler`；
4. Middleware 为什么适合放横切逻辑；
5. `connection refused`、TLS error、404、401、403 分别大概位于哪一层。
