# -*- coding: utf-8 -*-
"""
华为云 OBS SDK 封装。

使用官方 SDK esdk-obs-python（pip install esdk-obs-python）。
不自行实现签名算法，全部委托给官方 ObsClient。

封装目标：
- 屏蔽 SDK 版本差异，业务层只依赖本模块的简洁接口。
- 统一把 SDK 异常/状态码翻译成业务友好的 ObsError。
"""

from typing import Optional

from app.config.regions import RegionConfig
from app.config.settings import ACL_PUBLIC_READ
from app.utils.auth import Credentials
from app.utils.logger import logger

try:
    from obs import ObsClient  # 官方 SDK
    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - 仅在未安装 SDK 时触发
    ObsClient = None  # type: ignore
    _SDK_AVAILABLE = False


class ObsError(Exception):
    """OBS 操作业务异常，message 已是用户友好文案。"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def _ensure_sdk() -> None:
    if not _SDK_AVAILABLE:
        raise ObsError(
            "未检测到华为云 OBS SDK，请先执行 pip install esdk-obs-python。"
        )


def _format_sdk_error(resp, default_msg: str) -> ObsError:
    """把 SDK 返回结果翻译成 ObsError。"""
    status = getattr(resp, "status", None)
    reason = getattr(resp, "reason", "") or ""
    error_code = ""
    error_msg = ""
    try:
        if getattr(resp, "errorCode", None):
            error_code = resp.errorCode
        if getattr(resp, "errorMessage", None):
            error_msg = resp.errorMessage
    except Exception:
        pass

    # 根据状态码给出友好提示
    if status in (403, 401):
        msg = "认证失败，请检查华为云 Access Key / Secret Key。"
    elif status == 404:
        msg = "目标区域对应的 OBS Bucket 不存在。"
    elif status is not None and 500 <= status < 600:
        msg = f"OBS 服务端异常（{status}），请稍后重试。"
    else:
        detail = error_msg or reason or default_msg
        msg = f"{default_msg}（HTTP {status}）" if status else detail

    return ObsError(msg, status)


class ObsService:
    """OBS 操作服务。"""

    def __init__(self, credentials: Credentials, region: RegionConfig):
        if not credentials or not credentials.is_valid():
            raise ObsError("缺少华为云凭证，无法初始化 OBS 客户端。")
        _ensure_sdk()
        self._region = region
        self._credentials = credentials
        try:
            self._client = ObsClient(
                access_key_id=credentials.access_key,
                secret_access_key=credentials.secret_key,
                server=region.server,
                security_token=credentials.security_token,
            )
        except Exception as e:
            # 不暴露凭证细节
            logger.error("OBS 客户端初始化失败。")
            raise ObsError("OBS 客户端初始化失败，请检查凭证与区域配置。") from e

    # ------------------------------------------------------------------
    # Bucket 检查
    # ------------------------------------------------------------------
    def check_bucket_accessible(self) -> None:
        """检查 Bucket 是否存在且可访问。失败抛出 ObsError。"""
        try:
            resp = self._client.headBucket(self._region.bucket)
        except Exception:
            logger.error("Bucket 访问异常，请检查网络连接。")
            raise ObsError("网络连接异常，请稍后重试。")
        status = getattr(resp, "status", None)
        if status == 200:
            return
        if status == 404:
            raise ObsError("目标区域对应的 OBS Bucket 不存在。", status)
        if status in (403, 401):
            raise ObsError("当前账号没有该 Bucket 的访问权限。", status)
        raise _format_sdk_error(resp, "Bucket 访问失败")

    # ------------------------------------------------------------------
    # 对象存在性检查
    # ------------------------------------------------------------------
    def object_exists(self, object_key: str) -> bool:
        """判断对象是否已存在。"""
        try:
            resp = self._client.headObject(self._region.bucket, object_key)
        except Exception:
            raise ObsError("网络连接异常，请稍后重试。")
        status = getattr(resp, "status", None)
        if status == 200:
            return True
        if status == 404:
            return False
        if status in (403, 401):
            raise ObsError("认证失败，请检查华为云 Access Key / Secret Key。", status)
        raise _format_sdk_error(resp, "对象检查失败")

    # ------------------------------------------------------------------
    # 上传文件
    # ------------------------------------------------------------------
    def upload_file(self, object_key: str, file_path: str,
                    on_progress=None) -> None:
        """上传本地文件到指定 Object Key。失败抛出 ObsError。

        :param on_progress: 可选回调 on_progress(transferred:int, total:int) -> None
        """
        progress_cb = None
        if on_progress:
            def progress_cb(transferred, total, _extra=None):
                try:
                    on_progress(int(transferred), int(total))
                except Exception:
                    pass

        try:
            resp = self._client.putFile(
                self._region.bucket, object_key, file_path,
                progressCallback=progress_cb,
            )
        except Exception:
            logger.error("文件上传异常，请检查网络连接。")
            raise ObsError("文件上传失败，请检查网络连接和 OBS 权限。")
        status = getattr(resp, "status", None)
        if status in (200, 204):
            return
        if status in (403, 401):
            raise ObsError("认证失败，请检查华为云 Access Key / Secret Key。", status)
        raise _format_sdk_error(resp, "文件上传失败，请检查网络连接和 OBS 权限。")

    # ------------------------------------------------------------------
    # 设置公共读 ACL
    # ------------------------------------------------------------------
    def set_public_read(self, object_key: str) -> None:
        """将对象 ACL 设置为公共读。失败抛出 ObsError。

        使用官方 setObjectAcl 接口的 aclControl 参数（canned ACL 字符串）。
        注意：SDK 中 acl 参数期望 ACL 对象，canned 字符串必须传给 aclControl。
        """
        try:
            resp = self._client.setObjectAcl(
                self._region.bucket, object_key, aclControl=ACL_PUBLIC_READ
            )
        except Exception:
            raise ObsError("公共读权限设置失败，请检查 OBS 权限。")
        status = getattr(resp, "status", None)
        if status in (200, 204):
            return
        if status in (403, 401):
            raise ObsError("公共读权限设置失败：当前账号无权修改对象 ACL。", status)
        raise _format_sdk_error(resp, "公共读权限设置失败。")

    # ------------------------------------------------------------------
    # 验证对象
    # ------------------------------------------------------------------
    def verify_object(self, object_key: str) -> bool:
        """验证对象是否上传成功（存在即可）。"""
        return self.object_exists(object_key)

    # ------------------------------------------------------------------
    # 列举子目录
    # ------------------------------------------------------------------
    def list_subdirectories(self, prefix: str) -> list:
        """
        列举指定前缀下的子目录（一级）。

        :param prefix: 如 "solution-as-code-publicbucket/solution-as-code-moudle/"
        :return: 子目录名列表，如 ["deploying-cognee", "deploying-dify"]
        :raises ObsError
        """
        # 确保前缀以 / 结尾，否则会把它本身当作 key 前缀
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        dirs = []
        marker = None
        try:
            while True:
                resp = self._client.listObjects(
                    self._region.bucket,
                    prefix=prefix,
                    delimiter="/",
                    marker=marker,
                    max_keys=1000,
                )
                status = getattr(resp, "status", None)
                if status not in (200,):
                    raise _format_sdk_error(resp, "列举目录失败")

                # commonPrefixs 即子目录
                common = getattr(resp, "commonPrefixs", None) or []
                for item in common:
                    full = getattr(item, "prefix", "") or ""
                    # 去掉前缀和结尾 /，得到子目录名
                    name = full
                    if name.startswith(prefix):
                        name = name[len(prefix):]
                    name = name.rstrip("/")
                    if name:
                        dirs.append(name)

                # 处理分页
                if getattr(resp, "is_truncated", False):
                    marker = getattr(resp, "next_marker", None)
                    if not marker:
                        break
                else:
                    break
        except ObsError:
            raise
        except Exception:
            raise ObsError("列举目录失败，请检查网络连接和 OBS 权限。")

        # 去重保序
        seen = set()
        unique = []
        for d in dirs:
            if d not in seen:
                seen.add(d)
                unique.append(d)
        return unique
