# OBS Solution Uploader — OBS 一键上传工具

将 Terraform / Solution as Code 文件一键上传到华为云 OBS，自动设置公共读权限并返回公网访问 URL。提高上传效率

> **选择一个文件 + 选择区域 → 点击上传 → 自动完成全部操作 → 返回公共访问 URL**

---
## 开始使用
### 1.下载.exe
https://github.com/Justin-TangPan/obs-solution-uploader/releases/tag/v1.0.0

### 2.双击软件
选择“设置”
填入你的华为云AK\SK
选择“保存”

### 3.选择文件

### 4.选择region

### 5.点击上传
<img width="400" height="500" alt="image" src="https://github.com/user-attachments/assets/815d7259-9525-4674-a727-3cfb95840491" />

---


## 设置面板（前端可配置）

点击主界面右上角 **⚙️ 设置** 打开设置对话框，可配置以下内容，保存后持久化到 `user_settings.json`（不进 Git），默认值即当前商定值：

### 1. 华为云凭证
- Access Key / Secret Key / Security Token
- Secret Key 以密码形式显示
- 留空则回退到环境变量 / config.yaml

### 2. 目标路径前缀
- 根目录（默认 `solution-as-code-publicbucket`）
- 模块目录（默认 `solution-as-code-moudle`）
- 最终路径：`{root}/{module}/{solution-name}/{filename}`

### 3. 区域映射表
- 表格可直接编辑：显示名称 / Region Code / Bucket / Endpoint
- **＋ 新增区域** / **－ 删除选中** / **↺ 恢复默认区域**
- 保存后主界面区域下拉框立即刷新

### 配置文件
- 路径：exe 同目录（打包后）或项目根目录（开发时）下的 `user_settings.json`
- 格式示例：
  ```json
  {
    "credentials": {"access_key": "...", "secret_key": "...", "security_token": ""},
    "path_prefix": {"root_prefix": "solution-as-code-publicbucket", "module_prefix": "solution-as-code-moudle"},
    "regions": {"华北-北京四": {"bucket": "documentation-samples", "region": "cn-north-4", "endpoint": "obs.cn-north-4.myhuaweicloud.com"}}
  }
  ```
- 已加入 `.gitignore`，绝不提交

---

```bash
# 在项目根目录下
python -m app.main
```

或：

```bash
python app/main.py
```

---

## 五、使用流程

1. **选择文件**：点击文件区域选择，或直接拖拽文件到窗口（**支持多文件**）
2. **自定义目录**（可选）：修改目录名，所有文件上传到此目录下；默认使用文件名（去掉扩展名）
3. **选择区域**：下拉选择目标区域（如 `华北-北京四`）
4. 自动显示目标 Bucket、Region、Endpoint、目标路径
5. 点击 **🚀 上传到 OBS**
6. 若对象已存在，弹窗提示是否覆盖
7. 上传完成后，结果区显示每个文件的状态：
   - ✓ 文件上传成功
   - ✓ 对象权限设置成功
   - ✓ 公网 URL 生成成功
8. 点击 **复制链接** 或 **打开链接**；多文件时可点击 **▼ 查看全部 URL**

---

## 六、北京四完整上传示例

输入：

```
文件：deploying-cognee.tf
区域：华北-北京四
```

工具自动完成：

```
Bucket:   documentation-samples
Region:   cn-north-4
Endpoint: obs.cn-north-4.myhuaweicloud.com
Object Key: solution-as-code-publicbucket/solution-as-code-moudle/deploying-cognee/deploying-cognee.tf
ACL:       public-read
```

返回公网 URL：

```
https://documentation-samples.obs.cn-north-4.myhuaweicloud.com/solution-as-code-publicbucket/solution-as-code-moudle/deploying-cognee/deploying-cognee.tf
```

---

## 功能特性

- ✅ 文件选择 + 拖拽上传（**支持多文件**）
- ✅ **自定义目录**：首页可自由输入目录名，默认自动填充文件名
- ✅ 区域选择，自动映射 Bucket / Region / Endpoint
- ✅ 自动生成 Object Key：`{root}/{module}/{自定义目录}/{filename}`
- ✅ 调用华为云 OBS 官方 SDK 上传（不自行实现签名）
- ✅ 上传后自动设置对象 ACL 为公共读
- ✅ 自动生成公网 URL，一键复制 / 打开
- ✅ 重复对象提示覆盖
- ✅ 完整日志区，敏感信息脱敏
- ✅ 友好错误提示（认证失败 / Bucket 不存在 / 权限不足 / 网络异常 / ACL 失败）
- ✅ 可打包为 Windows `.exe`
- ✅ **设置面板**：凭证 / 目标路径前缀 / 区域映射表 全部前端可配置，持久化到 `user_settings.json`，默认值即当前商定值

