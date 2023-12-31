from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate

from server.agent.custom_agent.ChatGLM3Agent import initialize_glm3_agent
from server.agent.tools_select import tools, tool_names, aime_tools_names, aime_tools
from server.agent.callbacks import CustomAsyncIteratorCallbackHandler, Status
from langchain.agents import LLMSingleActionAgent, AgentExecutor
from server.agent.custom_template import CustomOutputParser, CustomPromptTemplate, SalesConvoOutputParser
from fastapi import Body
from fastapi.responses import StreamingResponse
from configs import LLM_MODELS, TEMPERATURE, HISTORY_LEN, Agent_MODEL
from server.utils import wrap_done, get_ChatOpenAI, get_prompt_template
from langchain.chains import LLMChain
from typing import AsyncIterable, Optional
import asyncio
from typing import List
from server.chat.utils import History
import json
from server.agent import model_container
from server.knowledge_base.kb_service.base import get_kb_details

async def aime_chat(query: str = Body(..., description="用户输入", examples=["恼羞成怒"]),
                    history: List[History] = Body([],
                                                  description="历史对话",
                                                  examples=[[
                                                      {"role": "user", "content": "请使用知识库工具查询今天北京天气"},
                                                      {"role": "assistant",
                                                       "content": "使用天气查询工具查询到今天北京多云，10-14摄氏度，东北风2级，易感冒"}]]
                                                  ),
                    stream: bool = Body(False, description="流式输出"),
                    model_name: str = Body(LLM_MODELS[0], description="LLM 模型名称。"),
                    temperature: float = Body(TEMPERATURE, description="LLM 采样温度", ge=0.0, le=1.0),
                    max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
                    prompt_name: str = Body("default",
                                            description="使用的prompt模板名称(在configs/prompt_config.py中配置)"),
                    # top_p: float = Body(TOP_P, description="LLM 核采样。勿与temperature同时设置", gt=0.0, lt=1.0),
                    ):
    print("toto aime chat")
    history = [History.from_data(h) for h in history]
    conversation_stages = {
        "1": "Introduction: Greet users politely, Start the conversation by introducing yourself. Be polite and respectful while keeping the tone of the conversation professional. Your greeting should be welcoming. Always clarify in your greeting the reason why you are contacting the prospect.",
        "2": "Qualification: Qualify the prospect by confirming if they are the right person to talk to regarding your product/service. Ensure that they have the authority to make purchasing decisions.",
        "3": "Value proposition: Briefly explain how your product/service can benefit the prospect. Focus on the unique selling points and value proposition of your product/service that sets it apart from competitors.",
        "4": "Needs analysis: Ask open-ended questions to uncover the prospect's needs and pain points. Listen carefully to their responses and take notes.",
        "5": "Solution presentation: Based on the prospect's needs, present your product/service as the solution that can address their pain points.",
        "6": "Objection handling: Address any objections that the prospect may have regarding your product/service. Be prepared to provide evidence or testimonials to support your claims.",
        "7": "Close: Ask for the sale by proposing a next step. This could be a demo, a trial or a meeting with decision-makers. Ensure to summarize what has been discussed and reiterate the benefits.",
    }
    stage_prompt = ""
    for key, value in conversation_stages.items():
        stage_prompt += f"{key}. {value}\n"
    verbose = True

    async def aime_chat_iterator(
            query: str,
            history: Optional[List[History]],
            model_name: str = LLM_MODELS[0],
            prompt_name: str = prompt_name,
    ) -> AsyncIterable[str]:
        nonlocal max_tokens
        # import pydevd_pycharm
        # pydevd_pycharm.settrace('49.7.62.197', port=10090, stdoutToServer=True, stderrToServer=True, suspend=False)

        assistant_name = "cashbacks.ai"
        assistant_role = "smart AI agent"
        work_purpose = "exciting discounts, coupons, and rebate websites from brands around the world"
        conversation_purpose = "find out whether they are looking to get cheaper items by using coupons"
        conversation_history = [],
        conversation_type = "online chat"
        conversation_stage_id = 1
        callback = CustomAsyncIteratorCallbackHandler()
        if isinstance(max_tokens, int) and max_tokens <= 0:
            max_tokens = None

        model = get_ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            callbacks=[callback],
        )

        ## 传入全局变量来实现agent调用
        kb_list = {x["kb_name"]: x for x in get_kb_details()}
        # model_container.DATABASE = {name: details['kb_info'] for name, details in kb_list.items()}
        model_container.DATABASE = {name: details['kb_info'] for name, details in kb_list.items()}

        if Agent_MODEL:
            ## 如果有指定使用Agent模型来完成任务
            model_agent = get_ChatOpenAI(
                model_name=Agent_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                callbacks=[callback],
            )
            model_container.MODEL = model_agent
        else:
            model_container.MODEL = model

        # aime chain
        prompt_template = get_prompt_template("aime_chat", prompt_name)
        prompt_template_agent = CustomPromptTemplate(
            template=prompt_template,
            tools=aime_tools,
            input_variables=[
                "input",
                "intermediate_steps",
                "assistant_name",
                "assistant_role",
                "work_purpose",
                "conversation_purpose",
                "conversation_type",
                "conversation_stage",
                "conversation_history"
            ],
            partial_variables={"conversation_stages": stage_prompt},
        )
        output_parser = SalesConvoOutputParser()
        llm_chain = LLMChain(llm=model, prompt=prompt_template_agent)
        # 把history转成agent的memory

        # aime stage
        stage_prompt_template = get_prompt_template("aime_chat", "stage_analyzer")
        stage_prompt_template_agent = PromptTemplate(
            template=stage_prompt_template,
            input_variables=["conversation_history"],
            partial_variables={"conversation_stages": stage_prompt},
        )
        stage_chain = LLMChain(llm=model, prompt=stage_prompt_template_agent, verbose=verbose)
        memory = ConversationBufferWindowMemory(
            ai_prefix=assistant_name,
            input_key="input",
            memory_key="conversation_history",
            k=HISTORY_LEN * 2)
        for message in history:
            # 检查消息的角色
            if message.role == 'user':
                # 添加用户消息
                memory.chat_memory.add_user_message(message.content)
            else:
                # 添加AI消息
                memory.chat_memory.add_ai_message(message.content)
        if query != "":
            memory.chat_memory.add_user_message(query)

        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:", "Observation"],
            allowed_tools=aime_tools_names,
            verbose=verbose
        )
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent,
                                                            tools=aime_tools,
                                                            verbose=verbose,
                                                            memory=memory,
                                                            )

        while True:
            conversation_stage_id = stage_chain.run(conversation_history=memory.buffer)
            try:
                task = asyncio.create_task(wrap_done(
                    agent_executor.acall(
                        inputs=dict(
                            input=query,
                            assistant_name=assistant_name,
                            assistant_role=assistant_role,
                            work_purpose=work_purpose,
                            conversation_purpose=conversation_purpose,
                            conversation_type=conversation_type,
                            conversation_stage=conversation_stages[conversation_stage_id],
                        ),
                        callbacks=[callback],
                        include_run_info=True
                    ),
                    callback.done))
                break
            except:
                pass

        if stream:
            async for chunk in callback.aiter():
                tools_use = []
                # Use server-sent-events to stream the response
                data = json.loads(chunk)
                if data["status"] == Status.start or data["status"] == Status.complete:
                    continue
                elif data["status"] == Status.error:
                    tools_use.append("\n```\n")
                    tools_use.append("工具名称: " + data["tool_name"])
                    tools_use.append("工具状态: " + "调用失败")
                    tools_use.append("错误信息: " + data["error"])
                    tools_use.append("重新开始尝试")
                    tools_use.append("\n```\n")
                    yield json.dumps({"tools": tools_use}, ensure_ascii=False)
                elif data["status"] == Status.tool_finish:
                    tools_use.append("\n```\n")
                    tools_use.append("工具名称: " + data["tool_name"])
                    tools_use.append("工具状态: " + "调用成功")
                    tools_use.append("工具输入: " + data["input_str"])
                    tools_use.append("工具输出: " + data["output_str"])
                    tools_use.append("\n```\n")
                    # yield json.dumps({"final_answer": data["output_str"]}, ensure_ascii=False)
                    yield json.dumps({"tools": tools_use}, ensure_ascii=False)
                elif data["status"] == Status.agent_finish:
                    yield json.dumps({"final_answer": data["final_answer"]}, ensure_ascii=False)
                else:
                    yield json.dumps({"answer": data["llm_token"]}, ensure_ascii=False)


        else:
            answer = ""
            final_answer = ""
            async for chunk in callback.aiter():
                # Use server-sent-events to stream the response
                data = json.loads(chunk)
                if data["status"] == Status.start or data["status"] == Status.complete:
                    continue
                if data["status"] == Status.error:
                    answer += "\n```\n"
                    answer += "工具名称: " + data["tool_name"] + "\n"
                    answer += "工具状态: " + "调用失败" + "\n"
                    answer += "错误信息: " + data["error"] + "\n"
                    answer += "\n```\n"
                if data["status"] == Status.tool_finish:
                    answer += "\n```\n"
                    answer += "工具名称: " + data["tool_name"] + "\n"
                    answer += "工具状态: " + "调用成功" + "\n"
                    answer += "工具输入: " + data["input_str"] + "\n"
                    answer += "工具输出: " + data["output_str"] + "\n"
                    answer += "\n```\n"
                if data["status"] == Status.agent_finish:
                    final_answer = data["final_answer"]
                else:
                    answer += data["llm_token"]

            yield json.dumps({"answer": answer, "final_answer": final_answer}, ensure_ascii=False)
        await task

    return StreamingResponse(aime_chat_iterator(query=query,
                                                history=history,
                                                model_name=model_name,
                                                prompt_name=prompt_name),
                             media_type="text/event-stream")
