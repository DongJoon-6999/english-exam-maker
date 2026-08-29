import json
import random
import re
import requests
from typing import Dict, Any, List, Optional

SYSTEM_PROMPT = """You are an expert Korean High School English Teacher and CSAT (수능) / School Exam (내신) Item Writer.
Your task is to analyze an English reading passage (모의고사/교과서 지문) and generate authentic Korean High School subjective summary-completion test questions (고등학교 영어 서술형 요약문 빈칸 완성 문항) tailored to specific difficulty levels.

### Difficulty Levels & Context Guidelines:
- **intro (입문 / 고1 기초)**:
  * Summary Sentence scaffolding: Provide plenty of context before and after the blank. The blank is short (4~6 words) and tests straightforward, intuitive grammar (e.g. basic relative pronoun 'that/which', simple 'to-V').
  * Minimal missing functional words (0~1 word omitted).
- **basic (기본 / 고1~고2 표준)**:
  * Standard Korean high school exam level.
  * Blank length is 6~8 words. Tests standard 5-verb patterns (allow/enable/encourage O to V), participial phrases, or that-clauses.
  * 1~2 functional words omitted (e.g. 'to', 'for', 'that').
- **advanced (실전 / 고2~고3 심화)**:
  * High-school Mock Exam 3-point question level.
  * Blank length is 8~10 words. Requires synthetic thinking with 2~3 base-form modifications (e.g., active/passive participle, tense/agreement, gerund subject).
  * 1~3 functional words omitted.
- **killer (최상위 킬러 / 1등급 변별용)**:
  * CSAT / High School 1st-grade separator question.
  * Blank length is 9~14 words. Tests complex structures (e.g., inversion, Not only A but also B, with+noun+participle, double clauses).
  * Minimal prefix/suffix hints, demanding sophisticated syntactic construction.

### Problem Format & Rules:
1. **Direction (지시문)**:
   "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)"

2. **<단어> (Given Words List)**:
   - Extract the words composing the blank `(A)` and convert inflected words to **base/lemma forms**.
   - Shuffle all words in random order, separated by ' / '.

3. **<조건> (Conditions)**:
   - "1. 어법상 기능어 반드시 추가할 것"
   - "2. 필요시 단어를 변형할 것 (수일치, 시제, 분사, 품사 변형 등)"

4. **Detailed Functional Words Breakdown**:
   - Provide a list of all functional words (that, to, while, by, for, which, etc.) used in the blank, their grammatical roles, and whether they were omitted from the given words list.
"""

def get_gemini_prompt(passage: str, target_grammar: str = "", target_vocab: str = "", candidate_count: int = 3, difficulty: str = "basic") -> str:
    diff_labels = {
        "intro": "입문 (초급 - 풍부한 문맥 힌트, 짧은 빈칸 4~6단어, 기초 문법)",
        "basic": "기본 (표준 - 고1~고2 일반 내신 수준, 6~8단어 빈칸, 5형식/관계사/분사)",
        "advanced": "실전 (심화 - 고2~고3 3점 서술형 수준, 8~10단어 빈칸, 조건부 어형변형)",
        "killer": "최상위 킬러 (고난도 - 고3/1등급 변별용, 9~14단어 복합구문, 도치/상관접속사)"
    }
    diff_desc = diff_labels.get(difficulty, diff_labels["basic"])
    
    grammar_instruction = f"- Focus Grammar to utilize: {target_grammar}" if target_grammar else "- Focus Grammar: Automatically select the most relevant grammar structure suitable for this passage."
    vocab_instruction = f"- Key Vocabulary to include: {target_vocab}" if target_vocab else "- Key Vocabulary: Automatically extract the key subject words from the passage."

    return f"""Please generate {candidate_count} distinct high-school exam subjective summary questions for the following English passage.

[Target Difficulty Level / 출제 난이도]:
{diff_desc}

[Passage / 영어 지문]:
\"\"\"
{passage}
\"\"\"

[User Requirements]:
{grammar_instruction}
{vocab_instruction}

Output your response strictly as a JSON object adhering to this schema:
{{
  "candidates": [
    {{
      "candidate_id": 1,
      "difficulty": "{difficulty}",
      "theme_title": "요약 주제 요약 (한국어 한 줄)",
      "target_grammar_used": "적용된 핵심 문법 (예: 5형식 enable + 목적어 + to부정사)",
      "target_vocab_used": "활용된 핵심 어휘 목록",
      "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
      "sentence_prefix": "요약문 앞부분 (빈칸 앞 문맥)",
      "blank_answer": "빈칸 (A)의 정답 영어 문구",
      "sentence_suffix": "요약문 뒷부분 (빈칸 뒤 문맥, 없으면 빈 문자열)",
      "full_sentence": "완성된 전체 요약문 영어 문장",
      "given_words": ["단어1(원형)", "단어2(원형)", "단어3", "... (무작위 순서)"],
      "conditions": [
        "1. 어법상 기능어 반드시 추가할 것",
        "2. 필요시 단어를 변형할 것"
      ],
      "functional_words_detail": [
        {{
          "word": "to",
          "role": "to부정사 표지 (목적격보어)",
          "omitted_from_given": true,
          "reason": "5형식 동사 뒤 목적격 보어 to부정사"
        }},
        {{
          "word": "that",
          "role": "주격 관계대명사",
          "omitted_from_given": true,
          "reason": "선행사를 수식하는 관계사절 유도"
        }}
      ],
      "added_functional_words": ["to", "that"],
      "modified_words": [
        {{"base": "enable", "modified": "enables", "reason": "단수 주어에 따른 수일치"}},
        {{"base": "restore", "modified": "restore", "reason": "to부정사 뒤 동사원형"}}
      ],
      "translation_korean": "전체 요약문의 자연스러운 한국어 번역",
      "grammar_explanation": "출제 의도 및 문법 포인트에 대한 상세 해설 (한국어)"
    }}
  ]
}}
"""

