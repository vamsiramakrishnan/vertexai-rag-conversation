import time
from typing import Dict, List
from langchain.embeddings.base import Embeddings
from langchain.llms.vertexai import _VertexAICommon
from langchain.pydantic_v1 import root_validator
from langchain.utilities.vertexai import raise_vertex_import_error

def rate_limit(limit_per_minute : int, timestamps: list[float]) -> list[float]:
    
  current_time = time.time()

  # Remove timestamps older than 1 minute
  while timestamps and timestamps[0] < current_time - 60:
      timestamps.pop(0)

  # Check if the number of invocations in the last minute exceeds the limit
  if len(timestamps) >= limit_per_minute:
      print(f"Rate limit exceeded. Allowed {limit_per_minute} requests per minute. Sleeping for the rest of the minute.")
      time.sleep(60 - (current_time - timestamps[0]))
      timestamps.clear()  # Clear all timestamps after sleeping

  # Add the current timestamp to the queue
  timestamps.append(current_time)
  return timestamps      

class VertexAIEmbeddings(_VertexAICommon, Embeddings):
    """Google Cloud VertexAI embedding models."""

    model_name: str = "textembedding-gecko"
    requests_per_minute: int = 15

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        """Validates that the python package exists in environment."""
        cls._try_init_vertexai(values)
        try:
            from vertexai.preview.language_models import TextEmbeddingModel
        except ImportError:
            raise_vertex_import_error()
        values["client"] = TextEmbeddingModel.from_pretrained(values["model_name"])
        return values

    def embed_documents(
        self, texts: List[str], batch_size: int = 5
    ) -> List[List[float]]:
        """Embed a list of strings. Vertex AI currently
        sets a max batch size of 5 strings.

        Args:
            texts: List[str] The list of strings to embed.
            batch_size: [int] The batch size of embeddings to send to the model

        Returns:
            List of embeddings, one for each text.
        """
        print(f"Embeddings Model Used {self.model_name}")
        timestamps = []

        embeddings = []    
        for batch in range(0, len(texts), batch_size):
            text_batch = texts[batch : batch + batch_size]
            embeddings_batch = self.client.get_embeddings(text_batch)
            embeddings.extend([el.values for el in embeddings_batch])
            rate_limit(self.requests_per_minute, timestamps)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a text.

        Args:
            text: The text to embed.

        Returns:
            Embedding for the text.
        """
        embeddings = self.client.get_embeddings([text])
        return embeddings[0].values