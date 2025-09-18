import os
import posixpath
from webdav3.client import Client
from dotenv import load_dotenv

# Load env vars once
load_dotenv()


class InfiniCloudClient:
    def __init__(self):
        """Initialize InfiniCLOUD client using credentials from .env"""
        hostname = os.getenv("INFINICLOUD_HOST")
        if hostname and not hostname.endswith("/"):
            hostname += "/"

        options = {
            "webdav_hostname": hostname,
            "webdav_login": os.getenv("INFINICLOUD_USER"),
            "webdav_password": os.getenv("INFINICLOUD_PASS"),
        }

        # Validate required settings
        if not options["webdav_hostname"]:
            raise ValueError("Missing INFINICLOUD_HOST in environment")
        if not options["webdav_login"]:
            raise ValueError("Missing INFINICLOUD_USER in environment")
        if not options["webdav_password"]:
            raise ValueError("Missing INFINICLOUD_PASS in environment")

        self.client = Client(options)

    def _ensure_folder(self, remote_folder: str):
        """Ensure a remote folder exists, create if missing (recursive)."""
        remote_folder = remote_folder.strip().rstrip("/")
        if not remote_folder or remote_folder == "/":
            return

        parts = [p for p in remote_folder.split("/") if p]
        current = ""
        for part in parts:
            current = posixpath.join(current, part)
            if not current.startswith("/"):
                current = "/" + current

            try:
                if not self.client.check(current):
                    self.client.mkdir(current)
            except Exception:
                # Some servers throw even if exists → double check
                if not self.client.check(current):
                    raise

    def upload(self, local_path: str, remote_path: str):
        """Upload file to InfiniCLOUD under /uploads (auto-create subfolders)."""
        try:
            # Normalize path
            remote_path = remote_path.strip()
            if not remote_path.startswith("/"):
                remote_path = "/" + remote_path

            # Always put uploads under /uploads, but keep subfolder structure
            if not remote_path.startswith("/uploads/"):
                remote_path = posixpath.join("/uploads", remote_path.lstrip("/"))

            parent = posixpath.dirname(remote_path)

            # Ensure parent folder exists
            self._ensure_folder(parent)

            # Perform upload
            self.client.upload_sync(remote_path=remote_path, local_path=local_path)
            return {"success": True, "message": f"Uploaded {local_path} → {remote_path}"}
        except Exception as e:
            return {"success": False, "message": f"Upload failed: {str(e)}"}


    def download(self, remote_path: str, local_path: str):
        """Download file from InfiniCLOUD."""
        try:
            self.client.download_sync(remote_path=remote_path, local_path=local_path)
            return {"success": True, "message": f"Downloaded {remote_path} → {local_path}"}
        except Exception as e:
            return {"success": False, "message": f"Download failed: {str(e)}"}

    def list_files(self, remote_path: str = "/uploads/"):
        """List files in a remote folder (defaults to /uploads)."""
        try:
            if not remote_path.startswith("/"):
                remote_path = "/" + remote_path
            files = self.client.list(remote_path)
            return {"success": True, "data": files}
        except Exception as e:
            return {"success": False, "message": f"Listing failed: {str(e)}"}
