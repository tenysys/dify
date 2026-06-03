# Dify Console API 文档

本文档基于当前仓库代码整理，覆盖以下接口：

- `POST /console/api/auth-service/login`
- `POST /console/api/apps`
- `PUT /console/api/apps/{app_id}`
- `DELETE /console/api/apps/{app_id}`

适用场景：

- 先通过 `auth-service` 令牌登录 Dify Console
- 再使用登录返回的控制台访问令牌创建、更新、删除应用

## 1. auth-service 登录

### 接口地址

`POST /console/api/auth-service/login`

### 接口说明

使用外部 `auth-service` 签发的访问令牌登录 Dify Console。

服务端会执行以下动作：

- 校验传入的 `auth-service token`
- 从 `auth-service` 拉取用户信息
- 按配置的默认工作空间自动创建或绑定 Dify 账号
- 确保账号加入默认工作空间
- 切换到该工作空间
- 返回 Dify Console 自身的登录令牌

### 请求头

```http
Content-Type: application/json
```

该接口当前不要求预先携带 Dify Console 的 `Authorization`。

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `token` | string | 是 | `auth-service` 签发的访问令牌 |

### 请求示例

```json
{
  "token": "auth-service-access-token"
}
```

### 成功响应

HTTP 状态码：`200 OK`

```json
{
  "result": "success",
  "data": {
    "access_token": "dify-console-access-token",
    "refresh_token": "dify-console-refresh-token",
    "csrf_token": "dify-console-csrf-token"
  }
}
```

### 成功响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `result` | string | 固定为 `success` |
| `data.access_token` | string | Dify Console 访问令牌，后续调用受保护的 `/console/api/*` 接口时使用 |
| `data.refresh_token` | string | Dify Console 刷新令牌 |
| `data.csrf_token` | string | Dify Console CSRF 令牌 |

### 响应头

成功时响应头还会返回：

```http
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

### 失败响应

#### 401 auth-service token 无效或过期

```json
{
  "code": "auth_service_authentication_failed",
  "message": "Invalid or expired auth-service token.",
  "status": 401
}
```

#### 500 auth-service 配置错误

```json
{
  "code": "auth_service_configuration_error",
  "message": "auth-service login is not configured correctly.",
  "status": 500
}
```

### 登录后建议保留的令牌

登录成功后，建议保存：

- `access_token`
- `refresh_token`
- `csrf_token`

后续调用应用接口时，至少需要：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

如希望与 Dify Console 前端现有调用方式保持一致，建议同时携带：

```http
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

## 2. 创建应用

### 接口地址

`POST /console/api/apps`

### 接口说明

创建一个新的应用。

当前支持的 `mode`：

- `workflow`：工作流
- `advanced-chat`：对话流
- `chat`：聊天助手
- `agent-chat`：Agent 对话
- `completion`：文本生成

### 鉴权要求

需要 Dify Console 登录态。

推荐请求头：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

最少要求：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 应用名称，最少 1 个字符 |
| `description` | string \| null | 否 | 应用描述，最大 400 字符 |
| `mode` | string | 是 | 支持：`chat`、`agent-chat`、`advanced-chat`、`workflow`、`completion` |
| `icon_type` | string \| null | 否 | 图标类型，常见值：`emoji`、`image`、`link` |
| `icon` | string \| null | 否 | 图标内容，`emoji` 时通常直接传 emoji |
| `icon_background` | string \| null | 否 | 图标背景色，例如 `#FFEAD5` |

### 关于 `id`

当前接口不支持在请求体中指定应用 `id`。

不要传：

```json
{
  "id": "..."
}
```

应用主键 `id` 由服务端自动生成。

### 工作流创建示例

```json
{
  "name": "订单处理工作流",
  "description": "用于处理订单审批和通知",
  "mode": "workflow",
  "icon_type": "emoji",
  "icon": "⚙️",
  "icon_background": "#FFEAD5"
}
```

### 对话流创建示例

```json
{
  "name": "客服对话流",
  "description": "用于多轮客服问答",
  "mode": "advanced-chat",
  "icon_type": "emoji",
  "icon": "💬",
  "icon_background": "#D1FADF"
}
```

### 成功响应

HTTP 状态码：`201 Created`

```json
{
  "id": "b8d6b0e0-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "订单处理工作流",
  "description": "用于处理订单审批和通知",
  "mode": "workflow",
  "icon": "⚙️",
  "icon_background": "#FFEAD5",
  "enable_site": false,
  "enable_api": false,
  "model_config": null,
  "workflow": null,
  "tracing": null,
  "use_icon_as_answer_icon": false,
  "created_by": "user-xxx",
  "created_at": 1710000000,
  "updated_by": "user-xxx",
  "updated_at": 1710000000,
  "access_mode": null,
  "tags": []
}
```

