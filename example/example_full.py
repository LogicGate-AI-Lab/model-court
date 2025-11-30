# model court使用示例

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加父目录到 Python 路径（如果还没安装包）
sys.path.insert(0, str(Path(__file__).parent.parent))

# 可选: 使用 python-dotenv 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()  # 从 .env 文件加载环境变量
except ImportError:
    print("提示: 安装 python-dotenv 可自动加载 .env 文件: pip install python-dotenv")

# -----------------------------------------------------------------------------
# 0. 导入 Model Court 核心包
# -----------------------------------------------------------------------------
from model_court import Court, Prosecutor, Jury, Judge
from model_court.code import SqliteCourtCode
from model_court.references import (
    LocalRAGReference
)

# -----------------------------------------------------------------------------
# 1. 基础设施初始化 (Infrastructure)
# -----------------------------------------------------------------------------

# A. 初始化判例库 (混合检索：SQL + Vector)
"""
这里用户可以选择不同的预设判例库，暂时不支持用户自定义判例库
现在支持的判例库是包含vector查询，但是也可以直接看到的SQL数据库
也就是说用户可以直接看到SQL数据库的内容并修改，同时结果也会同步更新向量
在Prosecutor搜索的时候，会直接进行向量查询（因为大概率无法直接查到同样的结果）
--------
目前考虑设置的reference类别包括：
1、Google Search 需要API参数
2、Web Search 使用开源方案
3、RAG 知识库，需要初始化、建库，添加新词条需要embedding，其他程序也可以修改RAG从而实现多代理或搭配协作；默认使用ChromaDB
4、SimpleTextStorage 直接使用一个文本文档作为引用源，用户可以方便撰写text，text本身直接会被作为一个prompt提供给jury（现在LLM的上下文窗口非常大）
"""
court_db = SqliteCourtCode(
    db_path="./fact_check_history.db",
    default_validity_period=timedelta(days=30),
    enable_vector_search=True # 开启向量检索以查找相似判例
)

# B. 初始化参考资料 (Reference)

# 资料源 1: RAG 知识库
# 逻辑优化：检测到路径下有 DB 就加载，没有就根据 source_folder 初始化
rumor_rag = LocalRAGReference(
    # 用户可选OpenAI在线API，本地小模型MiniLM，本地大模型BGE-Large等。这个一定要设置成lazy loading，用的人在用的时候再下载。
    # 参数包括：MiniLM, BGE, OpenAI（如果选OpenAI，则还要填写API参数）
    collection_name="common_rumors",
    persist_directory="./rag_db_storage",  # 向量库存储位置
    source_folder="./rumor_txt_files",     # 原始文件位置（确保此文件夹存在）
    embedding_model="MiniLM",  # "MiniLM", "BGE", or "OpenAI"
    # embedding_api_key="..." # 如果选OpenAI的embedding方式，则需要选择这个
    mode="append", # "overwrite" | "append" | "read_only"
    top_k=2
)

# -----------------------------------------------------------------------------
# 2. 初始化检察官 (Prosecutor)
# -----------------------------------------------------------------------------

prosecutor = Prosecutor(
    court_code=court_db,

    # 启用自动拆分：将长文拆解为独立 Claim，如果不启用，则将整个case视为一个claim
    # 如果不拆分case为若干个claim，则不需要配置model
    # 如果要将case拆分为claims，并各自检查是否存在于code中，则需要配置model
    auto_claim_splitting=True, 
    
    # 使用 OpenRouter 调用 GPT-3.5
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "openai/gpt-3.5-turbo",
        "temperature": 0.1
    },
    prosecutor_prompt="你是一名严格的检察官。请将输入的案情（Case）拆解为独立的、可验证的事实断言（Claims）。"
)

# -----------------------------------------------------------------------------
# 3. 组建陪审团 (The Juries)
# -----------------------------------------------------------------------------

# 采用三明治结构构建LLM指令：用户只需要写jury针对claim类别的判断标准、objection的判定阈值
# 其他的系统PROMPT，包括输出格式、浏览器类别的cycle指令等，都在后端用system prompt写好（目前先硬编码system prompt，后续考虑加入用户自定义system prompt的功能）

# 提醒用户陪审员可能的输出选项："no_objection", "suspicious_fact", "reasonable_doubt"
# 如果写到输出结果相关的内容，用户一定要针对这三个输出选项进行适应性修改


# Jury 1: 逻辑审查员 (Blind) - 使用 GPT-4
jury_logic = Jury(
    name="Logic_Checker_GPT4",
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "openai/gpt-4",
        "temperature": 0.0
    },
    reference=None,  # None = Blind Mode，如果没有写参数reference，则默认为None
    jury_prompt="请仅根据逻辑一致性和常识判断此 Claim 是否成立，不要编造事实。"
)

# Jury 2: 网络侦探 (使用 Perplexity Sonar 联网搜索模型)
"""
Perplexity Sonar 模型自带联网搜索能力，无需额外的搜索 API
模型会自动从互联网获取最新信息并引用来源
"""
jury_web = Jury(
    name="Web_Detective_Perplexity",
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "perplexity/sonar",
        "temperature": 0.0
    },
    reference=None,  # 不需要外部 reference，模型自带联网搜索
    jury_prompt="""You are a research engine. You MUST perform a web search for every claim to provide the most current information. Do not answer from your internal training data. Always cite your sources.

请严格遵守输出规范，你的最终结论（decision）必须且只能是以下三个短语之一，严禁创造其他词汇：
1. "no_objection" (如果网络证据支持该说法)
2. "suspicious_fact" (如果证据不足或有冲突)
3. "reasonable_doubt" (如果网络证据直接反驳该说法)

你必须基于实时网络搜索的结果进行判断，并在理由中引用具体的网络来源。"""
)

