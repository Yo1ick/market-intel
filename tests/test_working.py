# class FakeLLM:
#     def generate(self, messages: list[dict], tools: list[dict] | None = None, temperature=0.3) -> LLMResponse:
#         return  LLMResponse(content="fake response")


def test_add_message_appends_user_message():
    class FakeLLM:
        def generate(self, messages, tools=None, temperature=0.3):
            from src.llm.provider import LLMResponse
            return  LLMResponse(content="fake response")
    fllm = FakeLLM()
    from src.memory.working import WorkingMemory
    wm = WorkingMemory(llm=fllm)
    wm.add_message({"role": "user", "content": "fake message"})
    assert wm.get_messages() == [{"role": "user", "content": "fake message"}]

def test_summarize_no_trigger_below_threshold():
    class FakeLLM:
        def generate(self, messages, tools=None, temperature=0.3):
            from src.llm.provider import LLMResponse
            return LLMResponse(content="should not be called")

    from src.memory.working import WorkingMemory
    wm = WorkingMemory(llm=FakeLLM())
    wm.add_message({"role": "user", "content": "你好"})
    wm.add_message({"role": "assistant", "content": "你好，我没什么可以帮您，你自己忙吧"})

    wm.summarize()

    assert len(wm.get_messages()) == 2
    assert wm.get_messages()[0]["content"] == "你好"


def test_summarize_compression_above_threshold():
    class FakeLLM:
        def generate(self, messages, tools=None, temperature=0.3):
            from src.llm.provider import LLMResponse
            return LLMResponse(content="FAKE_SUMMARY")

    from src.memory.working import WorkingMemory
    wm = WorkingMemory(llm=FakeLLM())

    wm.add_message({"role": "user", "content": "我想了解贵州茅台"})
    wm.add_message({"role": "assistant", "content": "贵州茅台是高端白酒龙头"})
    wm.add_message({"role": "user", "content": "现在适合买入吗"})
    wm.add_message({"role": "assistant", "content": "看估值和大盘综合判断"})
    wm.add_message({"role": "user", "content": "对比五粮液呢"})
    wm.add_message({"role": "assistant", "content": "五粮液估值便宜但护城河略弱"})

    wm.summarize(keep_recent_n=2, context_window_size=100, compress_threshold_ratio=0.5)

    msgs = wm.get_messages()

    # 验证 1:总长度 = 1 summary + 2 recent = 3
    assert len(msgs) == 3

    # 验证 2:_messages[0] 是 FakeLLM 返回的总结
    assert msgs[0]["role"] == "assistant"
    assert msgs[0]["content"] == "FAKE_SUMMARY"

    # 验证 3:最后 2 条是原始最近消息
    assert msgs[-2]["content"] == "对比五粮液呢"
    assert msgs[-1]["content"] == "五粮液估值便宜但护城河略弱"

