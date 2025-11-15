import requests
import subprocess
import json
import time
import webbrowser


class ConnectivityTest:
    def __init__(self):
        self.results = {}
        self.category_results = {}

    def test_http_endpoint(self, name, url):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            result = {
                "status": "success",
                "response_time_ms": response_time_ms,
                "status_code": response.status_code,
                "content_length": len(response.content),
                "json_structure": list(response.json().keys())
                if response.headers.get("Content-Type") == "application/json"
                else None,
            }
            self.results[name] = result
            print(
                f"{name}: ✅ 成功 (响应时间: {response_time_ms:.2f} ms, 状态码: {response.status_code})"
            )
            return result
        except Exception as e:
            result = {"status": "failure", "error": str(e)}
            self.results[name] = result
            print(f"{name}: ❌失败 ({str(e)})")
            return result

    def test_git_connectivity(self, name, url):
        try:
            start_time = time.time()
            result = subprocess.run(
                ["git", "ls-remote", url], capture_output=True, text=True, timeout=10
            )
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            branch_count = len(result.stdout.splitlines())
            if result.returncode == 0:
                self.results[name] = {
                    "status": "success",
                    "response_time_ms": response_time_ms,
                    "branch_count": branch_count,
                    "method": "git_command",
                }
                print(
                    f"{name}: ✅ 成功 (响应时间: {response_time_ms:.2f} ms, 分支数量: {branch_count})"
                )
                return self.results[name]
            else:
                self.results[name] = {"status": "failure", "error": result.stderr}
                print(f"{name}: ❌失败 ({result.stderr})")
                return self.results[name]
        except FileNotFoundError:
            # Git 命令未找到，使用 HTTP 兜底方案
            print(f"{name}: ⚠️ Git 未安装，使用 HTTP 兜底方案...")
            return self._test_git_connectivity_fallback(name, url)
        except Exception as e:
            self.results[name] = {"status": "failure", "error": str(e)}
            print(f"{name}: ❌失败 ({str(e)})")
            return self.results[name]

    def _test_git_connectivity_fallback(self, name, url):
        """当系统中找不到 git 时的兜底方案"""
        try:
            # 将 git URL 转换为对应的网页 URL
            web_url = self._convert_git_url_to_web(url)
            start_time = time.time()
            response = requests.get(web_url, timeout=10)
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                self.results[name] = {
                    "status": "success",
                    "response_time_ms": response_time_ms,
                    "branch_count": None,  # 无法通过 HTTP 获取分支数量
                    "method": "http_fallback",
                    "status_code": response.status_code,
                    "note": "使用 HTTP 兜底方案测试仓库可访问性"
                }
                print(
                    f"{name}: ✅ 成功 (HTTP兜底方案, 响应时间: {response_time_ms:.2f} ms, 状态码: {response.status_code})"
                )
                return self.results[name]
            else:
                self.results[name] = {
                    "status": "failure",
                    "error": f"HTTP状态码: {response.status_code}",
                    "method": "http_fallback"
                }
                print(f"{name}: ❌失败 (HTTP兜底方案, 状态码: {response.status_code})")
                return self.results[name]
        except Exception as e:
            self.results[name] = {
                "status": "failure",
                "error": str(e),
                "method": "http_fallback"
            }
            print(f"{name}: ❌失败 (HTTP兜底方案, {str(e)})")
            return self.results[name]

    def _convert_git_url_to_web(self, git_url):
        """将 git URL 转换为对应的网页 URL"""
        # 移除 .git 后缀
        web_url = git_url.replace('.git', '')
        
        # 处理常见的 Git 托管平台 URL 格式
        if 'github.com' in web_url:
            # GitHub: https://github.com/username/repo
            return web_url
        elif 'gitee.com' in web_url:
            # Gitee: https://gitee.com/username/repo
            return web_url
        elif 'gitlab.com' in web_url:
            # GitLab: https://gitlab.com/username/repo
            return web_url
        else:
            # 对于其他 Git 服务器，尝试直接访问
            return web_url

    def run_all_tests(self):
        print("开始连通性测试...")

        # 1. 测试PyPI镜像源
        print("1. 测试PyPI镜像源...")
        pypi_tests = []
        pypi_tests.append(self.test_http_endpoint("默认PyPI源", "https://pypi.org/pypi/requests/json"))
        pypi_tests.append(self.test_http_endpoint(
            "清华大学PyPI镜像源", "https://pypi.tuna.tsinghua.edu.cn/pypi/requests/json"
        ))
        pypi_tests.append(self.test_http_endpoint(
            "阿里云PyPI镜像源", "https://mirrors.aliyun.com/pypi/simple/requests/"
        ))
        self._update_category_status("PyPI镜像源", pypi_tests)

        # 2. 测试米哈游API
        print("2. 测试米哈游API...")
        mihoyo_tests = []
        mihoyo_tests.append(self.test_http_endpoint(
            "米哈游游戏信息API",
            "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGames?launcher_id=jGHBHlcOq1&language=zh-cn",
        ))
        mihoyo_tests.append(self.test_http_endpoint(
            "米哈游基础信息API",
            "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getAllGameBasicInfo?launcher_id=jGHBHlcOq1&language=zh-cn",
        ))
        self._update_category_status("米哈游API", mihoyo_tests)

        # 3. 测试Git仓库
        print("3. 测试Git仓库连通性...")
        git_tests = []
        github_result = self.test_git_connectivity(
            "GitHub仓库",
            "https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon.git",
        )
        git_tests.append(github_result)

        gitee_result = self.test_git_connectivity(
            "Gitee仓库",
            "https://gitee.com/OneDragon-Anything/ZenlessZoneZero-OneDragon.git",
        )
        git_tests.append(gitee_result)
        self._update_category_status("Git仓库", git_tests)

        # 4. 测试公告系统
        print("4. 测试公告系统...")
        notice_tests = []
        notice_tests.append(self.test_http_endpoint(
            "公告通知URL", "https://one-dragon.com/notice/zzz/notice.json"
        ))
        self._update_category_status("公告系统", notice_tests)

        # 5. 测试文档链接
        print("5. 测试文档链接...")
        doc_tests = []
        doc_tests.append(self.test_http_endpoint(
            "快速开始文档", "http://one-dragon.com/zzz/zh/quickstart.html"
        ))
        doc_tests.append(self.test_http_endpoint("项目主页", "https://one-dragon.com/zzz/zh/home.html"))
        doc_tests.append(self.test_http_endpoint(
            "腾讯文档",
            "https://docs.qq.com/doc/p/7add96a4600d363b75d2df83bb2635a7c6a969b5",
        ))
        self._update_category_status("文档链接", doc_tests)

        # 6. 测试ghproxy链接
        print("6. 测试ghproxy链接...")
        ghproxy_tests = []
        ghproxy_tests.append(self.test_http_endpoint(
            "ghproxy链接", "https://ghproxy.link/js/src_views_home_HomeView_vue.js"
        ))
        self._update_category_status("ghproxy链接", ghproxy_tests)

        # 输出大类状态汇总
        self._print_category_summary()

        return self.results

    def save_results(self, results):
        with open("connectivity_test_report.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def _update_category_status(self, category_name, test_results):
        """更新大类状态，只要有一个小类通过，整个大类就通过"""
        category_passed = False
        for result in test_results:
            if result and result.get("status") == "success":
                category_passed = True
                break
        
        self.category_results[category_name] = {
            "status": "success" if category_passed else "failure",
            "passed_tests": sum(1 for r in test_results if r and r.get("status") == "success"),
            "total_tests": len(test_results)
        }

    def _print_category_summary(self):
        """输出大类状态汇总"""
        print("\n" + "="*50)
        print("大类测试状态汇总")
        print("="*50)
        
        for category, result in self.category_results.items():
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(f"{status_icon} {category}: {result['passed_tests']}/{result['total_tests']} 个测试通过")
        
        print("="*50)

    def check_results(self):
        """检查所有大类是否都至少有一个测试通过"""
        all_categories_passed = True
        for category, result in self.category_results.items():
            if result["status"] == "failure":
                all_categories_passed = False
                break
        return all_categories_passed


if __name__ == "__main__":
    tester = ConnectivityTest()
    results = tester.run_all_tests()
    tester.save_results(results)

    # 添加命令行输出
    print("\n连通性测试已完成。结果已保存到 connectivity_test_report.json")

    # 检查测试结果
    if tester.check_results():
        print("所有测试通过。您可以继续 安装/使用")
    else:
        print("某些测试失败，请检查您的网络环境。")

    # 暂停命令行窗口
    input("按 Enter 键退出...")

    # 打开网页
    webbrowser.open("https://pd.qq.com/g/onedrag00n")
