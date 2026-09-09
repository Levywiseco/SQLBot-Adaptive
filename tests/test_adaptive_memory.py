from apps.learning.crud.learning import sql_dependencies, sql_is_read_only
from apps.memory.crud.memory import _fingerprint, _memory_score, looks_like_follow_up
from apps.memory.models.memory import MemoryEntry


def test_short_follow_up_detection_is_conservative():
    assert looks_like_follow_up("那 7 月呢？")
    assert looks_like_follow_up("what about last month")
    assert not looks_like_follow_up("请统计新客订单数并解释定义")
    assert not looks_like_follow_up("请重新设计整个销售分析模型，包含渠道、地区、商品和退货原因" * 3)


def test_personal_preference_can_be_retrieved_without_keyword_match():
    memory = MemoryEntry(
        id=1,
        oid=1,
        owner_user_id=7,
        created_by=7,
        title="金额显示单位",
        content="金额默认用万元显示",
        memory_type="preference",
        scope="personal",
        fingerprint="x" * 64,
    )
    assert _memory_score("统计本月净销售额", memory) > 0


def test_business_rule_requires_a_relevant_term():
    memory = MemoryEntry(
        id=2,
        oid=1,
        created_by=1,
        title="退款归属规则",
        content="退款按退款发生日归属",
        keywords=["退款"],
        memory_type="business_rule",
        scope="workspace",
        fingerprint="y" * 64,
    )
    assert _memory_score("统计退款金额", memory) > 0
    assert _memory_score("统计新增用户", memory) == 0


def test_memory_fingerprint_is_normalized_and_scope_sensitive():
    base = {
        "owner_user_id": 1,
        "datasource_id": 3,
        "memory_type": "preference",
        "title": " 金额 单位 ",
        "content": "默认 用 万元",
    }
    first = _fingerprint(scope="personal", **base)
    second = _fingerprint(
        scope="personal",
        **{**base, "title": "金额 单位", "content": "默认   用 万元"},
    )
    shared = _fingerprint(scope="workspace", **base)
    assert first == second
    assert first != shared


def test_learning_only_accepts_single_read_only_query():
    assert sql_is_read_only("WITH paid AS (SELECT * FROM sales) SELECT * FROM paid")
    assert not sql_is_read_only("SELECT 1; DROP TABLE sales")
    assert not sql_is_read_only("UPDATE sales SET amount = 0")


def test_reviewed_sql_dependencies_include_tables_and_fields():
    dependencies = sql_dependencies(
        "SELECT s.region, SUM(s.amount) FROM sales s GROUP BY s.region"
    )
    assert dependencies == ["sales", "sales.region", "sales.amount"]


def test_reviewed_sql_dependencies_resolve_single_source_cte():
    dependencies = sql_dependencies(
        "WITH paid AS ("
        "SELECT s.region, s.amount FROM sales s WHERE s.status = 'paid'"
        ") SELECT p.region, SUM(p.amount) FROM paid p GROUP BY p.region"
    )
    assert dependencies == [
        "sales",
        "sales.region",
        "sales.amount",
        "sales.status",
    ]
