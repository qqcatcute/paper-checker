GitHub 作业链接：[paper-checker / 3224004157](https://github.com/qqcatcute/paper-checker/tree/main/3224004157)

# 第一次个人编程作业

学号：3224004157。课程作业：[个人项目——论文查重](https://edu.cnblogs.com/campus/gdgy/Class56-Grade2024-CS/homework/15693)。

## 一、项目目标与开发准备

本项目实现一个 Python 命令行程序，接收原文、待比较文本和答案文件三个绝对路径，在答案文件中写入保留两位小数的重复率。入口文件为 `main.py`，运行时只使用标准库。

开发前先记录 PSP 预估，随后按基本功能、性能测量、优化和报告整理分别提交。初版开发时尚未连接远端仓库，提交先保存在本地。

目前使用自建文本进行测试，拿到班级群样例后再补充验证。

## 二、计算模块的设计与实现

程序由命令行入口、文件读写层、相似度计算层和异常类组成：

| 接口 | 作用 |
| --- | --- |
| `main(argv)` | 检查三个参数，处理帮助和错误退出 |
| `compare_files(original, candidate, output)` | 检查路径、保护输入、读写指定文件 |
| `normalize_text(text)` | 统一全角/大小写、过滤空白与标点 |
| `cosine_similarity(left, right)` | 计算两个频数向量的余弦相似度 |
| `similarity(left, right)` | 提取单字符/双字符特征并加权 |

核心流程为：路径校验 → UTF-8 读取 → 文本标准化 → 字符片段频数统计 → 余弦计算 → 写入两位小数。

接口之间的调用关系如下：

```text
main(argv)
  └─ compare_files(original, candidate, output)
       ├─ _validate_paths(...)：检查绝对路径和输入保护
       ├─ _read_text(...)：分别读取两份 UTF-8 文本
       ├─ similarity(left, right)
       │    ├─ normalize_text(...)：清洗两份文本
       │    └─ cosine_similarity(...)：计算单字符项和双字符项
       └─ output.write_text(...)：写入两位小数
```

`CheckerError` 是程序预期异常的公共父类，下面区分路径错误、读取错误和写入错误；命令行入口统一捕获并显示错误。计算函数不直接访问文件，因此可以在不准备真实文件的情况下单独测试数学结果。路径检查和文件操作则使用临时文件测试。

相邻双字符特征能保留部分局部语序。例如“论文查重”分成“论文”“文查”“查重”。分别计算单字符和双字符余弦相似度，再使用 `0.3 × 单字符余弦 + 0.7 × 双字符余弦` 得到 0～1 的得分。

任一文本清洗后为空时返回 0；只有一个字符时采用单字符项。权重是本项目公开的设计选择，并未经过教师样例调参。该方法不依赖中文分词词典，运行时不联网，特征提取的时间随输入长度线性增长。

这种方法主要比较文字和局部语序，对同义改写的识别能力有限；频数分布相近的文章也可能得到较高分数。

## 三、性能瓶颈与改进

阶段记录中，性能测量与代码改进占用 2026-09-11 17:00:31 至 17:03:19，约 **2.81 分钟**；随后回归、覆盖率和长输入验证约 **1.97 分钟**。这是助手参与开发过程的计时，原始记录见 [阶段计时](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/development-timing.json)，不等于个人学习和操作时间，也不重复计入 PSP 总数。

初版为余弦计算建立特征并集和两个补零列表。cProfile 显示该函数两次调用累计约 0.08593 秒，字典查找调用达到 289,632 次。

优化后，点积只遍历较小的频数字典，范数分别遍历已有频数，消除额外并集和稠密列表。公式保持不变。

在相同种子的 120,000 与 126,000 字符自建中文输入上：

| 指标 | 初版 | 优化后 |
| --- | ---: | ---: |
| 核心计算中位耗时（5 次） | 0.103169 秒 | 0.062176 秒 |
| Python 分配峰值 | 48.49 MiB | 28.49 MiB |
| 含进程启动/文件读写的命令行中位耗时 | 0.135066 秒 | 0.092911 秒 |
| 得分 | 0.875756509005383 | 0.875756509005383 |

下列函数图来自初版和优化版实际运行产生的 cProfile 文件，由 SnakeViz 展示。此次截图重新打开已保存的报告，没有重新生成或改写测量数值。

优化前的函数调用图与耗时排名：

![优化前函数调用图](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/images/02-performance-before.jpg?raw=true)

![优化前函数耗时排名](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/images/03-functions-before.jpg?raw=true)

优化后的函数调用图与耗时排名：

![优化后函数调用图](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/images/04-performance-after.jpg?raw=true)

![优化后函数耗时排名](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/images/05-functions-after.jpg?raw=true)

图中的 `tottime` 是函数自身耗时，`cumtime` 包含子函数调用时间；排名按 `tottime` 降序展示。

优化后，余弦计算累计约 0.02593 秒；自耗时最大的函数变成频数统计使用的 `_collections._count_elements`，约 0.02214 秒。图上的追踪耗时包含分析工具开销，与未开启分析工具的计时分开统计。

另一组原文 100 万字符、待比较文本 105 万字符的实际命令行检查耗时约 0.764 秒，最大常驻内存约 300 MiB。该结果只代表这台电脑和这组自建输入，不代表老师的隐藏测试。

页面对性能图工具的表述需要确认：这里使用的是 Python cProfile/SnakeViz，尚未确认是否可以替代 VS 2017/JProfiler。

## 四、单元测试与覆盖率

优化后执行 52 项测试全部通过，覆盖正常输入、边界条件、异常分支和真实命令行调用。固定随机种子的额外检查验证相似度对称性、范围和优化前后公式等价性。

测试首先按代码中的条件分支进行白盒设计，再补充等价类、边界值和文件接口测试：

| 被测函数/分支 | 构造数据的方法 | 检查目标 |
| --- | --- | --- |
| `normalize_text` | 全角字母、大小写、纯标点、组合重音 | 字符标准化、保留与过滤分支 |
| `similarity` 空文本分支 | 双空、原文空、候选空、清洗后为空 | 返回 0，不把无有效内容当作重复 |
| `similarity` 相同文本分支 | 完全相同或仅有排版差异 | 清洗后相同返回 1 |
| `similarity` 单字符分支 | “甲”与“甲乙” | 采用单字符余弦，避免不存在的双字符项 |
| `cosine_similarity` | 零向量、交集为空、两边特征数量不同 | 分母保护和遍历较小字典的分支 |
| `compare_files` | 临时 UTF-8/BOM 文件、输入输出路径别名 | 两位小数、错误分类、输入保护 |
| `main` | 参数过少/过多、帮助参数、正常绝对路径 | 成功、参数错误和文件错误退出码 |

这些数据覆盖了正常和异常控制路径。150 组随机文本检查对称性与数值范围，100 组随机频数向量与独立稠密公式比较，补充验证优化未改变数学结果。它们仍不能代替老师的 18 个隐藏测试点或真实论文语料的准确率评估。

一个可以手算预期值的例子：`abc` 与 `abd` 的单字符余弦为 2/3，双字符余弦为 1/2，所以加权结果为 0.55：

```python
def test_hand_calculated_weighted_score(self):
    self.assertAlmostEqual(similarity("abc", "abd"), 0.55)
```

程序运行时代码共 93 条可执行语句、26 个分支，行与分支覆盖率均为 100%。覆盖范围不包括测试自身和开发工具，覆盖率也不能代替算法准确性评估。

![测试覆盖率](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/images/01-coverage.jpg?raw=true)

Ruff 代码规则检查和格式检查通过。原始输出：[测试日志](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/tests.txt)、[覆盖率摘要](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/coverage-summary.txt)、[代码质量检查](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/reports/quality.txt)。

## 五、异常处理

| 异常 | 设计目标 | 一个对应测试 |
| --- | --- | --- |
| `InvalidPathError` | 拒绝相对路径，阻止答案覆盖输入 | `test_answer_cannot_overwrite_original` |
| `TextReadError` | 清晰说明文件缺失、无效 UTF-8 或读取失败 | `test_invalid_utf8_does_not_replace_previous_answer` |
| `ResultWriteError` | 说明输出父目录不存在或没有写入权限 | `test_output_parent_must_exist` |

以下三个示例均来自 [文件接口测试](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/tests/test_fileio.py)。测试的 `setUp` 会在临时文件夹写入原文 `abc`、待比较文本 `abd`，预期正常结果为 `0.55`；`self.compare()` 调用三个临时文件路径对应的 `compare_files`。

### 路径错误：答案路径与原文相同

`InvalidPathError` 用于拒绝不合规路径和危险的输入输出别名。此例将原文同时作为答案路径，必须报错并保留原文内容。

```python
def test_answer_cannot_overwrite_original(self):
    with self.assertRaises(InvalidPathError):
        compare_files(self.original, self.candidate, self.original)
    self.assertEqual(self.original.read_text(), "abc")
```

### 读取错误：待比较文件不是 UTF-8

`TextReadError` 将文件缺失、读取权限问题和无效编码转换为明确的输入错误。此例构造非法 UTF-8 字节，并验证错误发生后旧答案仍然保留。

```python
def test_invalid_utf8_does_not_replace_previous_answer(self):
    self.candidate.write_bytes(b"\xff\xfe\x00\x00")
    self.output.write_text("previous", encoding="utf-8")
    with self.assertRaises(TextReadError):
        self.compare()
    self.assertEqual(self.output.read_text(), "previous")
```

### 写入错误：答案的父文件夹不存在

`ResultWriteError` 用于报告答案文件不能写入的场景。程序只使用指定的输出路径，不自动猜测其他位置；此例验证父文件夹缺失时给出该异常。

```python
def test_output_parent_must_exist(self):
    with self.assertRaises(ResultWriteError):
        compare_files(self.original, self.candidate, self.root / "missing" / "out.txt")
```

上述三类异常均由命令行入口捕获并返回退出码 1，具体原因写入标准错误；参数数量不正确时返回 2。

## 六、PSP 与过程记录

首次编码前的预估保存在 [原始 PSP 记录](https://github.com/qqcatcute/paper-checker/blob/main/3224004157/docs/PSP.md)。

### 本轮个人复现与完善记录

下表记录本轮个人复现与完善：预估合计 200 分钟，实际耗时由本人填报，合计 210 分钟。该计划不替代首次编码前已经保存的预估，个人填报用时与工具辅助开发阶段的计时分别记录。

| PSP2.1 | 计划工作 | 预估耗时（分钟） | 实际耗时（分钟） |
| --- | --- | ---: | ---: |
| Planning / Estimate | 确定本轮复现目标和时间安排 | 10 | 15 |
| Development / Analysis | 阅读要求，理解输入输出、余弦相似度和算法限制 | 25 | 30 |
| Development / Design Spec | 对照代码梳理模块职责和数据流 | 15 | 20 |
| Development / Design Review | 检查空文本、单字符、异常路径等设计 | 10 | 5 |
| Development / Coding Standard | 熟悉命名、注释和 Ruff 检查规则 | 5 | 5 |
| Development / Design | 设计补充样例或有实际需要的改进 | 20 | 25 |
| Development / Coding | 根据本轮发现的问题完善代码或测试 | 50 | 40 |
| Development / Code Review | 检查自己的改动及其影响 | 15 | 10 |
| Development / Test | 运行测试、演示与性能分析，核对结果 | 25 | 20 |
| Reporting / Test Report | 根据实际复现结果完善博文和截图 | 10 | 15 |
| Reporting / Size Measurement | 统计本轮实际修改的内容和工作量 | 5 | 10 |
| Reporting / Postmortem | 写下实际理解、问题及改进计划 | 10 | 15 |
| 合计 | | **200** | **210** |

## 七、功能划分与提交记录

| 阶段 | 内容 | 提交 |
| --- | --- | --- |
| 编码前计划 | PSP 预估和实现计划 | [5fea1fa](https://github.com/qqcatcute/paper-checker/commit/5fea1fa) |
| 基本功能 | 文件接口、字符片段相似度、异常处理和初版测试 | [15d1de1](https://github.com/qqcatcute/paper-checker/commit/15d1de1) |
| 基线测量 | 保存初版性能数据与测量脚本 | [a9af0f9](https://github.com/qqcatcute/paper-checker/commit/a9af0f9) |
| 性能改进 | 稀疏余弦计算、回归验证、长输入和覆盖率检查 | [bf9e75a](https://github.com/qqcatcute/paper-checker/commit/bf9e75a) |
| 报告整理 | 测试、性能截图和说明材料 | [6119278](https://github.com/qqcatcute/paper-checker/commit/6119278) |

这些阶段在本地按顺序提交；由于仓库与认证稍后完成，远端于 2026-09-11 晚间统一接收。本地 commit 和远端上传的时间分别保留。后续实质改动将在验证后及时提交并同步。

## 八、总结与后续工作

将文件读写、异常处理和相似度计算拆开后，可以分别验证每一部分。性能分析也发现了多余的中间列表，优化时只需调整余弦计算，不影响文件接口。后续需要补测老师的样例，并确认 Python 性能图的提交要求。

个人复盘（本人实际阅读、运行或修改了什么，理解了哪些原理，遇到的问题如何解决）：**待本人补充。**


## 参考资料

- [课程作业要求](https://edu.cnblogs.com/campus/gdgy/Class56-Grade2024-CS/homework/15693)
- [Python 性能分析器 cProfile](https://docs.python.org/3/library/profile.html)
- [Coverage.py 7.10.7](https://coverage.readthedocs.io/en/7.10.7/)
- [SnakeViz 文档](https://jiffyclub.github.io/snakeviz/)
- [Ruff 文档](https://docs.astral.sh/ruff/)