def generate_with_gemini(api_key: str, passage: str, target_grammar: str = "", target_vocab: str = "", model_name: str = "gemini-3.6-flash", candidate_count: int = 3, difficulty: str = "basic") -> Dict[str, Any]:
    prompt_text = get_gemini_prompt(passage, target_grammar, target_vocab, candidate_count, difficulty)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "responseMimeType": "application/json"
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    # Retry up to 2 times if rate-limited
    import time
    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return clean_and_parse_json(raw_text)
            elif response.status_code == 429:
                if attempt == 0:
                    time.sleep(3) # Wait 3 seconds and retry once
                    continue
                else:
                    raise RuntimeError("Google Gemini 무료 API의 1분당 호출 한도(20회/분)에 일시적으로 도달했습니다. 구글 정책상 약 30~50초 후 자동으로 리셋되므로, 잠시만 기다리신 후 다시 [서술형 문제 생성하기]를 눌러주세요.")
            else:
                error_msg = response.text
                try:
                    err_json = response.json()
                    if "error" in err_json and "message" in err_json["error"]:
                        error_msg = err_json["error"]["message"]
                except Exception:
                    pass
                raise RuntimeError(f"Gemini API Error ({response.status_code}): {error_msg}")
        except requests.exceptions.Timeout:
            raise RuntimeError("Gemini API 서버 응답 시간 초과 (Timeout). 잠시 후 다시 시도해 주세요.")
        except Exception as e:
            if "Google Gemini 무료 API" in str(e) or "Gemini API Error" in str(e):
                raise
            raise RuntimeError(f"문제 생성 실패: {str(e)}")

def generate_with_openai(api_key: str, passage: str, target_grammar: str = "", target_vocab: str = "", model_name: str = "gpt-4o-mini", candidate_count: int = 3, difficulty: str = "basic") -> Dict[str, Any]:
    url = "https://api.openai.com/v1/chat/completions"
    prompt_text = get_gemini_prompt(passage, target_grammar, target_vocab, candidate_count, difficulty)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if response.status_code != 200:
        error_msg = response.text
        try:
            err_json = response.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_msg = err_json["error"]["message"]
        except Exception:
            pass
        raise RuntimeError(f"OpenAI API Error ({response.status_code}): {error_msg}")

    data = response.json()
    try:
        raw_text = data["choices"][0]["message"]["content"]
        return clean_and_parse_json(raw_text)
    except Exception as e:
        raise ValueError(f"Failed to parse OpenAI response: {e}\nRaw: {data}")

