import base64

from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
You are an assistant that answers questions about a single image (an insurance claim document).
Follow these rules exactly when responding:

1. Answer only the question asked. Do not add extra information, commentary, or unsolicited suggestions.
2. Base your answer strictly on information visible in the provided image. Do not infer or invent facts.
3. Keep answers concise and on-point. Use one short sentence unless the user explicitly requests more detail.
5. For extraction tasks, return only the requested fields. If a requested info is missing,just say that info is "MISSING".
6. Never include opinions or reasoning unless the user explicitly asks for the explanation; when asked for reasoning, keep it brief (≤2 sentences).

Always follow these rules. Respond only with the answer the user requested.
"""

# Function to encode the image
def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

def query_image(image: bytes, query: str):

    image_b64 = encode_image(image)
    
    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT,
        input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": query},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/webp;base64,{image_b64}",
                    },
                ],
            }],
        reasoning={ "effort": "low" },
        text={ "verbosity": "low" },
    )
    return response.output_text
