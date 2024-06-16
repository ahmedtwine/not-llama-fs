import base64
import json
import logging
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor

import groq
import magic
import openai

from ..fs.tree import TreeObject
from .interface import ABCProducer


class OpenAIProducer(ABCProducer):
    def __init__(self, host: str = "https://api.openai.com/v1", api_key: str = None):
        super().__init__()
        self.host = host
        self.prompt = None
        self.model = None
        self.options = {}
        self._client = None
        self.api_key = api_key
        self.cache = {}
        self.max_retries = 3
        self.retry_delay = 5

    def setup(
            self,
            prompt: str,
            model: str = "gpt-3.5-turbo",
            options: dict | None = None,
    ):
        self.prompt = prompt
        self.model = model
        if options is not None:
            self.options = options
        if self.options is None:
            self.options = {}

    @property
    def client(self) -> openai.OpenAI:
        if self._client is None:
            self._client = openai.OpenAI(api_key=self.api_key, base_url=self.host)
        return self._client

    def prepare_file(self, path: pathlib.Path):
        if self.model is None:
            raise ValueError("Model is not set")
        if self.prompt is None:
            raise ValueError("Prompt is not set")
        if self.options is None:
            raise ValueError("Options are not set")

        logging.info(f"Preparing {path}")
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(path.as_posix())
        logging.info(f"Detected mime type: {mime_type}")
        result = None

        if path.as_posix() in self.cache:
            logging.info(f"Using cached result for {path}")
            return self.cache[path.as_posix()]

        retries = 0
        while retries < self.max_retries:
            try:
                if mime_type.startswith("text"):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 4096:
                            content = content[:4096]
                        result = self.client.with_options(**self.options).chat.completions.create(
                            messages=[
                                {"content": self.prompt, "role": "system"},
                                {"content": content, "role": "user"}
                            ],
                            model=self.model,
                            response_format={"type": "json_object"}
                        )
                elif mime_type.startswith("image"):
                    with open(path, "rb") as f:
                        image_data = f.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        result = self.client.with_options(**self.options).chat.completions.create(
                            messages=[
                                {"content": self.prompt, "role": "system"},
                                {"role": "user", "content": [{"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }}]}
                            ],
                            temperature=1,
                            max_tokens=256,
                            top_p=1,
                            frequency_penalty=0,
                            presence_penalty=0,
                            model=self.model,
                            response_format={"type": "json_object"}
                        )
                else:
                    logging.warning(f"{mime_type} is not yet supported")
                    return
                break
            except openai.RateLimitError as e:
                logging.warning(f"Rate limit error: {e}")
                logging.warning(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                retries += 1
            except openai.AuthenticationError as e:
                logging.error(f"Authentication error: {e}")
                return
            except Exception as e:
                logging.error(f"Error preparing file {path}: {e}")
                return

        if retries == self.max_retries:
            logging.error(f"Max retries reached for {path}")
            return

        logging.info(f"Prepared {path}, result: {result}")
        self.cache[path.as_posix()] = result.choices[0].message.content
        return result.choices[0].message.content

    def prepare_files(self, files_type: str | None = None):
        with ThreadPoolExecutor() as executor:
            futures = []
            for file in self.files:
                if files_type is not None:
                    mime = magic.Magic(mime=True)
                    mime_type = mime.from_file(file.as_posix())
                    if not mime_type.startswith(files_type):
                        continue
                if file.as_posix() in [f[0] for f in self.prepared_files]:
                    continue
                futures.append(executor.submit(self.prepare_file, file))

            for future in futures:
                result = future.result()
                if result is not None:
                    self.prepared_files.append((file.as_posix(), result))

    def produce(self) -> TreeObject:
        if self.model is None:
            raise ValueError("Model is not set")
        if self.prompt is None:
            raise ValueError("Prompt is not set")
        if self.options is None:
            raise ValueError("Options are not set")

        groq_response = self.client.with_options(**self.options).chat.completions.create(
            messages=[
                {"content": self.prompt, "role": "system"},
                {"content": json.dumps(self.prepared_files), "role": "user"}
            ],
            model=self.model,
            response_format={"type": "json_object"}
        ).choices[0].message.content

        try:
            groq_response_json = json.loads(groq_response)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON response: {e}")
            logging.error(f"Response: {groq_response}")
            raise e

        return TreeObject.from_json(groq_response_json)