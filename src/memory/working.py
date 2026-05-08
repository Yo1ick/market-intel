from src.llm.provider import LLMProvider


class WorkingMemory:
    """
    会话级消息存储、压缩、组装。

    职责单一:把对话消息收拾成 OpenAI messages 格式,供 Agent 层送给主 LLM。
    不参与主对话调用,仅内部使用 compression_llm 做阈值压缩。
    """

    def __init__(self, llm: LLMProvider):
        """
        Args:
            llm:用于压缩的LLMProvider(通常是 qwen-turbo 等廉价模型)。
                主对话 LLM 由 Agent 层持有,不传入此处。
        """
        self._llm = llm
        self._messages: list[dict] = []

    def get_messages(self) -> list[dict]:
        """
        返回当前对话的消息列表

        Returns:
            消息列表,压缩后会在头部插入总结段
        """

        return self._messages

    def summarize(self) -> None:
        """
        达到50% token时压缩旧消息。

        压缩后,[0] 位置是总结段,[1..N] 是最近 N 条原文。
        调用者无需接收返回值,压缩完后用 get_messages() 拿更新后的列表。

        Raises:
            LLMError: 压缩调用失败时(由 LLMProvider 抛出)
        """
        ...

    def add_message(self, message: dict) -> None:
        """往工作记忆尾部追加一条消息

        Args:
            message: OpenAI messages 格式的字典,形如 {"role": "user", "content": "..."}

        Raises:
            AssertionError: role 角色不正确
            AssertionError: tool_call_id 不存在
        """
        role = message.get("role")
        assert role in {"user", "assistant", "tool"}, f"role为{role},角色不正确"
        if role == "tool":
            assert "tool_call_id" in message, "role='tool' 但缺 tool_call_id"
        self._messages.append(message)
