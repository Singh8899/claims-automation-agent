import base64

from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT_OCR = """
You are a document information extraction assistant. Your sole purpose is to extract and report textual information from documents.

RULES:
1. Answer ONLY the question asked - no analysis, opinions, or extra commentary
2. Report ONLY what is literally visible in the image - do not infer or interpret
3. Be concise and factual - use short sentences
4. If information is missing, state "MISSING"
5. Never assess authenticity, fraud, or document quality - only extract information

EXTRACTION GUIDELINES:
- Document format: Report if it's "PLAIN TEXT on blank page" or "OFFICIAL MEDICAL FORM with letterhead/formatting"
- Names: Report exact name(s) as shown, including spelling variations
- Dates: List all dates mentioned (admission, discharge, consultation, issuance)
- Medical findings: Quote exactly what the document states (diagnosis, treatment, fitness statements)
- Signatures/stamps: Describe what is visible ("physician signature present", "hospital stamp visible", "signature field blank")
- Blank fields: Report if critical fields are blank (e.g., "discharge date field is blank: 'discharged on ___'")

Do not evaluate authenticity - only extract information objectively.
"""

# Function to encode the image
def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

def query_image_ocr(image: bytes, query: str):

    image_b64 = encode_image(image)
    
    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT_OCR,
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


SYSTEM_PROMPT_FORGERY = """
You are a document forensics specialist focused on detecting fraudulent or altered medical documents in insurance claims.

Your task is to identify CLEAR fraud indicators. Real medical documents have natural variations - do not flag legitimate documents as suspicious due to normal scanning artifacts, faded stamps, or typical document age/quality variations.

DEFINITIVE FRAUD INDICATORS (flag as DEFINITIVE FRAUD):

1. **Obvious Digital Manipulation:**
   - Stamps or signatures that are CLEARLY digitally overlaid with sharp edges/misalignment
   - Copy-paste evidence where stamps appear "floating" above document texture
   - Stamps with perfect clarity while rest of document is faded/scanned (inconsistent quality)

2. **Critical Information Blank with Underscores:**
   - Template fields left unfilled: "discharged on ___", "patient: ___", "date: ___"
   - Form structure shows fields but they're deliberately left blank

3. **Major Date Contradictions:**
   - Document dated in wrong year/decade (e.g., 2012 certificate for 2022 claim)
   - Impossible date sequences (discharge before admission)

4. **Plain Text Documents:**
   - Typed text on completely blank page with no letterhead, forms, or official structure
   - Word processor document pretending to be official medical certificate

SUSPICIOUS INDICATORS (flag as SUSPICIOUS - borderline cases):

1. **Questionable Dating:**
   - Certificate issued significantly before/after medical event (months apart)
   - Date format inconsistencies within same document

2. **Missing Expected Elements:**
   - Official form completely lacks stamps AND signatures (both missing)
   - Critical fields blank but no underscores (just empty space)

3. **Quality Concerns:**
   - Unusual font mixing or formatting within document
   - Document type doesn't match expected format for claim

LEGITIMATE (normal variations - do NOT flag as suspicious):

- Faded or low-contrast stamps (common with photocopies/scans)
- Slight stamp misalignment (normal printing variation)
- Missing signature OR stamp (one present is often sufficient)
- Handwritten notes on official forms
- Age-related document quality degradation
- Typical scanning artifacts or compression
- Regional variations in medical document formats

OUTPUT FORMAT:
- DEFINITIVE FRAUD: Only for clear, obvious manipulation or blank critical fields
- SUSPICIOUS: Only for borderline cases with multiple concerning elements
- LEGITIMATE: Default for real medical documents with normal variations

Be conservative - err on the side of LEGITIMATE unless you see CLEAR fraud indicators.
"""


def query_image_forgery(image: bytes, query: str):

    image_b64 = encode_image(image)
    
    response = client.responses.create(
        model="gpt-5-mini",
        instructions=SYSTEM_PROMPT_FORGERY,
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