---

## 项目结构

```
obs-solution-uploader/
├── app/
│   ├── main.py                 # 入口
│   ├── config/
│   │   ├── regions.py          # 区域 → Bucket/Endpoint 映射
│   │   └── settings.py         # 固定目录、ACL、环境变量名
│   ├── services/
│   │   ├── obs_service.py      # OBS SDK 封装
│   │   ├── upload_service.py   # 上传流程编排
│   │   └── url_service.py      # 公网 URL 生成
│   ├── ui/
│   │   ├── main_window.py      # 主窗口
│   │   ├── upload_widget.py    # 上传表单（含拖拽）
│   │   ├── result_widget.py    # 结果展示
│   │   ├── settings_dialog.py  # 设置对话框（凭证/路径/区域）
│   │   └── worker.py           # 上传工作线程
│   └── utils/
│       ├── auth.py             # 凭证加载
│       ├── file_utils.py       # 文件名解析 / Object Key 生成
│       └── logger.py           # 安全日志
├── tests/                      # 单元测试
├── requirements.txt
├── .env.example
├── config.yaml.example
├── .gitignore
├── build.spec                  # PyInstaller 打包配置
└── README.md
```

UI、业务逻辑、OBS SDK、区域配置、工具函数相互解耦。

> `app/config/config_manager.py` 是配置中枢：凭证、路径前缀、区域映射全部由它统一加载/保存，默认值即代码内商定值。

---

## 区域映射表（示例，用作定义多桶管理）

| 区域 | Region Code | Bucket | Endpoint |
| --- | --- | --- | --- |
| 华北-北京四 | cn-north-4 | documentation-samples | obs.cn-north-4.myhuaweicloud.com |
| 华南-广州 | cn-south-1 | documentation-samples-2 | obs.cn-south-1.myhuaweicloud.com |
| 华东-上海 | cn-east-3 | documentation-samples-3 | obs.cn-east-3.myhuaweicloud.com |
| 西南-贵阳 | cn-southwest-2 | documentation-samples-9 | obs.cn-southwest-2.myhuaweicloud.com |
| 华北-乌兰察布一 | cn-north-9 | documentation-samples-17 | obs.cn-north-9.myhuaweicloud.com |
| cn-east-4 | cn-east-4 | documentation-samples-16 | obs.cn-east-4.myhuaweicloud.com |
| 中国-香港 | ap-southeast-1 | documentation-samples-5 | obs.ap-southeast-1.myhuaweicloud.com |
| 亚太-新加坡 | ap-southeast-3 | documentation-samples-4 | obs.ap-southeast-3.myhuaweicloud.com |
| 亚太-曼谷 | ap-southeast-2 | documentation-samples-6 | obs.ap-southeast-2.myhuaweicloud.com |
| 亚太-雅加达 | ap-southeast-4 | documentation-samples-18 | obs.ap-southeast-4.myhuaweicloud.com |
| 土耳其-伊斯坦布尔 | tr-west-1 | documentation-samples-8 | obs.tr-west-1.myhuaweicloud.com |
| 南非-约翰内斯堡 | af-south-1 | documentation-samples-11 | obs.af-south-1.myhuaweicloud.com |
| 中东-利雅得 | me-east-1 | documentation-samples-12 | obs.me-east-1.myhuaweicloud.com |
| 拉美-墨西哥城一 | na-mexico-1 | documentation-samples-19 | obs.na-mexico-1.myhuaweicloud.com |
| 拉美-墨西哥城二 | na-mexico-2 | documentation-samples-13 | obs.na-mexico-2.myhuaweicloud.com |
| 拉美-圣保罗一 | sa-brazil-1 | documentation-samples-14 | obs.sa-brazil-1.myhuaweicloud.com |
| 拉美-圣地亚哥 | la-south-2 | documentation-samples-15 | obs.la-south-2.myhuaweicloud.com |
| af-north-1 | af-north-1 | documentation-samples-10 | obs.af-north-1.myhuaweicloud.com |

新增区域只需在 `app/config/regions.py` 的 `REGIONS` 中追加一项。

---
