from kokoro import KPipeline
from google import genai
from google.genai import types
import torch 
import os 

configs = types.GenerateContentConfig(max_output_tokens=200,
                                      temperature=0.5
                                      )
client = genai.Client(api_key="YOUR-API-KEY")

tts_pipeline = KPipeline(lang_code='a')

torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)] 
