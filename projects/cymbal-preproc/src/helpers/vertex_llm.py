import time
from typing import Any, Mapping, List, Dict, Optional, Tuple
from pydantic import BaseModel, Extra, root_validator
from langchain.llms.base import LLM
from langchain.embeddings.base import Embeddings
from langchain.chat_models.base import BaseChatModel
from langchain.llms.utils import enforce_stop_tokens
from langchain.schema import Generation, LLMResult
from langchain.schema import (
    AIMessage,
    BaseMessage,
    ChatGeneration,
    ChatResult,
    HumanMessage,
    SystemMessage,
)
from vertexai.preview.language_models import (
    TextGenerationResponse,
    ChatSession,
    TextEmbeddingModel,
)


def rate_limit(max_per_minute=500):
    period = 60 / max_per_minute
    while True:
        before = time.time()
        yield
        after = time.time()
        elapsed = after - before
        sleep_time = max(0, period - elapsed)
        if sleep_time > 0:
            #print(f"Sleeping {sleep_time:.1f} seconds")
            time.sleep(sleep_time)


class _VertexCommon(BaseModel):
    """Wrapper around Vertex AI large language models.

    To use, you should have the
    ``google.cloud.aiplatform.private_preview.language_models`` python package
    installed.
    """

    client: Any = None  #: :meta private:
    model_name: str = "text-bison-001"
    """Model name to use."""

    temperature: float = 0.2
    """What sampling temperature to use."""

    top_p: int = 0.8
    """Total probability mass of tokens to consider at each step."""

    top_k: int = 40
    """The number of highest probability tokens to keep for top-k filtering."""

    max_output_tokens: int = 200
    """The maximum number of tokens to generate in the completion."""

    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling Vertex AI API."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }

    def _predict(self, prompt: str, stop: Optional[List[str]]) -> str:
        res = self.client.predict(prompt, **self._default_params)
        return self._enforce_stop_words(res.text, stop)

    def _enforce_stop_words(self, text: str, stop: Optional[List[str]]) -> str:
        if stop:
            return enforce_stop_tokens(text, stop)
        return text

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "vertex_ai"


class VertexLLM(_VertexCommon, LLM):
    model_name: str = "google/text-bison@001"

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            from vertexai.preview.language_models import TextGenerationModel
        except ImportError:
            raise ValueError("Could not import Vertex AI LLM python package. ")

        try:
            values["client"] = TextGenerationModel.from_pretrained(values["model_name"])
        except AttributeError:
            raise ValueError("Could not set Vertex Text Model client.")

        return values

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call out to Vertex AI's create endpoint.

        Args:
            prompt: The prompt to pass into the model.

        Returns:
            The string generated by the model.
        """
        return self._predict(prompt, stop)


class _VertexChatCommon(_VertexCommon):
    """Wrapper around Vertex AI Chat large language models.

    To use, you should have the
    ``google.cloud.aiplatform.private_preview.language_models`` python package
    installed.
    """

    model_name: str = "chat-bison@001"
    """Model name to use."""

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            from vertexai.preview.language_models import ChatModel
        except ImportError:
            raise ValueError("Could not import Vertex AI LLM python package. ")

        try:
            values["client"] = ChatModel.from_pretrained(values["model_name"])
        except AttributeError:
            raise ValueError("Could not set Vertex Text Model client.")

        return values

    def _response_to_chat_results(
        self, response: TextGenerationResponse, stop: Optional[List[str]]
    ) -> ChatResult:
        text = self._enforce_stop_words(response.text, stop)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


class VertexChat(_VertexChatCommon, BaseChatModel):
    """Wrapper around Vertex AI large language models."""

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        chat, prompt = self._start_chat(messages)
        response = chat.send_message(prompt)
        return self._response_to_chat_results(response, stop=stop)

    def _start_chat(self, messages: List[BaseMessage]) -> Tuple[ChatSession, str]:
        """Start a chat.
        Args:
            messages: a list of BaseMessage.
        Returns:
            a tuple that has a Vertex AI chat model initializes, and a prompt to send to the model.
        Currently it expects either one HumanMessage, or two message (SystemMessage and HumanMessage).
        If two messages are provided, the first one would be use for context.
        """
        if len(messages) == 1:
            message = messages[0]
            if not isinstance(message, HumanMessage):
                raise ValueError(
                    "Message should be from a human if it's the first one."
                )
            context, prompt = None, message.content
        elif len(messages) == 2:
            first_message, second_message = messages[0], messages[1]
            if not isinstance(first_message, SystemMessage):
                raise ValueError(
                    "The first message should be a system if there're two of them."
                )
            if not isinstance(second_message, HumanMessage):
                raise ValueError("The second message should be from a human.")
            context, prompt = first_message.content, second_message.content
        else:
            raise ValueError(
                f"Chat model expects only one or two messages. Received {len(messages)}"
            )
        chat = self.client.start_chat(context=context, **self._default_params)
        return chat, prompt

    async def _agenerate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        raise NotImplementedError(
            """Vertex AI doesn't support async requests at the moment."""
        )