# Jury 3: 档案管理员 (RAG) - 使用 Llama 3
jury_rag = Jury(
    name="Archive_Keeper_Llama",
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "meta-llama/llama-3-70b-instruct",
        "temperature": 0.2
    },
    reference=rumor_rag,
    jury_prompt="请在本地谣言库中检索是否存在匹配的记录。"
)

# -----------------------------------------------------------------------------
# 4. 组建法庭 (Court Assembly)
# -----------------------------------------------------------------------------

# 初始化法官，负责汇总近似判例和juries投票结果 - 使用 GPT-4
judge = Judge(
    # 法官模型配置
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "openai/gpt-4",
        "temperature": 0.2
    }
)

# Jury 4: 文本存储 (Basic Facts)
basic_facts_text = """
常见事实知识：
- 地球是圆的（球形）
- 水的化学式是 H2O
- 人类有 206 块骨骼（成年人）
- 光速约为 299,792,458 米/秒
- 地球绕太阳公转
- 疫苗通过激发免疫系统工作
- 酒精只能体外消毒，饮用无法杀死体内病毒
- 埃隆·马斯克未收购可口可乐公司
"""
from model_court.references import SimpleTextStorage
text_storage = SimpleTextStorage(text=basic_facts_text)

jury_facts = Jury(
    name="Facts_Checker_GPT35",
    model={
        "provider": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.getenv("OPENROUTER_API_KEY", "sk-or-v1-..."),
        "model_name": "openai/gpt-3.5-turbo",
        "temperature": 0.1
    },
    reference=text_storage,
    jury_prompt="""对照提供的基础事实知识，判断此 Claim 是否符合事实。
    你的最终结论（decision）必须且只能是以下三个之一：
    1. "no_objection"
    2. "suspicious_fact"
    3. "reasonable_doubt"
    """
)

# 最终实例化的model court对象，配置好court后，用户只需要调用Court对象并输入case content参数，就可以进行庭审了
fact_check_court = Court(
    prosecutor=prosecutor,
    juries=[jury_logic, jury_web, jury_rag, jury_facts],
    judge=judge,
    
    
    # 判决逻辑配置 (Rule-based Verdict)
    # 逻辑：统计 'objection' (即非 no_objection) 的票数比例
    verdict_rules={
        # 如果 0 个反对 -> Supported
        "supported":  {"operator": "eq", "value": 0},   
        # 如果反对票 < 50% (且不为0) -> Suspicious
        "suspicious": {"operator": "lt", "value": 0.5}, 
        # 其他情况 (>= 50%) -> Refuted (Default)
        "refuted":    "default" 
    },
    
    quorum=3,         # 必须3个都成功返回，否则流审 (或者设为2允许1个掉队)
    concurrency_limit=4
)
# 这里要注意court庭审每一个claim，都会将结果记录到code中

# -----------------------------------------------------------------------------
# 5. 开庭审理 (Execution - run_trial)
# -----------------------------------------------------------------------------

async def run_trial():
    # 1. 准备案情
    case_text = """
    有人发现了南极臭氧层的问题已经被解决。
    """
    
    print(f"🏛️  Model Court 开庭受理中...\nCase: {case_text.strip()[:30]}...")

    # 2. 执行审理 (Court.hear 内部自动调度 Prosecutor -> Juries -> Judge)
    # 返回的是一个结构化的 CaseReport 对象
    report = await fact_check_court.hear(case_text)

    # 3. 打印完整判决书
    print("\n" + "="*50)
    print(f"📜 判决意见书 (Case ID: {report.case_id})")
    print("="*50)

    # 遍历每个 Claim 的结果
    for idx, claim_res in enumerate(report.claims, 1):
        print(f"\n🔹 指控 {idx}: {claim_res.claim.text}")
        
        # A. 展示 Prosecutor 的查重结果
        if claim_res.claim.source == "cache":
            print(f"   [直接裁定] 命中历史有效判例 (ID: {claim_res.claim.cache_id})")
            print(f"   ⚖️  结果: {claim_res.verdict.upper()}")
            continue # 如果命中缓存，后面就不展示了
            
        # B. 展示 Prosecutor 的相似判例证据 (如果有)
        if claim_res.claim.precedents:
            print(f"   [历史判例] 发现 {len(claim_res.claim.precedents)} 条相似过往案件，已提交法官参考。")

        # C. 展示 Juries 投票详情
        print("   [陪审团投票]")
        for vote in claim_res.jury_votes:
            if vote.decision == "abstain":
                icon = "⚪"  # 缺席用空心圆表示
            elif vote.decision == "no_objection":
                icon = "✅"
            else:
                icon = "❌"
            # 如果是搜索模式，打印出找到的 Reference
            ref_info = f" (Ref: {vote.reference_summary})" if vote.reference_summary else ""
            print(f"     {icon} {vote.jury_name}: {vote.decision}{ref_info}")
            if vote.reason:
                print(f"        Reason: {vote.reason[:60]}...")

        # D. 展示最终判决
        print(f"   ⚖️  最终判决: 【{claim_res.verdict.upper()}】")
        print(f"   📝 法官综述: {claim_res.judge_reasoning}")

    # 4. 异常处理展示
    if report.status == "mistrial":
        print(f"\n⚠️ 审判无效 (Mistrial): {report.error_message}")

# 运行
if __name__ == "__main__":
    asyncio.run(run_trial())

