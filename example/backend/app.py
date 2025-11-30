"""
Model Court Web API Backend

这是一个简单的 Flask API，提供 Model Court 的 Web 接口。
用于事实核查：判断输入文本中是否包含不符合事实的内容。
"""

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 可选: 使用 python-dotenv 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    # 加载 example 目录下的 .env 文件
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded .env from: {env_path}")
except ImportError:
    print("⚠️  提示: 安装 python-dotenv 可自动加载 .env 文件: pip install python-dotenv")

# 添加父目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from model_court import Court, Prosecutor, Jury, Judge, SqliteCourtCode
from model_court.references import LocalRAGReference, SimpleTextStorage

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# 全局变量存储 Court 实例
court_instance = None
initialization_error = None

def initialize_court():
    """初始化 Court 实例"""
    global court_instance, initialization_error
    
    try:
        # 设置路径
        base_path = Path(__file__).parent
        db_path = base_path / "court_history.db"
        rag_path = base_path.parent / "data" / "rag_storage"
        rag_docs = base_path.parent / "data" / "rag_documents"
        
        # 1. 初始化 Court Code
        print("Initializing Court Code...")
        court_code = SqliteCourtCode(
            db_path=str(db_path),
            embedding_model="MiniLM",
            default_validity_period=timedelta(days=30),
            enable_vector_search=True
        )
        
        # 2. 初始化 Prosecutor（启用自动拆分）
        print("Initializing Prosecutor...")
        prosecutor = Prosecutor(
            court_code=court_code,
            auto_claim_splitting=True,  # 启用自动拆分
            model={
                "provider": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                "model_name": "openai/gpt-3.5-turbo",
                "temperature": 0.1
            },
            prosecutor_prompt="你是一名严格的检察官。请将输入的案情（Case）拆解为独立的、可验证的事实断言（Claims）。"
        )
        
        # 3. 初始化 Reference 源
        print("Initializing References...")
        
        # RAG 知识库
        try:
            rag_reference = LocalRAGReference(
                collection_name="fact_check_knowledge",
                persist_directory=str(rag_path),
                embedding_model="MiniLM",
                source_folder=str(rag_docs) if rag_docs.exists() else None,
                mode="append",
                top_k=3
            )
        except Exception as e:
            print(f"Warning: RAG initialization failed: {e}")
            rag_reference = None
        
        # 简单文本存储（基础事实）
        # 从文件读取基础事实知识
        basic_facts_file = base_path.parent / "data" / "rag_documents" / "basic_facts.txt"
        if basic_facts_file.exists():
            with open(basic_facts_file, "r", encoding="utf-8") as f:
                basic_facts_text = f.read()
            text_reference = SimpleTextStorage(text=basic_facts_text)
            print(f"✅ Loaded basic facts from: {basic_facts_file}")
        else:
            print(f"⚠️  Warning: basic_facts.txt not found at {basic_facts_file}")
            text_reference = SimpleTextStorage(text="基础事实知识文件未找到。")

        
        # 4. 初始化 Juries
        print("Initializing Juries...")
        juries = []
        
        # 获取 OpenRouter API Key（从环境变量）
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        
        # 使用 OpenRouter 统一配置所有模型
        if not openrouter_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found. Please set it in environment variables or .env file."
            )
        
        # Jury 1: GPT-4 (Blind - 仅基于逻辑)
        juries.append(Jury(
            name="Logic_Checker_GPT4",
            model={
                "provider": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "model_name": "openai/gpt-4",
                "api_key": openrouter_key,
                "temperature": 0.0
            },
            reference=None,  # Blind mode
            jury_prompt="请仅根据逻辑一致性和常识判断此 Claim 是否成立，不要编造事实。"
        ))
        
        # Jury 2: Perplexity with Online Search (自带联网搜索能力)
        juries.append(Jury(
            name="Web_Detective_Perplexity",
            model={
                "provider": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "model_name": "perplexity/sonar",
                "api_key": openrouter_key,
                "temperature": 0.0
            },
            reference=None,  # 不需要外部 reference，模型自带联网搜索
            jury_prompt="""You are a research engine. You MUST perform a web search for every claim to provide the most current information. Do not answer from your internal training data. Always cite your sources.

Please strictly adhere to the output guidelines. Your final decision must and can only be one of the following three phrases; creating other words is strictly prohibited:

1. "no_objection" (if online evidence supports the statement)

2. "suspicious_fact" (if the evidence is insufficient or conflicting)

3. "reasonable_doubt" (if online evidence directly refutes the statement)

You must base your judgment on the results of real-time online searches and cite specific online sources in your reasoning."""
        ))
        
        # Jury 3: Llama with RAG
        if rag_reference:
            juries.append(Jury(
                name="Archive_Keeper_Llama",
                model={
                    "provider": "openai_compatible",
                    "base_url": "https://openrouter.ai/api/v1",
                    "model_name": "meta-llama/llama-3-70b-instruct",
                    "api_key": openrouter_key,
                    "temperature": 0.2
                },
                reference=rag_reference,
                jury_prompt="请在本地谣言库中检索是否存在匹配的记录。"
            ))
        
        # Jury 4: GPT-3.5 with Basic Facts
        juries.append(Jury(
            name="Facts_Checker_GPT35",
            model={
                "provider": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "model_name": "openai/gpt-3.5-turbo",
                "api_key": openrouter_key,
                "temperature": 0.1
            },
            reference=text_reference,
            jury_prompt="""对照提供的基础事实知识，判断此 Claim 是否符合事实。
            你的最终结论（decision）必须且只能是以下三个之一：
            1. "no_objection"
            2. "suspicious_fact"
            3. "reasonable_doubt"
            """
        ))
        
        # 5. 初始化 Judge
        print("Initializing Judge...")
        judge = Judge(
            model={
                "provider": "openai_compatible",
                "base_url": "https://openrouter.ai/api/v1",
                "model_name": "openai/gpt-4",
                "api_key": openrouter_key,
                "temperature": 0.2
            },
            verdict_rules={
                "supported": {"operator": "eq", "value": 0},      # 0个反对 -> Supported
                "suspicious": {"operator": "lt", "value": 0.5},  # < 50%反对 -> Suspicious
                "refuted": "default"  # >= 50% -> Refuted
            }
        )
        
        # 6. 组装 Court
        print("Assembling Court...")
        court_instance = Court(
            prosecutor=prosecutor,
            juries=juries,
            judge=judge,
            quorum=min(3, len(juries)),  # 至少需要 3 个 jury 投票
            concurrency_limit=3
        )
        
        print(f"✅ Court initialized successfully with {len(juries)} juries!")
        return True
        
    except Exception as e:
        initialization_error = str(e)
        print(f"❌ Court initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/status', methods=['GET'])
def status():
    """检查 API 状态"""
    return jsonify({
        "status": "ready" if court_instance else "error",
        "error": initialization_error,
        "juries_count": len(court_instance.juries) if court_instance else 0
    })


@app.route('/api/check', methods=['POST'])
def check_facts():
    """
    检查输入文本的事实准确性
    
    请求体：
    {
        "text": "要检查的文本内容"
    }
    """
    if not court_instance:
        return jsonify({
            "error": "Court not initialized",
            "details": initialization_error
        }), 500
    
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # 运行 Court 审理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        report = loop.run_until_complete(
            court_instance.hear(text, domain="fact_check")
        )
        loop.close()
        
        # 提取结果
        result = {
            "case_id": report.case_id,
            "status": report.status,
            "claims": []
        }
        
        for claim_result in report.claims:
            claim_data = {
                "text": claim_result.claim.text,
                "verdict": claim_result.verdict,
                "judge_reasoning": claim_result.judge_reasoning,
                "jury_votes": [
                    {
                        "jury_name": vote.jury_name,
                        "decision": vote.decision,
                        "confidence": vote.confidence,
                        "reason": vote.reason,
                        "reference_summary": vote.reference_summary if hasattr(vote, 'reference_summary') else None
                    }
                    for vote in claim_result.jury_votes
                ],
                "objection_ratio": claim_result.objection_ratio,
                "from_cache": claim_result.claim.source == "cache",
                "cache_id": claim_result.claim.cache_id if claim_result.claim.source == "cache" else None,
                "precedents": [
                    {
                        "id": p.precedent_id,
                        "text": p.claim,
                        "verdict": p.verdict,
                        "similarity": p.similarity_score
                    }
                    for p in (claim_result.claim.precedents or [])
                ] if hasattr(claim_result.claim, 'precedents') else []
            }
            result["claims"].append(claim_data)
        
        # 生成总体评估
        verdicts = [c.verdict for c in report.claims]
        if all(v == "supported" for v in verdicts):
            result["overall"] = "supported"
            result["summary"] = "✅ 内容得到支持，未发现虚假信息。"
        elif any(v == "refuted" for v in verdicts):
            result["overall"] = "refuted"
            result["summary"] = "❌ 内容包含虚假或不准确的信息。"
        else:
            result["overall"] = "suspicious"
            result["summary"] = "⚠️ 部分内容存疑，需要进一步核实。"
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Processing failed",
            "details": str(e)
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史记录"""
    if not court_instance:
        return jsonify({"error": "Court not initialized"}), 500
    
    try:
        # 这里可以实现从数据库读取历史记录的逻辑
        # 简化版暂时返回空
        return jsonify({
            "history": [],
            "message": "History feature coming soon"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """主函数"""
    print("=" * 70)
    print("Model Court Web API")
    print("=" * 70)
    
    # 初始化 Court
    if not initialize_court():
        print("\n⚠️  Court initialization failed, but server will start anyway.")
        print("Please check the error message and set up API keys properly.\n")
    
    # 启动 Flask 服务器
    port = int(os.getenv("PORT", 5000))
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print(f"📁 Database location: {Path(__file__).parent}/court_history.db")
    print("\nPress Ctrl+C to stop the server.\n")
    
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)


if __name__ == '__main__':
    main()