### 成功响应字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 应用 ID |
| `name` | string | 应用名称 |
| `description` | string \| null | 应用描述 |
| `mode` | string | 应用模式 |
| `icon` | string \| null | 图标内容 |
| `icon_background` | string \| null | 图标背景色 |
| `enable_site` | boolean | 是否启用站点 |
| `enable_api` | boolean | 是否启用 API |
| `model_config` | object \| null | 模型配置 |
| `workflow` | object \| null | 工作流摘要信息 |
| `tracing` | object \| null | tracing 配置 |
| `use_icon_as_answer_icon` | boolean \| null | 是否使用应用图标作为回答图标 |
| `created_by` | string \| null | 创建人 ID |
| `created_at` | integer \| null | 创建时间戳 |
| `updated_by` | string \| null | 更新人 ID |
| `updated_at` | integer \| null | 更新时间戳 |
| `access_mode` | string \| null | 访问模式 |
| `tags` | array | 标签列表 |

### `workflow` 字段说明

当 `workflow` 不为 `null` 时，结构如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | workflow ID |
| `created_by` | string \| null | 创建人 |
| `created_at` | integer \| null | 创建时间戳 |
| `updated_by` | string \| null | 更新人 |
| `updated_at` | integer \| null | 更新时间戳 |

### 注意事项

- 新建 app 成功后，`workflow` 通常仍为 `null`
- 如需初始化或保存工作流草稿，需要继续调用 `POST /console/api/apps/{app_id}/workflows/draft`

### 失败响应

#### 400 请求参数错误

```json
{
  "code": "invalid_param",
  "message": "具体错误信息",
  "status": 400
}
```

#### 401 未授权

```json
{
  "code": "unauthorized",
  "message": "Unauthorized.",
  "status": 401
}
```

#### 403 无权限或配额限制

可能场景包括：

- 当前账号未初始化
- 当前用户没有编辑权限
- 云版应用数达到订阅上限

示例：

```json
{
  "code": "unknown",
  "message": "The number of apps has reached the limit of your subscription.",
  "status": 403
}
```

## 3. 更新应用

### 接口地址

`PUT /console/api/apps/{app_id}`

### 接口说明

更新指定应用的基础信息。

`app_id` 需要是应用 UUID。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `app_id` | string | 是 | 应用 ID，UUID 格式 |

### 鉴权要求

需要 Dify Console 登录态，并且当前用户对该应用具备编辑权限。

推荐请求头：

