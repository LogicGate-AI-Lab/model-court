# Contribution Guide \| 贡献指南

[English](#english) \| [中文](#中文)

---

## English

Thank you for your interest in **Model Court**!
This is a small project, and we welcome all kinds of contributions.

### How to Contribute

#### 1. Report Issues

- If you find a bug or have a suggestion, please open a GitHub Issue.
- Describe clearly what happened and how to reproduce it (if
  applicable).

#### 2. Submit Code

1. Fork the repo\
2. Create a new branch:`git checkout -b feature/your-feature`
3. Commit your changes:`git commit -m "Describe your change"`
4. Push the branch:`git push origin feature/your-feature`
5. Open a Pull Request

#### 3. Development Setup

```bash
git clone <your-fork>
cd model-court
pip install -e .[dev,full]
```

Run tests:

```bash
pytest
```

Format code:

```bash
black model_court/
isort model_court/
```

#### 4. Code Style

- Follow basic PEP 8 rules\
- Use type hints when possible\
- Keep code simple and readable

#### 5. Pull Request Checklist

- [ ] Tests pass\
- [ ] Code is formatted\
- [ ] Description is clear\
- [ ] No unnecessary file changes

---

## 中文

感谢你对 **Model Court** 的关注！
这是一个小项目，我们欢迎各种形式的贡献。

### 如何贡献

#### 1. 报告问题

- 如果你发现 bug 或有建议，请创建 GitHub Issue。
- 清楚描述问题和复现步骤（如适用）。

#### 2. 提交代码

1. Fork 仓库\
2. 创建新分支：`git checkout -b feature/your-feature`
3. 提交修改：`git commit -m "描述你的修改"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

#### 3. 开发环境

```bash
git clone <your-fork>
cd model-court
pip install -e .[dev,full]
```

运行测试：

```bash
pytest
```

格式化代码：

```bash
black model_court/
isort model_court/
```

#### 4. 代码规范

- 基本遵循 PEP 8\
- 尽量使用类型标注\
- 保持代码简单易读

#### 5. Pull Request 检查

- [ ] 测试通过\
- [ ] 代码已格式化\
- [ ] 描述清晰\
- [ ] 没有不必要的变更
