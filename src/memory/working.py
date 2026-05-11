from src.llm.provider import LLMProvider
import tiktoken

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

    def summarize(self,keep_recent_n = 4,compress_threshold_ratio = 0.5,context_window_size = 32000,):
        """
        达到50% token时压缩旧消息。

        压缩后,[0] 位置是总结段,[1..N] 是最近 N 条原文。
        调用者无需接收返回值,压缩完后用 get_messages() 拿更新后的列表。

        Raises:
            LLMError: 压缩调用失败时(由 LLMProvider 抛出)
        """
        encoding = tiktoken.get_encoding("cl100k_base")
        total = 0
        for msg in self._messages:
            content = msg.get("content", "") or ""
            tokens = encoding.encode(content)
            total += len(tokens)
        threshold = context_window_size * compress_threshold_ratio
        if total < threshold:
            return
        cut_index = -keep_recent_n
        if self._messages[cut_index].get("role") == "tool":
            cut_index -= 1
        old_messages = self._messages[:cut_index]
        recent_messages = self._messages[cut_index:]
        conversation_str = ""
        for m in old_messages:
            role = m.get("role", "")
            content = m.get("content", "") or ""
            conversation_str += f"{role}: {content}\n"
        summarize_messages = [
            {"role": "user",
            "content": "把下面的对话总结成一段简洁中文,保留关键信息(用户问题、助手回答、工具返回值):\n\n" + conversation_str}
        ]
        response = self._llm.generate(summarize_messages)
        summary_text = response.content or ""
        summary_msg = {"role": "assistant", "content": summary_text}
        self._messages = [summary_msg] + recent_messages

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
