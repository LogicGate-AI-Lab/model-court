# 贡献指南

感谢您对 Model Court 项目感兴趣！我们欢迎各种形式的贡献。

## 贡献方式

### 报告问题

如果您发现 bug 或有功能建议：

1. 在 GitHub Issues 中搜索，确认问题尚未被报告
2. 创建新 Issue，清楚描述问题或建议
3. 提供复现步骤（如果是 bug）

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "描述你的更改"`
4. 推送到分支：`git push origin feature/your-feature`
5. 创建 Pull Request

## 开发环境设置

### 安装依赖

```bash
# 克隆仓库
git clone <your-fork>
cd model-court

# 安装开发依赖
pip install -e .[dev,full]
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_court.py

# 生成覆盖率报告
pytest --cov=model_court --cov-report=html
```

### 代码格式化

```bash
# 格式化代码
black model_court/

# 排序 imports
isort model_court/

# 检查代码规范
flake8 model_court/

# 类型检查
mypy model_court/
```

## 代码规范

### Python 风格

- 遵循 PEP 8
- 使用类型提示
- 函数和类添加 docstrings
- 保持代码简洁清晰

### 提交信息

- 使用清晰的提交信息
- 第一行简短描述（50 字以内）
- 必要时添加详细说明

示例：
```
添加 Claude 3.5 支持

- 实现 AnthropicProvider
- 添加配置示例
- 更新文档
```

### 文档

- 新功能需要更新 API 文档
- 添加代码示例
- 保持文档与代码同步

## 贡献建议

### 新手友好的任务

- 修复文档中的错误
- 添加代码注释
- 改进错误信息
- 添加测试用例

### 进阶任务

- 添加新的 LLM Provider
- 实现新的 Reference 源
- 性能优化
- 添加新功能

## Pull Request 检查清单

提交 PR 前，请确认：

- [ ] 代码通过所有测试
- [ ] 添加了必要的测试
- [ ] 代码符合规范（black, isort, flake8）
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有不必要的文件变更

## 代码审查流程

1. 提交 Pull Request
2. CI 自动运行测试
3. 维护者审查代码
4. 根据反馈修改
5. 合并到主分支

## 许可证

通过贡献，您同意您的代码将在 MIT License 下发布。

## 联系方式

如有问题，请：
- 创建 GitHub Issue
- 在 Pull Request 中讨论

感谢您的贡献！