```http
Authorization: Bearer <access_token>
Content-Type: application/json
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `name` | string | 是 | 应用名称，最少 1 个字符 |
| `description` | string \| null | 否 | 应用描述，最大 400 字符 |
| `icon_type` | string \| null | 否 | 图标类型 |
| `icon` | string \| null | 否 | 图标内容 |
| `icon_background` | string \| null | 否 | 图标背景色 |
| `use_icon_as_answer_icon` | boolean \| null | 否 | 是否将应用图标作为回答图标 |
| `max_active_requests` | integer \| null | 否 | 最大并发活跃请求数 |

### 请求示例

```json
{
  "name": "订单处理工作流-生产版",
  "description": "用于处理订单审批、通知和回调",
  "icon_type": "emoji",
  "icon": "🧩",
  "icon_background": "#FCE7F3",
  "use_icon_as_answer_icon": true,
  "max_active_requests": 20
}
```

### 成功响应

HTTP 状态码：`200 OK`

返回结构为 `AppDetailWithSite`。它在创建接口返回的 `AppDetail` 基础上，额外增加以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `icon_type` | string \| null | 图标类型 |
| `icon_url` | string \| null | 图标访问地址，服务端计算字段 |
| `api_base_url` | string \| null | API 基础地址 |
| `max_active_requests` | integer \| null | 最大并发活跃请求数 |
| `deleted_tools` | array | 已删除工具列表 |
| `site` | object \| null | WebApp 站点配置 |

成功响应示例：

```json
{
  "id": "b8d6b0e0-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "订单处理工作流-生产版",
  "description": "用于处理订单审批、通知和回调",
  "mode": "workflow",
  "icon_type": "emoji",
  "icon": "🧩",
  "icon_url": null,
  "icon_background": "#FCE7F3",
  "enable_site": false,
  "enable_api": false,
  "api_base_url": null,
  "max_active_requests": 20,
  "model_config": null,
  "workflow": null,
  "tracing": null,
  "use_icon_as_answer_icon": true,
  "deleted_tools": [],
  "site": null,
  "created_by": "user-xxx",
  "created_at": 1710000000,
  "updated_by": "user-xxx",
  "updated_at": 1710000100,
  "access_mode": null,
  "tags": []
}
```

### `site` 字段说明

当响应中的 `site` 不为 `null` 时，常见字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `access_token` | string \| null | 站点访问令牌 |
| `code` | string \| null | 站点 code |
| `title` | string \| null | 站点标题 |
| `icon_type` | string \| null | 站点图标类型 |
| `icon` | string \| null | 站点图标 |
| `icon_background` | string \| null | 站点图标背景色 |
| `description` | string \| null | 站点描述 |
| `default_language` | string \| null | 默认语言 |
| `chat_color_theme` | string \| null | 聊天主题色 |
| `chat_color_theme_inverted` | boolean \| null | 是否反转主题色 |
| `customize_domain` | string \| null | 自定义域名 |
| `copyright` | string \| null | 版权说明 |
| `privacy_policy` | string \| null | 隐私政策 |
| `custom_disclaimer` | string \| null | 自定义免责声明 |
| `customize_token_strategy` | string \| null | token 策略 |
| `prompt_public` | boolean \| null | 提示词是否公开 |
| `app_base_url` | string \| null | WebApp 基础地址 |
| `show_workflow_steps` | boolean \| null | 是否展示工作流步骤 |
| `use_icon_as_answer_icon` | boolean \| null | 是否使用图标作为回答图标 |
| `created_by` | string \| null | 创建人 |
| `created_at` | integer \| null | 创建时间戳 |
| `updated_by` | string \| null | 更新人 |
| `updated_at` | integer \| null | 更新时间戳 |

### 失败响应

#### 400 请求参数错误

```json
{
  "code": "invalid_param",
  "message": "具体错误信息",
  "status": 400
}
```

#### 401 未授权

```json
{
  "code": "unauthorized",
  "message": "Unauthorized.",
  "status": 401
}
```

#### 403 无权限

```json
{
  "code": "forbidden",
  "message": "Forbidden.",
  "status": 403
}
```

## 4. 删除应用

### 接口地址

`DELETE /console/api/apps/{app_id}`

### 接口说明

删除指定应用。

`app_id` 需要是应用 UUID。

控制器返回 `204 No Content`，响应体为空。

服务端当前行为分两段：

- 先删除应用主记录并提交事务
- 再异步触发“删除应用相关数据”任务

因此，从接口调用视角看，`204` 代表“删除请求已完成主记录删除并已触发后续清理任务”。

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `app_id` | string | 是 | 应用 ID，UUID 格式 |

### 鉴权要求

需要 Dify Console 登录态，并且当前用户对该应用具备编辑权限。

推荐请求头：

```http
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

### 成功响应

HTTP 状态码：`204 No Content`

响应体为空：

```http
(empty body)
```

### 失败响应

#### 401 未授权

```json
{
  "code": "unauthorized",
  "message": "Unauthorized.",
  "status": 401
}
```

#### 403 无权限

```json
{
  "code": "forbidden",
  "message": "Forbidden.",
  "status": 403
}
```

## 5. 推荐调用顺序

### 第一步：auth-service 登录

```http
POST /console/api/auth-service/login
```

拿到：

- `access_token`
- `refresh_token`
- `csrf_token`

### 第二步：创建应用

```http
POST /console/api/apps
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

### 第三步：更新应用

```http
PUT /console/api/apps/{app_id}
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

### 第四步：删除应用

```http
DELETE /console/api/apps/{app_id}
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
X-CSRF-Token: <csrf_token>
```

## 6. curl 示例

### 6.1 auth-service 登录

```bash
curl -X POST "http://<host>/console/api/auth-service/login" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "auth-service-access-token"
  }'
```

### 6.2 创建工作流应用

```bash
curl -X POST "http://<host>/console/api/apps" \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Refresh-Token: <refresh_token>" \
  -H "X-CSRF-Token: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "订单处理工作流",
    "description": "用于处理订单审批和通知",
    "mode": "workflow",
    "icon_type": "emoji",
    "icon": "⚙️",
    "icon_background": "#FFEAD5"
  }'
```

### 6.3 更新应用

```bash
curl -X PUT "http://<host>/console/api/apps/<app_id>" \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Refresh-Token: <refresh_token>" \
  -H "X-CSRF-Token: <csrf_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "订单处理工作流-生产版",
    "description": "用于处理订单审批、通知和回调",
    "icon_type": "emoji",
    "icon": "🧩",
    "icon_background": "#FCE7F3",
    "use_icon_as_answer_icon": true,
    "max_active_requests": 20
  }'
```

### 6.4 删除应用

```bash
curl -X DELETE "http://<host>/console/api/apps/<app_id>" \
  -H "Authorization: Bearer <access_token>" \
  -H "X-Refresh-Token: <refresh_token>" \
  -H "X-CSRF-Token: <csrf_token>"
```