class VertexMultiTurnChat(_VertexChatCommon, BaseChatModel):
    """Wrapper around Vertex AI large language models."""

    chat: Optional[ChatSession] = None

    def clear_chat(self) -> None:
        self.chat = None

    def start_chat(self, message: Optional[SystemMessage] = None) -> None:
        if self.chat:
            raise ValueError("Chat has already been started. Please, clear it first.")
        if message and not isinstance(message, SystemMessage):
            raise ValueError("Context should be a system message")
        context = message.content if message else None
        self.chat = self.client.start_chat(context=context, **self._default_params)

    @property
    def history(self) -> List[Tuple[str]]:
        """Chat history."""
        if self.chat:
            return self.chat._history
        return []

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        if len(messages) != 1:
            raise ValueError(
                "You should send exactly one message to the chat each turn."
            )
        if not self.chat:
            raise ValueError("You should start_chat first!")
        response = self.chat.send_message(messages[0].content)
        return self._response_to_chat_results(response, stop=stop)

    async def _agenerate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        raise NotImplementedError(
            """Vertex AI doesn't support async requests at the moment."""
        )


class VertexEmbeddings(Embeddings, BaseModel):
    """Wrapper around Vertex AI large language models embeddings API.

    To use, you should have the
    ``google.cloud.aiplatform.private_preview.language_models`` python package
    installed.
    """

    model_name: str = "google/textembedding-gecko@001"
    """Model name to use."""

    model: Any
    requests_per_minute: int = 15

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that the python package exists in environment."""
        try:
            from vertexai.preview.language_models import TextEmbeddingModel

        except ImportError:
            raise ValueError("Could not import Vertex AI LLM python package. ")

        try:
            values["model"] = TextEmbeddingModel

        except AttributeError:
            raise ValueError("Could not set Vertex Text Model client.")

        return values

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Call Vertex LLM embedding endpoint for embedding docs
        Args:
            texts: The list of texts to embed.
        Returns:
            List of embeddings, one for each text.
        """
        self.model = self.model.from_pretrained(self.model_name)

        limiter = rate_limit(self.requests_per_minute)
        results = []
        docs = list(texts)

        while docs:
            # Working in batches of 2 because the API apparently won't let
            # us send more than 2 documents per request to get embeddings.
            head, docs = docs[:2], docs[2:]
            # print(f'Sending embedding request for: {head!r}')
            chunk = self.model.get_embeddings(head)
            results.extend(chunk)
            next(limiter)

        return [r.values for r in results]

    def embed_query(self, text: str) -> List[float]:
        """Call Vertex LLM embedding endpoint for embedding query text.
        Args:
          text: The text to embed.
        Returns:
          Embedding for the text.
        """
        single_result = self.embed_documents([text])
        return single_result[0]
