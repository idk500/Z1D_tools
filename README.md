# Z1D_tools

此项目用于一条龙相关工具或其他REPO收集


## Index

- env
  - 本地环境/依赖 相关
- network
  - 网络相关
 
## CI / 自动构建 (Windows .exe)

本仓库已添加 GitHub Actions 工作流，用于在 Windows runner 上自动构建 `network/connectivity_test.py` 的可执行文件（.exe），并把构建产物同时作为 workflow artifact 和 GitHub Release 资产上传。

主要文件
- `.github/workflows/build-windows.yml` — CI 工作流：checkout → setup Python → 安装依赖（`network/requirements.txt`）→ 安装 UPX → 使用 PyInstaller（`network/connectivity_test.spec`）打包 → 上传 artifact → 创建 Release 并上传 exe 资产。
- `network/requirements.txt` — 运行脚本的 Python 依赖（当前包含 `requests`）。

触发方式
- push 到 `main`、对 `main` 的 PR 或手动在 Actions 页面触发（workflow_dispatch）。

产物
- Actions 页面中的 Artifacts（名称：`connectivity_test-windows`），包含 `connectivity_test.exe`。
- 自动创建的 GitHub Release，资产名为 `connectivity_test.exe`。

注意事项
- UPX 已在 CI 中通过 choco 安装并用于 PyInstaller 的压缩（提高可执行文件压缩率）。
- `connectivity_test.spec` 引用了 `1D_logo.png` / `1D_logo.ico` 等资源；请确保这些资源在构建时可访问（位于 `network/` 或更新 spec 中的相对路径），否则生成的 exe 可能缺少图标或资源。
- Release tag 名称采用 CI 运行号（示例：`v123-456789`）。如果你需要基于语义化版本的 tag（例如 `v1.2.3`）发布，请在 push 时用带 tag 的提交或告诉我要改为仅在带 tag 的 push 时发布。

手动操作（在本地准备 PR）
1. 创建分支并推送：

```powershell
git checkout -b ci/add-windows-build-workflow
git add .
git commit -m "ci: add Windows build workflow and README docs"
git push -u origin ci/add-windows-build-workflow
```

2. 在 GitHub 上创建 PR（网页操作）或使用 `gh`：

```powershell
gh pr create --fill --base main --head ci/add-windows-build-workflow
```

如果你希望我代为创建 PR（自动打开 GitHub PR），请确认你的环境已配置 `git` 远程权限或允许我生成推送的命令并由你执行（我可以尝试推送，但可能需要你的凭据/权限）。

如需我把资源文件自动移动到 `network/` 或更新 spec 的 datas 路径，我可以直接修改并提交到同一分支。
