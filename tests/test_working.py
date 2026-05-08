


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
