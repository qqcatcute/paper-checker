# 测试与代码质量报告

## 实测结果

环境：macOS 26.5.2、arm64、Python 3.9.6。核心优化后执行了 52 项 `unittest` 测试，全部通过。另有 150 组种子固定的随机文本性质检查，以及 100 组优化前后数学等价性检查，均包含在上述测试中。

真实命令行测试从另一个工作目录启动 `main.py`，传入包含中文和空格的绝对路径，验证退出码、标准输出/错误和答案内容。该路径实际运行成功。

| 运行时代码 | 可执行语句 | 未覆盖语句 | 分支 | 未覆盖分支 | 覆盖率 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `checker/errors.py` | 4 | 0 | 0 | 0 | 100% |
| `checker/fileio.py` | 33 | 0 | 10 | 0 | 100% |
| `checker/similarity.py` | 32 | 0 | 10 | 0 | 100% |
| `main.py` | 24 | 0 | 6 | 0 | 100% |
| 合计 | 93 | 0 | 26 | 0 | 100% |

覆盖率范围是提交程序的 `checker` 包和 `main.py`，不包括测试自身及开发用性能脚本。没有为了提高数值而排除程序的可执行分支。单元测试之后追加运行真实入口，覆盖 `__main__` 启动路径。

![Coverage.py 实际生成的覆盖率报告](../reports/images/coverage.png)

高覆盖率说明这些分支被执行过，不等于老师的隐藏测试一定通过，也不代表算法经过真实论文语料准确率评估。

## 用例设计

| 类别 | 示例 | 设计依据 |
| --- | --- | --- |
| 标准化 | 全角 ABC、大小写、标点、组合重音字符 | 等价类划分 |
| 基本功能 | 完全相同、完全不同、增补、删除、次序变化 | 正常与替代路径 |
| 可手算结果 | `abc` 对 `abd` 应为 0.55 | 独立数学预期 |
| 边界 | 双空、单空、纯标点、单字符、零向量 | 条件与分支覆盖 |
| 文件接口 | UTF-8 BOM、覆盖旧答案、输入相同、两位小数 | 文件协议约束 |
| 输入保护 | 输出同名、符号链接、硬链接 | 危险别名路径 |
| 异常处理 | 文件缺失、编码错误、读写权限失败、输出目录缺失 | 错误分支与状态保持 |
| 命令行 | 参数数量、帮助、其他目录启动、中文和空格路径 | 端到端调用 |
| 数学性质 | 对称性、0～1 边界、稀疏与稠密公式相等 | 固定随机种子的性质检查 |
| 长输入 | 10 万字符重复文本与独立百万字压力测试 | 资源和复杂度检查 |

## 部分测试代码

该用例的预期值来自手算，不是将程序输出复制回测试：

```python
def test_hand_calculated_weighted_score(self):
    # 单字符余弦 2/3，双字符余弦 1/2，最终 0.3*(2/3)+0.7*(1/2)=0.55。
    self.assertAlmostEqual(similarity("abc", "abd"), 0.55)
```

异常测试还验证失败时不破坏已有结果：

```python
def test_invalid_utf8_does_not_replace_previous_answer(self):
    self.candidate.write_bytes(b"\xff\xfe\x00\x00")
    self.output.write_text("previous", encoding="utf-8")
    with self.assertRaises(TextReadError):
        self.compare()
    self.assertEqual(self.output.read_text(), "previous")
```

## 异常设计与对应测试

| 异常/状态 | 设计目标 | 对应用例 |
| --- | --- | --- |
| `InvalidPathError` | 强制绝对路径并阻止答案覆盖输入 | `test_relative_path_rejected`、`test_hardlink_output_cannot_overwrite_input` |
| `TextReadError` | 说明输入不存在、不是文件、编码无效或没有读取权限 | `test_missing_original`、`test_invalid_utf8_does_not_replace_previous_answer`、`test_read_permission_failure_is_explained` |
| `ResultWriteError` | 说明答案路径不可写或父目录缺失 | `test_output_parent_must_exist`、`test_write_permission_failure_is_explained` |
| 参数数量错误（退出码 2） | 拒绝不符合三个参数约定的调用 | `test_wrong_argument_counts` |

## 代码质量

Ruff 0.16.7 的 `E/F/I/B/UP` 规则检查通过，格式检查通过。规则涉及基础语法/风格问题、未使用变量/导入、导入顺序、常见缺陷和适合 Python 3.9 的写法。测试工具版本详见 `requirements-dev.txt`。

原始日志：[测试输出](../reports/tests.txt)、[覆盖率文本](../reports/coverage-summary.txt)、[覆盖率 JSON](../reports/coverage.json)、[代码检查](../reports/quality.txt)。

## 尚未验证

- 老师下发的样例和 18 个隐藏测试点。
- Windows 实机运行；当前只在本机 macOS 验证。
- 基于真实标注论文数据的准确率、召回率和阈值。