def generate_with_claude(api_key: str, passage: str, target_grammar: str = "", target_vocab: str = "", model_name: str = "claude-3-7-sonnet-20250219", candidate_count: int = 3, difficulty: str = "basic") -> Dict[str, Any]:
    url = "https://api.anthropic.com/v1/messages"
    prompt_text = get_gemini_prompt(passage, target_grammar, target_vocab, candidate_count, difficulty)

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": model_name,
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT + "\nOutput strictly valid JSON with no conversational prefix or suffix.",
        "messages": [
            {"role": "user", "content": prompt_text}
        ]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if response.status_code != 200:
        error_msg = response.text
        try:
            err_json = response.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_msg = err_json["error"]["message"]
        except Exception:
            pass
        raise RuntimeError(f"Claude API Error ({response.status_code}): {error_msg}")

    data = response.json()
    try:
        raw_text = data["content"][0]["text"]
        return clean_and_parse_json(raw_text)
    except Exception as e:
        raise ValueError(f"Failed to parse Claude response: {e}\nRaw: {data}")

def clean_and_parse_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return json.loads(text)
def generate_mock_candidates(passage: str, target_grammar: str = "", target_vocab: str = "", candidate_count: int = 3, difficulty: str = "basic") -> Dict[str, Any]:
    """Fallback sample generator reflecting the user's uploaded images and difficulty levels."""
    is_soil_passage = "willow" in passage.lower() or "soil" in passage.lower() or "purifying" in passage.lower()
    is_habit_passage = "habit" in passage.lower() or "routine" in passage.lower() or "cue" in passage.lower()

    if is_soil_passage:
        all_candidates = [
            {
                "candidate_id": 1,
                "difficulty": difficulty,
                "theme_title": "버드나무의 특성을 활용한 친환경적 토양 정화",
                "target_grammar_used": "to부정사의 형용사적 용법 + 분사구문 (extracting)",
                "target_vocab_used": "eco-friendly, restore, extensive, extract, harmful",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "Planting willow trees provides ",
                "blank_answer": "an eco-friendly way to restore polluted soil while effectively extracting harmful substances",
                "sentence_suffix": " through their well-developed root systems.",
                "full_sentence": "Planting willow trees provides an eco-friendly way to restore polluted soil while effectively extracting harmful substances through their well-developed root systems.",
                "given_words": ["restore", "harmful", "way", "eco-friendly", "polluted", "extract", "substance", "soil", "while", "effective", "an"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (어형 및 분사 변형)"
                ],
                "functional_words_detail": [
                    {"word": "to", "role": "to부정사 표지 (형용사적 용법)", "omitted_from_given": True, "reason": "명사 way를 수식하는 to부정사"},
                    {"word": "while", "role": "분사구문 접속사", "omitted_from_given": False, "reason": "동시동작을 나타내는 접속사"},
                    {"word": "an", "role": "부정관사", "omitted_from_given": False, "reason": "단수 명사구 앞 관사"}
                ],
                "added_functional_words": ["to"],
                "modified_words": [
                    {"base": "extract", "modified": "extracting", "reason": "while 접속사 뒤 능동의 분사구문 (현재분사)"},
                    {"base": "substance", "modified": "substances", "reason": "복수형 명사"},
                    {"base": "effective", "modified": "effectively", "reason": "동명사/분사 수식 부사"}
                ],
                "translation_korean": "버드나무를 심는 것은 잘 발달된 뿌리 체계를 통해 해로운 물질을 효과적으로 추출하면서 오염된 토양을 복구하는 친환경적인 방법을 제공한다.",
                "grammar_explanation": "명사 way 뒤에 to부정사 형용사적 용법(to restore)이 수식하며, 접속사 while 뒤에 의미상 주어가 생략된 현재분사 분사구문(while effectively extracting)이 이끄는 고난도 수능/내신 빈출 구조입니다."
            },
            {
                "candidate_id": 2,
                "difficulty": difficulty,
                "theme_title": "오염 물질 흡수 능력을 지닌 버드나무 품종 탐구의 필요성",
                "target_grammar_used": "관계대명사 that + 5형식 enable A to B",
                "target_vocab_used": "species, absorb, enable, clean up, promising",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "Further exploration of willow species ",
                "blank_answer": "that absorb harmful materials better enables us to clean up our land",
                "sentence_suffix": " more cost-effectively.",
                "full_sentence": "Further exploration of willow species that absorb harmful materials better enables us to clean up our land more cost-effectively.",
                "given_words": ["better", "clean", "absorb", "up", "our", "that", "enable", "harmful", "material", "we", "land"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (수일치, 격변화, 어형 변형)"
                ],
                "functional_words_detail": [
                    {"word": "to", "role": "to부정사 표지 (목적격 보어)", "omitted_from_given": True, "reason": "5형식 enable의 목적격 보어 to부정사"},
                    {"word": "that", "role": "주격 관계대명사", "omitted_from_given": False, "reason": "선행사 willow species 수식"}
                ],
                "added_functional_words": ["to"],
                "modified_words": [
                    {"base": "enable", "modified": "enables", "reason": "주어 Further exploration(단수)에 따른 단수 동사 수일치"},
                    {"base": "we", "modified": "us", "reason": "동사 enables의 목적어 자리이므로 목적격 대명사 사용"},
                    {"base": "material", "modified": "materials", "reason": "복수형 명사"}
                ],
                "translation_korean": "해로운 물질을 더 잘 흡수하는 버드나무 종에 대한 추가적인 탐구는 우리가 비용 효율적으로 토지를 정화할 수 있도록 해준다.",
                "grammar_explanation": "주어(exploration)와 동사(enables) 사이 관계대명사절(that absorb harmful materials better)이 삽입되어 수일치를 묻고, 5형식 동사 enable + 목적어(us) + to부정사(to clean up)를 정확히 작문해야 하는 킬러 문항입니다."
            },
            {
                "candidate_id": 3,
                "difficulty": difficulty,
                "theme_title": "기존 매립 방식의 한계와 버드나무 식재의 경제적 대안",
                "target_grammar_used": "5형식 동사 allow + O + to-V + without 전치사 동명사",
                "target_vocab_used": "utilize, extensive, allow, extract, incur",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "Utilizing willow trees with extensive root systems ",
                "blank_answer": "allows us to naturally extract toxic substances from polluted soil without incurring high costs",
                "sentence_suffix": " of landfill transportation.",
                "full_sentence": "Utilizing willow trees with extensive root systems allows us to naturally extract toxic substances from polluted soil without incurring high costs of landfill transportation.",
                "given_words": ["allow", "we", "toxic", "natural", "extract", "incur", "high", "polluted", "cost", "soil", "without", "substance"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (수일치, 격변화, 품사 변형 및 동명사)"
                ],
                "functional_words_detail": [
                    {"word": "to", "role": "to부정사 표지 (목적격 보어)", "omitted_from_given": True, "reason": "5형식 동사 allow 뒤 목적격 보어"},
                    {"word": "from", "role": "출처의 전치사", "omitted_from_given": True, "reason": "extract A from B 구문"},
                    {"word": "without", "role": "전치사", "omitted_from_given": False, "reason": "조건/부정의 전치사"}
                ],
                "added_functional_words": ["to", "from"],
                "modified_words": [
                    {"base": "allow", "modified": "allows", "reason": "동명사 주어 Utilizing(단수)에 따른 수일치"},
                    {"base": "we", "modified": "us", "reason": "동사 allows의 목적어 자리이므로 목적격 대명사"},
                    {"base": "natural", "modified": "naturally", "reason": "동사 extract를 수식하는 부사형"},
                    {"base": "incur", "modified": "incurring", "reason": "전치사 without 뒤 동명사"},
                    {"base": "substance", "modified": "substances", "reason": "복수형 명사"},
                    {"base": "cost", "modified": "costs", "reason": "복수형 명사"}
                ],
                "translation_korean": "광범위한 뿌리 체계를 가진 버드나무를 활용하는 것은 매립지 운송의 높은 비용을 발생시키지 않고 오염된 토양에서 유독 물질을 자연스럽게 추출할 수 있도록 해준다.",
                "grammar_explanation": "동명사 주어(Utilizing)에 따른 동사 수일치(allows), 5형식 allow + O + to-V 구조와 전치사 without 뒤 동명사(incurring)를 영작하는 복합 구문 문제입니다."
            }
        ]
        return {"candidates": all_candidates[:candidate_count]}

    elif is_habit_passage:
        all_candidates = [
            {
                "candidate_id": 1,
                "difficulty": difficulty,
                "theme_title": "기존 루틴의 의식적 대체를 통한 습관 변화",
                "target_grammar_used": "가주어-진주어 not to A but to B + while 분사구문",
                "target_vocab_used": "crucial, eliminate, consciously, replace, maintain",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "To break an unwanted habit, it is ",
                "blank_answer": "crucial not to eliminate the cue but to consciously replace the old routine while maintaining the same reward",
                "sentence_suffix": ".",
                "full_sentence": "To break an unwanted habit, it is crucial not to eliminate the cue but to consciously replace the old routine while maintaining the same reward.",
                "given_words": ["cue", "maintain", "reward", "eliminate", "the", "routine", "old", "crucial", "replace", "conscious", "same", "while"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (부사형 및 분사 변형)"
                ],
                "functional_words_detail": [
                    {"word": "not to", "role": "진주어 부정 to부정사", "omitted_from_given": True, "reason": "not A but B 병렬 구조 to부정사"},
                    {"word": "but to", "role": "접속사 + to부정사", "omitted_from_given": True, "reason": "not A but B 병렬 구조 to부정사"},
                    {"word": "while", "role": "분사구문 접속사", "omitted_from_given": False, "reason": "동시동작 접속사"}
                ],
                "added_functional_words": ["not to", "but to"],
                "modified_words": [
                    {"base": "conscious", "modified": "consciously", "reason": "동사 replace를 수식하는 부사형"},
                    {"base": "maintain", "modified": "maintaining", "reason": "접속사 while 뒤 분사구문 (현재분사)"}
                ],
                "translation_korean": "원치 않는 습관을 없애기 위해서는 신호를 완전히 없애는 것이 아니라 동일한 보상을 유지하면서 이전의 루틴을 의식적으로 대체하는 것이 중요하다.",
                "grammar_explanation": "가주어 it 뒤 진주어 자리에서 'not A but B' 병렬 구조(not to eliminate ~ but to consciously replace ~)와 접속사를 수반한 분사구문(while maintaining)을 출제한 문항입니다."
            },
            {
                "candidate_id": 2,
                "difficulty": difficulty,
                "theme_title": "습관 루프의 자동화 메커니즘과 갈망 형성",
                "target_grammar_used": "접속사 as + become intertwined with + 분사",
                "target_vocab_used": "automatic, neurological, intertwined, craving, reinforce",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "A habit loop becomes deeply ingrained ",
                "blank_answer": "as the cue and reward become intertwined with a craving that drives the routine",
                "sentence_suffix": " automatically.",
                "full_sentence": "A habit loop becomes deeply ingrained as the cue and reward become intertwined with a craving that drives the routine automatically.",
                "given_words": ["cue", "reward", "that", "intertwine", "drive", "routine", "as", "the", "a", "become", "craving"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (과거분사 수동태, 관계사절 수일치)"
                ],
                "functional_words_detail": [
                    {"word": "with", "role": "연결 전치사", "omitted_from_given": True, "reason": "intertwined with 숙어 표현"},
                    {"word": "and", "role": "등위접속사", "omitted_from_given": True, "reason": "the cue와 reward 연결"},
                    {"word": "that", "role": "주격 관계대명사", "omitted_from_given": False, "reason": "a craving 수식"}
                ],
                "added_functional_words": ["and", "with"],
                "modified_words": [
                    {"base": "intertwine", "modified": "intertwined", "reason": "become 뒤 과거분사 보어"},
                    {"base": "drive", "modified": "drives", "reason": "선행사 a craving(단수)에 따른 단수 동사"}
                ],
                "translation_korean": "습관 루프는 신호와 보상이 루틴을 자동으로 유도하는 갈망과 얽히게 됨에 따라 깊이 각인된다.",
                "grammar_explanation": "수동의 의미를 나타내는 과거분사(intertwined)와 주격 관계대명사 that절 내의 3인칭 단수 동사 수일치(drives)를 결합한 서술형 문항입니다."
            },
            {
                "candidate_id": 3,
                "difficulty": difficulty,
                "theme_title": "성공적인 습관 교정을 위한 핵심 전략",
                "target_grammar_used": "동명사 주어 Modifying + 5형식 enable A to B",
                "target_vocab_used": "modify, preserve, enable, reform, successfully",
                "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
                "sentence_prefix": "Modifying the routine while ",
                "blank_answer": "preserving the trigger and reward enables individuals to reform their behavior",
                "sentence_suffix": " more effectively.",
                "full_sentence": "Modifying the routine while preserving the trigger and reward enables individuals to reform their behavior more effectively.",
                "given_words": ["individual", "reward", "trigger", "preserve", "enable", "reform", "the", "their", "behavior"],
                "conditions": [
                    "1. 어법상 기능어 반드시 추가할 것",
                    "2. 필요시 단어를 변형할 것 (분사구문, 3인칭 단수 동사, 복수형)"
                ],
                "functional_words_detail": [
                    {"word": "to", "role": "to부정사 표지 (목적격 보어)", "omitted_from_given": True, "reason": "enable + O + to-V 구조"},
                    {"word": "and", "role": "등위접속사", "omitted_from_given": True, "reason": "the trigger and reward 병렬 연결"}
                ],
                "added_functional_words": ["and", "to"],
                "modified_words": [
                    {"base": "preserve", "modified": "preserving", "reason": "while 뒤 분사구문 (현재분사)"},
                    {"base": "enable", "modified": "enables", "reason": "동명사 주어 Modifying(단수)에 따른 수일치"},
                    {"base": "individual", "modified": "individuals", "reason": "복수형 명사"}
                ],
                "translation_korean": "신호와 보상을 보존하면서 루틴을 수정하는 것은 개인이 자신의 행동을 더 효과적으로 개선할 수 있도록 해준다.",
                "grammar_explanation": "동명사 주어와 수일치(enables), 분사구문(preserving), 5형식 enable + O + to-V 구조를 모두 검증하는 고난도 서술형 문제입니다."
            }
        ]
        return {"candidates": all_candidates[:candidate_count]}

    # Default / Greenwashing example (Matching Image 2/3)
    all_candidates = [
        {
            "candidate_id": 1,
            "difficulty": difficulty,
            "theme_title": "그린워싱의 본질과 소비자를 오도하는 기만적 마케팅",
            "target_grammar_used": "주격 관계대명사 that + 5형식 allow + O + to-V + while 분사구문",
            "target_vocab_used": "deceptive, allow, present, false, eco-friendly, mislead, vague, unverified",
            "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
            "sentence_prefix": "Greenwashing is the deceptive practice ",
            "blank_answer": "that allows companies to present a false eco-friendly image while misleading consumers",
            "sentence_suffix": " with vague and unverified claims.",
            "full_sentence": "Greenwashing is the deceptive practice that allows companies to present a false eco-friendly image while misleading consumers with vague and unverified claims.",
            "given_words": ["eco-friendly", "allow", "while", "companies", "image", "mislead", "that", "present", "consumers", "a", "false"],
            "conditions": [
                "1. 어법상 기능어 반드시 추가할 것",
                "2. 필요시 단어를 변형할 것 (수일치, 분사 변형 등)"
            ],
            "functional_words_detail": [
                {"word": "to", "role": "to부정사 표지 (목적격 보어)", "omitted_from_given": True, "reason": "5형식 동사 allow + 목적어 + to부정사"},
                {"word": "that", "role": "주격 관계대명사", "omitted_from_given": False, "reason": "the deceptive practice 수식"},
                {"word": "while", "role": "분사구문 접속사", "omitted_from_given": False, "reason": "동시동작 나타냄"},
                {"word": "a", "role": "부정관사", "omitted_from_given": False, "reason": "단수 명사구 앞 관사"}
            ],
            "added_functional_words": ["to"],
            "modified_words": [
                {"base": "allow", "modified": "allows", "reason": "선행사 practice(3인칭 단수)에 따른 수일치"},
                {"base": "mislead", "modified": "misleading", "reason": "접속사 while 뒤 분사구문 (현재분사)"}
            ],
            "translation_korean": "그린워싱은 모호하고 검증되지 않은 주장으로 소비자를 오도하는 동시에 기업이 거짓된 친환경 이미지를 제시할 수 있도록 하는 기만적인 행위이다.",
            "grammar_explanation": "선행사 the deceptive practice를 수식하는 주격 관계대명사 that절 내부에서 5형식 동사 allow + 목적어(companies) + to부정사(to present) 구문과, 접속사를 살려둔 분사구문(while misleading)을 결합하여 영작하는 문항입니다."
        },
        {
            "candidate_id": 2,
            "theme_title": "친환경 위장을 통한 기업의 비윤리적 홍보 실태",
            "target_grammar_used": "가주어-진주어 It is ~ for A to-V + without 전치사 동명사",
            "target_vocab_used": "unethical, disguise, mislead, actual, commitment",
            "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
            "sentence_prefix": "In summary, ",
            "blank_answer": "it is unethical for corporations to disguise their products as green without demonstrating genuine commitment",
            "sentence_suffix": " to environmental protection.",
            "full_sentence": "In summary, it is unethical for corporations to disguise their products as green without demonstrating genuine commitment to environmental protection.",
            "given_words": ["green", "corporations", "disguise", "demonstrate", "genuine", "it", "commitment", "as", "their", "without", "product", "unethical"],
            "conditions": [
                "1. 어법상 기능어 반드시 추가할 것",
                "2. 필요시 단어를 변형할 것 (전치사 뒤 동명사, 복수형 명사)"
            ],
            "added_functional_words": ["for", "to"],
            "modified_words": [
                {"base": "product", "modified": "products", "reason": "복수형 명사"},
                {"base": "demonstrate", "modified": "demonstrating", "reason": "전치사 without 뒤 동명사"}
            ],
            "translation_korean": "요약하자면, 기업들이 환경 보호에 대한 진정한 헌신을 증명하지 않고 자사 제품을 친환경인 것처럼 위장하는 것은 비윤리적이다.",
            "grammar_explanation": "가주어 it과 진주어 to disguise 사이의 의미상 주어(for corporations)를 세우고, 전치사 without 뒤에 동명사(demonstrating)를 연결하는 서술형 핵심 구문입니다."
        },
        {
            "candidate_id": 3,
            "theme_title": "소비자 신뢰를 훼손하는 기만적 마케팅의 장기적 위험",
            "target_grammar_used": "Not only A but also B 병렬구문 + 분사",
            "target_vocab_used": "undermine, divert, genuine, deceptive, trust",
            "direction": "■ 윗글의 내용을 한 문장으로 요약하고자 한다. <보기>에 주어진 단어를 활용하여 빈칸 (A)에 들어갈 말을 영어로 쓰시오. (단, <조건>에 맞게 쓸 것)",
            "sentence_prefix": "Deceptive eco-friendly marketing ",
            "blank_answer": "not only undermines consumer trust but also diverts attention away from genuine solutions",
            "sentence_suffix": " for environmental protection.",
            "full_sentence": "Deceptive eco-friendly marketing not only undermines consumer trust but also diverts attention away from genuine solutions for environmental protection.",
            "given_words": ["divert", "genuine", "solution", "consumer", "not", "but", "also", "undermine", "trust", "attention", "only"],
            "conditions": [
                "1. 어법상 기능어 반드시 추가할 것",
                "2. 필요시 단어를 변형할 것 (3인칭 단수 동사 수일치, 복수형 명사)"
            ],
            "added_functional_words": ["away from"],
            "modified_words": [
                {"base": "undermine", "modified": "undermines", "reason": "단수 주어 marketing에 따른 3인칭 단수 동사"},
                {"base": "divert", "modified": "diverts", "reason": "not only A but also B 병렬 구조에 따른 단수 동사"},
                {"base": "solution", "modified": "solutions", "reason": "복수형 명사"}
            ],
            "translation_korean": "기만적인 친환경 마케팅은 소비자의 신뢰를 훼손할 뿐만 아니라 환경 보호를 위한 진정한 해결책으로부터 관심을 돌려놓는다.",
            "grammar_explanation": "주어(marketing)에 호응하는 'not only V1 but also V2' 병렬 일치(undermines ~ diverts ~)와 전치사구(away from)를 완성하는 빈출 서술형 구조입니다."
        }
    ]
    return {"candidates": all_candidates[:candidate_count]}
