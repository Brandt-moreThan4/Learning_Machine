


DEFAULT_PROMPT = """You are generating quiz questions strictly from SOURCE.
Return a JSON list of objects with fields:
 - kind (mcq|cloze|tf|short)
 - question
 - answer
 - distractors(3 for mcq else [])
 - difficulty (easy|medium|hard)
 - justification_span (<=200 chars from SOURCE).
SOURCE:
<<<
{source}
>>>
Write {n} questions.
Return only the Json data. 
"""



TOY_PROMPT = """You are generating a quiz.
Return a JSON list of objects with fields:
 - kind (mcq|cloze|tf|short)
 - question
 - answer
 - distractors(3 for mcq else [])
 - difficulty (easy|medium|hard)
 - answer_justification (<=200).

<<<
The quiz content should be about the nights watch from A Song of Ice and Fire.
>>>
Write 3 questions.
Return only the Json list. 
"""
